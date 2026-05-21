from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy.ext.asyncio import AsyncSession

from config import ButtonConfig, MessageConfig
from tg_bot.keyboards.back import BackKeyboard
from tg_bot.keyboards.case import CaseDetailKeyboard, CasesListKeyboard
from tg_bot.keyboards.main_menu import MainMenuKeyboard
from tg_bot.services.case import CaseService
from tg_bot.services.search import SearchService

router = Router()


class SearchStates(StatesGroup):
    waiting_for_query = State()


@router.message(F.text == ButtonConfig.SEARCH)
async def start_search(message: Message, state: FSMContext):
    """Начать поиск — запросить ключевые слова."""

    await state.set_state(SearchStates.waiting_for_query)
    await message.answer(
        MessageConfig.INSTRUCTIONS_FOR_SEARCH,
        reply_markup=BackKeyboard().get_markup()
    )


@router.message(SearchStates.waiting_for_query, F.text)
async def perform_search(message: Message, state: FSMContext, session: AsyncSession):
    """Выполнить поиск по запросу."""

    query = message.text.strip()

    if query == ButtonConfig.BACK:
        await state.clear()
        await message.answer(
            MessageConfig.SEARCH_CANCELED,
            reply_markup=MainMenuKeyboard().get_markup()
        )
        return

    if len(query) < 2:
        await message.answer(MessageConfig.TWO_SIMBOLS)
        return

    search_service = SearchService(session)
    results = await search_service.search_cases(query)

    await state.clear()

    if not results:
        await message.answer(
            MessageConfig.FOUND_NOTHING,
            reply_markup=MainMenuKeyboard().get_markup()
        )
        return

    await message.answer(
        f'🔎 Найдено кейсов: {len(results)}',
        reply_markup=MainMenuKeyboard().get_markup()
    )

    keyboard = CasesListKeyboard(results).get_markup()
    keyboard.inline_keyboard.append(
        [InlineKeyboardButton(text=ButtonConfig.BACK_TO_SEARCH, callback_data='back_to_search')]
    )

    await message.answer(
        'Выберите подходящий кейс:',
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith('case_'))
async def view_case_from_search(callback: CallbackQuery, session: AsyncSession):
    """Показать кейс из результатов поиска."""

    case_id = int(callback.data.split('_')[1])

    case_service = CaseService(session)
    case, documents = await case_service.get_case_with_documents(case_id)
    text = await case_service.format_case_text(case)

    back_button = InlineKeyboardButton(text=ButtonConfig.BACK_TO_SEARCH, callback_data='back_to_search')

    if documents:
        keyboard = CaseDetailKeyboard(documents, case.id).get_markup()
        keyboard.inline_keyboard.append([back_button])
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[back_button]])

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == 'back_to_search')
async def back_to_search(callback: CallbackQuery, state: FSMContext):
    """Вернуться к поиску."""

    await state.set_state(SearchStates.waiting_for_query)
    await callback.message.delete()
    await callback.message.answer(
        MessageConfig.INSTRUCTIONS_FOR_SEARCH,
        reply_markup=BackKeyboard().get_markup()
    )
    await callback.answer()
