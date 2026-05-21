from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import ButtonConfig, MessageConfig
from tg_bot.keyboards.back import BackKeyboard
from tg_bot.keyboards.case import CasesListKeyboard
from tg_bot.keyboards.main_menu import MainMenuKeyboard
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

    service = SearchService(session)
    results = await service.search_cases(query)

    if not results:
        await message.answer(MessageConfig.FOUND_NOTHING)
        return

    await state.clear()
    keyboard = CasesListKeyboard(results).get_markup()
    await message.answer(
        f'Найдено кейсов: {len(results)}\n\nВыберите подходящий:',
        reply_markup=keyboard
    )


@router.callback_query(F.data == 'back_to_search')
async def back_to_search(callback: CallbackQuery, state: FSMContext):
    """Вернуться к поиску."""

    await state.set_state(SearchStates.waiting_for_query)
    await callback.message.edit_text(
        MessageConfig.INSTRUCTIONS_FOR_SEARCH,
        reply_markup=BackKeyboard().get_markup()
    )
    await callback.answer()
