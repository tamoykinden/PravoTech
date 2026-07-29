"""Идемпотентная синхронизация юридических кейсов с Яндекс.Диском."""

import os
import tempfile
import xml.etree.ElementTree as element_tree
import zipfile
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Case, CaseCategory, Document
from infrastructure.storage import DiskCaseBundle, YandexDiskStorage


@dataclass(frozen=True)
class DiskSyncResult:
    """Счётчики завершённой синхронизации."""

    categories_created: int = 0
    cases_created: int = 0
    cases_moved: int = 0
    cases_updated: int = 0
    documents_created: int = 0


class YandexDiskCaseSynchronizer:
    """Переносит структуру папок Диска в нормализованные таблицы БД."""

    LEGACY_CATEGORY_NAME = 'Кейсы с Яндекс.Диска'

    def __init__(self, storage: YandexDiskStorage) -> None:
        self.storage = storage

    @classmethod
    def from_environment(cls) -> 'YandexDiskCaseSynchronizer':
        """Создаёт сервис из переменных окружения backend."""

        return cls(
            storage=YandexDiskStorage(
                token=os.getenv('YANDEX_DISK_TOKEN', ''),
                base_path=os.getenv('YANDEX_DISK_BASE_PATH', ''),
            ),
        )

    async def synchronize(self, session: AsyncSession) -> DiskSyncResult:
        """Создаёт и обновляет кейсы без удаления данных и дубликатов."""

        bundles = await self.storage.list_case_bundles()
        categories = {
            category.name: category
            for category in await session.scalars(select(CaseCategory))
        }
        legacy_category = categories.get(self.LEGACY_CATEGORY_NAME)

        created_categories = 0
        created_cases = 0
        moved_cases = 0
        updated_cases = 0
        created_documents = 0
        for bundle in bundles:
            category = categories.get(bundle.category_title)
            if category is None:
                category = CaseCategory(name=bundle.category_title)
                session.add(category)
                await session.flush()
                categories[category.name] = category
                created_categories += 1

            solution = await self._read_solution(bundle)
            case = await session.scalar(
                select(Case).where(
                    Case.title == bundle.title,
                    Case.category_id == category.id,
                )
            )
            if case is None:
                case = await self._find_legacy_case(
                    session,
                    legacy_category,
                    bundle.title,
                    category.id,
                )
                if case is not None:
                    case.category_id = category.id
                    moved_cases += 1
                else:
                    case = Case(
                        title=bundle.title,
                        solution=solution,
                        category_id=category.id,
                    )
                    session.add(case)
                    await session.flush()
                    created_cases += 1

            if case.solution != solution:
                case.solution = solution
                updated_cases += 1

            existing_titles = set(
                await session.scalars(
                    select(Document.title).where(Document.case_id == case.id)
                )
            )
            for disk_document in bundle.documents:
                if disk_document.title in existing_titles:
                    continue
                session.add(
                    Document(
                        title=disk_document.title,
                        case_id=case.id,
                    )
                )
                created_documents += 1

        await session.commit()
        return DiskSyncResult(
            categories_created=created_categories,
            cases_created=created_cases,
            cases_moved=moved_cases,
            cases_updated=updated_cases,
            documents_created=created_documents,
        )

    @staticmethod
    async def _find_legacy_case(
        session: AsyncSession,
        legacy_category: CaseCategory | None,
        case_title: str,
        target_category_id: int,
    ) -> Case | None:
        """Находит старый кейс для безопасного переноса в категорию."""

        if (
            legacy_category is None
            or legacy_category.id == target_category_id
        ):
            return None
        return await session.scalar(
            select(Case).where(
                Case.title == case_title,
                Case.category_id == legacy_category.id,
            )
        )

    async def _read_solution(self, bundle: DiskCaseBundle) -> str:
        """Скачивает основной DOCX и извлекает читаемые абзацы."""

        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temporary:
            path = Path(temporary.name)
        try:
            await self.storage.download_path(bundle.source.path, path)
            text = self._extract_docx_text(path)
        finally:
            path.unlink(missing_ok=True)
        if not text:
            raise ValueError(f'Основной документ кейса «{bundle.title}» пуст')
        return text

    @staticmethod
    def _extract_docx_text(path: Path) -> str:
        """Извлекает текст DOCX средствами стандартной библиотеки."""

        with zipfile.ZipFile(path) as archive:
            xml = archive.read('word/document.xml')
        root = element_tree.fromstring(xml)
        namespace = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        paragraphs: list[str] = []
        for paragraph in root.findall('.//w:p', namespace):
            text = ''.join(
                node.text or ''
                for node in paragraph.findall('.//w:t', namespace)
            ).strip()
            if text:
                paragraphs.append(text)
        return '\n\n'.join(paragraphs)
