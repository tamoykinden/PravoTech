"""Тесты правил импорта кейсов с Яндекс.Диска."""

import zipfile
from pathlib import Path
from types import SimpleNamespace

from backend.services.disk_sync import YandexDiskCaseSynchronizer
from infrastructure.storage import DiskDocument, YandexDiskStorage


def test_selects_case_description_instead_of_templates() -> None:
    """Основной DOCX выбирается даже при опечатке в имени папки."""

    files = [
        DiskDocument('Заявление в полицию - Оскорбления в Интернете', '/statement'),
        DiskDocument('Иск в суд - Оскорбления в Интернете', '/claim'),
        DiskDocument('Оскорбления в Интернете', '/source'),
    ]
    selected = YandexDiskStorage._select_source_document(
        'Оскробление в Интернете',
        files,
    )
    assert selected.path == '/source'


def test_extracts_paragraphs_from_docx(tmp_path) -> None:
    """DOCX преобразуется в читаемые абзацы решения."""

    path = tmp_path / 'case.docx'
    document_xml = '''<?xml version="1.0" encoding="UTF-8"?>
    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
      <w:body>
        <w:p><w:r><w:t>Первый шаг</w:t></w:r></w:p>
        <w:p><w:r><w:t>Второй шаг</w:t></w:r></w:p>
      </w:body>
    </w:document>'''.encode('utf-8')
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('word/document.xml', document_xml)
    assert YandexDiskCaseSynchronizer._extract_docx_text(path) == (
        'Первый шаг\n\nВторой шаг'
    )


class FakeYandexDiskClient:
    """Минимальная заглушка иерархии Яндекс.Диска."""

    def __init__(self) -> None:
        self.downloaded: tuple[str, str] | None = None
        self.items = {
            '/Cases': [
                SimpleNamespace(
                    type='dir',
                    name='Автомобиль и ДТП',
                    path='/Cases/Автомобиль и ДТП',
                ),
            ],
            '/Cases/Автомобиль и ДТП': [
                SimpleNamespace(
                    type='dir',
                    name='Вас сбила машина',
                    path=(
                        '/Cases/Автомобиль и ДТП/'
                        'Вас сбила машина'
                    ),
                ),
            ],
            '/Cases/Автомобиль и ДТП/Вас сбила машина': [
                SimpleNamespace(
                    type='file',
                    name='Вас сбила машина.docx',
                    path=(
                        '/Cases/Автомобиль и ДТП/'
                        'Вас сбила машина/Вас сбила машина.docx'
                    ),
                ),
                SimpleNamespace(
                    type='file',
                    name='Иск в суд - Вас сбила машина.docx',
                    path=(
                        '/Cases/Автомобиль и ДТП/'
                        'Вас сбила машина/Иск в суд.docx'
                    ),
                ),
            ],
        }

    def listdir(self, path: str):
        """Возвращает элементы заданной тестовой папки."""

        return self.items[path]

    def download(self, source: str, destination: str) -> None:
        """Запоминает путь скачивания без сетевого запроса."""

        self.downloaded = source, destination


def _fake_storage() -> tuple[YandexDiskStorage, FakeYandexDiskClient]:
    """Создаёт адаптер без настоящего токена и SDK-клиента."""

    client = FakeYandexDiskClient()
    storage = object.__new__(YandexDiskStorage)
    storage._client = client
    storage._base_path = '/Cases'
    return storage, client


def test_reads_category_case_document_hierarchy() -> None:
    """Первый уровень становится категорией, второй — кейсом."""

    storage, _ = _fake_storage()

    bundles = storage._list_case_bundles_sync()

    assert len(bundles) == 1
    bundle = bundles[0]
    assert bundle.category_title == 'Автомобиль и ДТП'
    assert bundle.title == 'Вас сбила машина'
    assert bundle.source.title == 'Вас сбила машина'
    assert [document.title for document in bundle.documents] == [
        'Иск в суд - Вас сбила машина'
    ]


def test_download_uses_category_and_case_path(tmp_path: Path) -> None:
    """Скачивание строит путь через категорию и кейс."""

    storage, client = _fake_storage()
    destination = tmp_path / 'document.docx'

    filename = storage._download_document_sync(
        'Автомобиль и ДТП',
        'Вас сбила машина',
        'Иск в суд - Вас сбила машина',
        destination,
    )

    assert filename == 'Иск в суд - Вас сбила машина.docx'
    assert client.downloaded == (
        '/Cases/Автомобиль и ДТП/'
        'Вас сбила машина/Иск в суд.docx',
        str(destination),
    )
