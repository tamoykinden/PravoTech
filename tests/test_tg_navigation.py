"""Регрессионные тесты навигации Telegram-бота."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.schemas import CaseRead, DocumentRead
from tg_bot.handlers.document import DocumentHandler
from tg_bot.handlers.search import SearchHandler
from tg_bot.keyboards.case import CaseDetailKeyboard


def _case(case_id: int, title: str) -> CaseRead:
    """Создаёт минимальный кейс для тестирования клавиатур."""

    return CaseRead(
        id=case_id,
        title=title,
        solution='Пошаговое решение',
        category_id=1,
    )


def test_document_callback_contains_parent_case_id() -> None:
    """Кнопка документа сохраняет ID кейса для обратной навигации."""

    document = DocumentRead(id=7, title='Претензия', case_id=3)

    markup = CaseDetailKeyboard([document], case_id=3).get_markup()

    assert markup.inline_keyboard[0][0].callback_data == 'doc_7_3_all'


@pytest.mark.asyncio
async def test_back_to_search_results_uses_backend_and_preserves_order() -> None:
    """Поисковая выдача восстанавливается через активный backend-клиент."""

    callback = SimpleNamespace(
        message=SimpleNamespace(edit_text=AsyncMock()),
        answer=AsyncMock(),
    )
    state = SimpleNamespace(
        get_data=AsyncMock(
            return_value={
                'search_results': [2, 1, 999],
                'search_query': 'товар',
            }
        )
    )
    backend = SimpleNamespace(
        get_cases=AsyncMock(
            return_value=[
                _case(1, 'Первый кейс'),
                _case(2, 'Второй кейс'),
            ]
        )
    )

    await SearchHandler().back_to_search_results(callback, state, backend)

    backend.get_cases.assert_awaited_once_with()
    markup = callback.message.edit_text.await_args.kwargs['reply_markup']
    assert [
        row[0].callback_data
        for row in markup.inline_keyboard[:2]
    ] == ['case_search_2', 'case_search_1']
    callback.answer.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_back_from_document_restores_parent_case() -> None:
    """Кнопка «Назад к кейсу» заменяет документ карточкой кейса."""

    document = DocumentRead(id=7, title='Претензия', case_id=3)
    case = _case(3, 'Возврат товара').model_copy(
        update={'documents': [document]}
    )
    callback = SimpleNamespace(
        data='back_to_case_3_search',
        message=SimpleNamespace(
            delete=AsyncMock(),
            answer=AsyncMock(),
        ),
        answer=AsyncMock(),
    )
    backend = SimpleNamespace(get_case=AsyncMock(return_value=case))

    await DocumentHandler().back_to_case(callback, backend)

    backend.get_case.assert_awaited_once_with(3)
    callback.message.delete.assert_awaited_once_with()
    sent_text = callback.message.answer.await_args.args[0]
    sent_markup = callback.message.answer.await_args.kwargs['reply_markup']
    assert 'Возврат товара' in sent_text
    assert sent_markup.inline_keyboard[0][0].callback_data == 'doc_7_3_search'
    assert (
        sent_markup.inline_keyboard[1][0].callback_data
        == 'back_to_search_results'
    )
    callback.answer.assert_awaited_once_with()


def test_category_origin_restores_category_navigation() -> None:
    """После документа кейс возвращает к исходной категории."""

    markup = SimpleNamespace(inline_keyboard=[])

    DocumentHandler._append_origin_navigation(markup, 'cat-12')

    assert [
        row[0].callback_data
        for row in markup.inline_keyboard
    ] == ['back_to_cases_from_cat_12', 'back_to_categories']
