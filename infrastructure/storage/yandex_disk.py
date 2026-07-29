import asyncio
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

import yadisk


@dataclass(frozen=True)
class DiskDocument:
    """Файл документа, обнаруженный в папке кейса."""

    title: str
    path: str


@dataclass(frozen=True)
class DiskCaseBundle:
    """Кейс с основным описанием и шаблонами документов."""

    category_title: str
    title: str
    source: DiskDocument
    documents: tuple[DiskDocument, ...]


class StorageError(Exception):
    """Базовая ошибка файлового хранилища."""


class DocumentNotFoundError(StorageError):
    """Документ не найден в файловом хранилище."""


class YandexDiskStorage:
    """Асинхронный адаптер для синхронного SDK Яндекс.Диска."""

    def __init__(self, token: str, base_path: str) -> None:
        if not token:
            raise ValueError('YANDEX_DISK_TOKEN не задан')
        if not base_path:
            raise ValueError('Базовый путь Яндекс.Диска не задан')

        self._client = yadisk.Client(token=token)
        self._base_path = base_path.rstrip('/')

    async def download_document(
        self,
        category_title: str,
        case_title: str,
        document_title: str,
        destination: Path,
    ) -> str:
        """Находит DOCX по названию и скачивает его без блокировки event loop.

        Returns:
            Имя найденного файла.
        """

        return await asyncio.to_thread(
            self._download_document_sync,
            category_title,
            case_title,
            document_title,
            destination,
        )

    async def list_case_bundles(self) -> list[DiskCaseBundle]:
        """Возвращает папки-кейсы и классифицирует DOCX внутри них."""

        return await asyncio.to_thread(self._list_case_bundles_sync)

    async def download_path(self, source_path: str, destination: Path) -> None:
        """Скачивает конкретный обнаруженный файл во временный путь."""

        await asyncio.to_thread(self._client.download, source_path, str(destination))

    def _download_document_sync(
        self,
        category_title: str,
        case_title: str,
        document_title: str,
        destination: Path,
    ) -> str:
        try:
            case_path = (
                f'{self._base_path}/{category_title}/{case_title}'
            )
            expected_title = self._normalize_title(document_title)

            for item in self._client.listdir(case_path):
                if item.type != 'file' or not item.name.lower().endswith('.docx'):
                    continue

                if expected_title not in self._normalize_title(item.name):
                    continue

                self._client.download(item.path, str(destination))
                return item.name
        except Exception as error:
            raise StorageError('Ошибка обращения к Яндекс.Диску') from error

        raise DocumentNotFoundError(
            f'Документ "{document_title}" не найден для кейса "{case_title}"'
        )

    def _list_case_bundles_sync(self) -> list[DiskCaseBundle]:
        bundles: list[DiskCaseBundle] = []
        try:
            categories = [
                item
                for item in self._client.listdir(self._base_path)
                if item.type == 'dir'
            ]
            for category in sorted(
                categories,
                key=lambda item: item.name.casefold(),
            ):
                case_directories = [
                    item
                    for item in self._client.listdir(category.path)
                    if item.type == 'dir'
                ]
                for case_directory in sorted(
                    case_directories,
                    key=lambda item: item.name.casefold(),
                ):
                    files = [
                        DiskDocument(
                            title=Path(item.name).stem,
                            path=item.path,
                        )
                        for item in self._client.listdir(
                            case_directory.path
                        )
                        if (
                            item.type == 'file'
                            and item.name.lower().endswith('.docx')
                        )
                    ]
                    if not files:
                        continue
                    source = self._select_source_document(
                        case_directory.name,
                        files,
                    )
                    documents = tuple(
                        item
                        for item in files
                        if item.path != source.path
                    )
                    bundles.append(
                        DiskCaseBundle(
                            category_title=category.name.strip(),
                            title=case_directory.name.strip(),
                            source=source,
                            documents=documents,
                        )
                    )
        except Exception as error:
            raise StorageError('Ошибка чтения структуры Яндекс.Диска') from error
        return bundles

    @classmethod
    def _select_source_document(
        cls,
        case_title: str,
        files: list[DiskDocument],
    ) -> DiskDocument:
        """Выбирает описание кейса, отделяя его от исков и заявлений."""

        template_prefixes = (
            'жалоба',
            'иск',
            'заявление',
            'заяление',
            'письменное обращение',
            'претензия',
        )
        candidates = [
            item
            for item in files
            if not item.title.strip().casefold().startswith(template_prefixes)
        ] or files
        normalized_case = cls._normalize_title(case_title)
        return max(
            candidates,
            key=lambda item: SequenceMatcher(
                None,
                normalized_case,
                cls._normalize_title(item.title),
            ).ratio(),
        )

    @staticmethod
    def _normalize_title(value: str) -> str:
        normalized = unicodedata.normalize('NFKC', value).strip().casefold()
        without_suffix = normalized.removesuffix('.docx')
        return ''.join(character for character in without_suffix if character.isalnum())
