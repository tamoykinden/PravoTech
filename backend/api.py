"""Авторизованное API для Telegram- и VK-клиентов."""

import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from backend.dependencies import get_session, require_client
from backend.schemas import (
    CaseRead,
    CategoryRead,
    ConsentUpdate,
    DocumentRead,
    FeedbackCreate,
    Platform,
    StatusRead,
    UserRead,
    ViewCreate,
)
from database.models import (
    Case,
    CaseCategory,
    Document,
    TGFeedback,
    TGUser,
    TGUserRequest,
    VKFeedback,
    VKUser,
    VKUserRequest,
)
from infrastructure.storage import DocumentNotFoundError, StorageError, YandexDiskStorage

router = APIRouter(prefix='/api/v1/{platform}', dependencies=[Depends(require_client)])


def _platform_models(platform: Platform):
    """Возвращает платформенные модели без дублирования обработчиков."""

    if platform == 'telegram':
        return TGUser, TGFeedback, TGUserRequest, TGUser.telegram_id
    return VKUser, VKFeedback, VKUserRequest, VKUser.vk_id


def _user_schema(user, platform: Platform) -> UserRead:
    """Нормализует разные внешние идентификаторы в единый контракт."""

    external_id = user.telegram_id if platform == 'telegram' else user.vk_id
    return UserRead(
        id=user.id,
        external_id=external_id,
        pd_agreed=user.pd_agreed,
        registered_at=user.registered_at,
    )


async def _case_schema(session: AsyncSession, case: Case) -> CaseRead:
    """Добавляет к кейсу безопасные метаданные документов."""

    documents = (
        await session.scalars(
            select(Document).where(Document.case_id == case.id).order_by(Document.id)
        )
    ).all()
    return CaseRead(
        id=case.id,
        title=case.title,
        solution=case.solution,
        category_id=case.category_id,
        documents=[DocumentRead.model_validate(item) for item in documents],
    )


@router.get('/categories', response_model=list[CategoryRead])
async def list_categories(session: AsyncSession = Depends(get_session)):
    """Возвращает категории в стабильном алфавитном порядке."""

    rows = (await session.scalars(select(CaseCategory).order_by(CaseCategory.name))).all()
    return rows


@router.get('/cases', response_model=list[CaseRead])
async def list_cases(
    category_id: int | None = Query(default=None, gt=0),
    session: AsyncSession = Depends(get_session),
):
    """Возвращает все кейсы либо кейсы выбранной категории."""

    statement = select(Case).order_by(Case.title)
    if category_id is not None:
        statement = statement.where(Case.category_id == category_id)
    rows = (await session.scalars(statement)).all()
    return [await _case_schema(session, item) for item in rows]


@router.get('/cases/search', response_model=list[CaseRead])
async def search_cases(
    q: str = Query(min_length=2, max_length=200),
    session: AsyncSession = Depends(get_session),
):
    """Безопасно ищет кейсы через plainto_tsquery без ручной сборки SQL."""

    statement = (
        select(Case)
        .where(Case.search_vector.op('@@')(func.plainto_tsquery('russian', q.strip())))
        .order_by(Case.title)
        .limit(50)
    )
    rows = (await session.scalars(statement)).all()
    return [await _case_schema(session, item) for item in rows]


@router.get('/cases/{case_id}', response_model=CaseRead)
async def get_case(case_id: int, session: AsyncSession = Depends(get_session)):
    """Возвращает один кейс или понятную ошибку 404."""

    case = await session.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail='Кейс не найден')
    return await _case_schema(session, case)


@router.get('/documents/{document_id}', response_class=FileResponse)
async def download_document(document_id: int, session: AsyncSession = Depends(get_session)):
    """Потоково отдаёт DOCX, не раскрывая клиенту токен хранилища."""

    document = await session.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail='Документ не найден')
    case = await session.get(Case, document.case_id)
    if case is None:
        raise HTTPException(status_code=404, detail='Кейс не найден')
    category = await session.get(CaseCategory, case.category_id)
    if category is None:
        raise HTTPException(status_code=404, detail='Категория не найдена')
    descriptor, raw_path = tempfile.mkstemp(suffix='.docx')
    os.close(descriptor)
    path = Path(raw_path)
    try:
        storage = YandexDiskStorage(
            token=os.getenv('YANDEX_DISK_TOKEN', ''),
            base_path=os.getenv('YANDEX_DISK_BASE_PATH', ''),
        )
        filename = await storage.download_document(
            category.name,
            case.title,
            document.title,
            path,
        )
    except DocumentNotFoundError as error:
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=404, detail='Файл не найден') from error
    except (StorageError, ValueError) as error:
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=502, detail='Хранилище документов недоступно') from error
    return FileResponse(
        path,
        filename=filename,
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        background=BackgroundTask(path.unlink, missing_ok=True),
    )


@router.post('/users/{external_id}', response_model=UserRead)
async def get_or_create_user(
    platform: Platform,
    external_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Идемпотентно регистрирует пользователя платформы."""

    user_model, _, _, external_column = _platform_models(platform)
    user = await session.scalar(select(user_model).where(external_column == external_id))
    if user is None:
        user = user_model(**{external_column.key: external_id})
        session.add(user)
    else:
        user.last_activity = func.now()
    await session.commit()
    await session.refresh(user)
    return _user_schema(user, platform)


@router.patch('/users/{user_id}/consent', response_model=UserRead)
async def update_consent(
    platform: Platform,
    user_id: int,
    payload: ConsentUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Обновляет согласие пользователя только внутри его платформы."""

    user_model, _, _, _ = _platform_models(platform)
    user = await session.get(user_model, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    user.pd_agreed = payload.agreed
    await session.commit()
    await session.refresh(user)
    return _user_schema(user, platform)


@router.post('/feedback', response_model=StatusRead, status_code=201)
async def create_feedback(
    platform: Platform,
    payload: FeedbackCreate,
    session: AsyncSession = Depends(get_session),
):
    """Сохраняет валидированную обратную связь."""

    user_model, feedback_model, _, _ = _platform_models(platform)
    if await session.get(user_model, payload.user_id) is None:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    session.add(feedback_model(user_id=payload.user_id, message=payload.message.strip()))
    await session.commit()
    return StatusRead()


@router.post('/views', response_model=StatusRead, status_code=201)
async def create_view(
    platform: Platform,
    payload: ViewCreate,
    session: AsyncSession = Depends(get_session),
):
    """Записывает просмотр существующего кейса существующим пользователем."""

    user_model, _, request_model, _ = _platform_models(platform)
    if await session.get(user_model, payload.user_id) is None:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    if await session.get(Case, payload.case_id) is None:
        raise HTTPException(status_code=404, detail='Кейс не найден')
    session.add(request_model(user_id=payload.user_id, case_id=payload.case_id))
    await session.commit()
    return StatusRead()
