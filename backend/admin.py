"""Минимальная серверная админка для управления контентом."""

import secrets

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_session
from backend.security import authenticate_admin, require_admin
from backend.services import YandexDiskCaseSynchronizer
from database.models import Case, CaseCategory, Document, TGFeedback, TGUser, VKFeedback, VKUser

router = APIRouter(prefix='/admin')
templates = Jinja2Templates(directory='backend/templates')


def _csrf(request: Request) -> str:
    """Возвращает или создаёт CSRF-токен административной сессии."""

    token = request.session.get('csrf_token')
    if not token:
        token = secrets.token_urlsafe(32)
        request.session['csrf_token'] = token
    return token


def _check_csrf(request: Request, token: str) -> None:
    """Отклоняет изменяющий запрос с неверным CSRF-токеном."""

    expected = request.session.get('csrf_token', '')
    if not expected or not secrets.compare_digest(expected, token):
        raise HTTPException(status_code=403, detail='Неверный CSRF-токен')


@router.get('/login', response_class=HTMLResponse)
async def login_page(request: Request):
    """Показывает форму входа без раскрытия причины прошлой ошибки."""

    return templates.TemplateResponse(request, 'login.html', {'error': None})


@router.post('/login')
async def login(request: Request, username: str = Form(), password: str = Form()):
    """Создаёт административную сессию после проверки Argon2-пароля."""

    if not authenticate_admin(username.strip(), password):
        return templates.TemplateResponse(
            request,
            'login.html',
            {'error': 'Неверные учётные данные'},
            status_code=401,
        )
    request.session.clear()
    request.session['admin_username'] = username.strip()
    _csrf(request)
    return RedirectResponse('/admin', status_code=303)


@router.post('/logout')
async def logout(request: Request, csrf_token: str = Form()):
    """Удаляет административную сессию."""

    require_admin(request)
    _check_csrf(request, csrf_token)
    request.session.clear()
    return RedirectResponse('/admin/login', status_code=303)


@router.get('', response_class=HTMLResponse)
async def dashboard(
    request: Request,
    _: str = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    """Показывает контент и агрегированную статистику без внешних ID."""

    categories = (await session.scalars(select(CaseCategory).order_by(CaseCategory.name))).all()
    cases = (await session.scalars(select(Case).order_by(Case.title))).all()
    documents = (await session.scalars(select(Document).order_by(Document.title))).all()
    counts = {
        'tg_users': await session.scalar(select(func.count()).select_from(TGUser)),
        'vk_users': await session.scalar(select(func.count()).select_from(VKUser)),
        'feedback': (
            await session.scalar(select(func.count()).select_from(TGFeedback))
            + await session.scalar(select(func.count()).select_from(VKFeedback))
        ),
    }
    return templates.TemplateResponse(
        request,
        'dashboard.html',
        {
            'csrf_token': _csrf(request),
            'categories': categories,
            'cases': cases,
            'documents': documents,
            'counts': counts,
        },
    )


@router.post('/categories')
async def create_category(
    request: Request,
    name: str = Form(min_length=2, max_length=100),
    csrf_token: str = Form(),
    _: str = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    """Создаёт уникальную категорию."""

    _check_csrf(request, csrf_token)
    session.add(CaseCategory(name=name.strip()))
    await session.commit()
    return RedirectResponse('/admin', status_code=303)


@router.post('/sync-yandex-disk')
async def sync_yandex_disk(
    request: Request,
    csrf_token: str = Form(),
    _: str = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    """Запускает ручную идемпотентную синхронизацию контента."""

    _check_csrf(request, csrf_token)
    result = await YandexDiskCaseSynchronizer.from_environment().synchronize(session)
    location = (
        '/admin?sync=ok'
        f'&categories_created={result.categories_created}'
        f'&cases_created={result.cases_created}'
        f'&cases_moved={result.cases_moved}'
        f'&cases_updated={result.cases_updated}'
        f'&documents_created={result.documents_created}'
    )
    return RedirectResponse(location, status_code=303)


@router.post('/cases')
async def create_case(
    request: Request,
    title: str = Form(min_length=2, max_length=100),
    solution: str = Form(min_length=10, max_length=20000),
    category_id: int = Form(gt=0),
    csrf_token: str = Form(),
    _: str = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    """Создаёт правовой кейс в существующей категории."""

    _check_csrf(request, csrf_token)
    if await session.get(CaseCategory, category_id) is None:
        raise HTTPException(status_code=400, detail='Категория не найдена')
    session.add(Case(title=title.strip(), solution=solution.strip(), category_id=category_id))
    await session.commit()
    return RedirectResponse('/admin', status_code=303)


@router.post('/cases/{case_id}/delete')
async def delete_case(
    case_id: int,
    request: Request,
    csrf_token: str = Form(),
    _: str = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    """Удаляет пустой кейс; связанные документы защищены ограничением БД."""

    _check_csrf(request, csrf_token)
    case = await session.get(Case, case_id)
    if case is not None:
        await session.delete(case)
        await session.commit()
    return RedirectResponse('/admin', status_code=303)
