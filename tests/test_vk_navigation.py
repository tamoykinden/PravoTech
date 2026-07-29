"""Регрессионные тесты контекстной навигации VK-бота."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.schemas import CaseRead, DocumentRead
from config import CallbackAction
from vk_bot.handlers.document import DocumentHandler
from vk_bot.handlers.search import SearchHandler
from vk_bot.keyboards.case import CaseDetailKeyboard
from vk_bot.keyboards.category import CasesByCategoryKeyboard
from vk_bot.services.document_uploader import (VKDocumentUploadError,
                                               VKMessageDocumentUploader)


def _case(case_id: int, title: str) -> CaseRead:
    """Создаёт минимальный кейс для тестирования."""

    return CaseRead(
        id=case_id,
        title=title,
        solution='Пошаговое решение',
        category_id=1,
    )


def test_vk_document_payload_preserves_search_origin() -> None:
    """Документ VK получает кейс и источник перехода."""

    document = DocumentRead(id=7, title='Претензия', case_id=3)

    markup = json.loads(
        CaseDetailKeyboard(
            [document],
            case_id=3,
            origin='search',
        ).get_markup()
    )
    payload = markup['buttons'][0][0]['action']['payload']

    assert payload == {
        'action': CallbackAction.DOCUMENT,
        'id': 7,
        'case_id': 3,
        'origin': 'search',
    }


def test_vk_search_origin_returns_to_search_results() -> None:
    """После документа поисковый кейс ведёт к прежней выдаче."""

    buttons = DocumentHandler._origin_buttons('search')

    assert buttons[0][1] == {
        'action': CallbackAction.BACK_TO_SEARCH_RESULTS
    }


def test_vk_category_origin_returns_to_same_category() -> None:
    """После документа категорийный кейс ведёт в ту же категорию."""

    buttons = DocumentHandler._origin_buttons('cat-12')

    assert buttons[0][1] == {
        'action': CallbackAction.BACK_TO_CASES_FROM_CAT,
        'category_id': 12,
    }
    assert buttons[1][1] == {
        'action': CallbackAction.BACK_TO_CATEGORIES
    }


@pytest.mark.asyncio
async def test_vk_search_results_use_backend_and_preserve_order() -> None:
    """VK восстанавливает сохранённую выдачу без legacy CRUD."""

    backend = SimpleNamespace(
        get_cases=AsyncMock(
            return_value=[
                _case(1, 'Первый кейс'),
                _case(2, 'Второй кейс'),
            ]
        )
    )

    cases = await SearchHandler._get_cases_by_ids(
        backend,
        [2, 1, 999],
    )

    assert [case.id for case in cases] == [2, 1]
    backend.get_cases.assert_awaited_once_with()


def test_vk_category_cases_are_paginated_within_keyboard_limit() -> None:
    """Большая категория формирует допустимую постраничную клавиатуру."""

    cases = [_case(index, f'Кейс {index}') for index in range(1, 26)]

    markup = json.loads(
        CasesByCategoryKeyboard(
            cases,
            category_id=4,
            page=0,
        ).get_markup()
    )

    assert len(markup['buttons']) == 4
    page_payload = markup['buttons'][-1][0]['action']['payload']
    assert page_payload == {
        'action': 'category_case_page',
        'category_id': 4,
        'page': 1,
    }


@pytest.mark.asyncio
async def test_vk_uploader_rejects_insecure_upload_url(tmp_path) -> None:
    """Загрузчик не отправляет документ по полученному от VK HTTP-адресу."""

    api = SimpleNamespace(
        request=AsyncMock(
            return_value={
                'response': {
                    'upload_url': 'http://upload.example/document',
                }
            }
        )
    )
    path = tmp_path / 'document.docx'
    path.write_bytes(b'document')
    uploader = VKMessageDocumentUploader(attempts=1, retry_delay=0)

    with pytest.raises(VKDocumentUploadError):
        await uploader.upload(api, path, peer_id=123, title='Документ')

    api.request.assert_awaited_once_with(
        'docs.getMessagesUploadServer',
        {'type': 'doc', 'peer_id': 123},
    )
