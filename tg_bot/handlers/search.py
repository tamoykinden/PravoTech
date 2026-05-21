from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from tg_bot.keyboards import MainMenuKeyboard
from tg_bot.keyboards.back import BackKeyboard
from tg_bot.keyboards.case import CasesListKeyboard
from tg_bot.services.search import SearchService

router = Router()


class SearchStates(StatesGroup):
    waiting_for_query = State()


@router.message(F.text == 'Поиск кейса')
async def start_search(message: Message, state: FSMContext):
    """Начать поиск — запросить ключевые слова."""

    await state.set_state(SearchStates.waiting_for_query)
    await message.answer(
        'Введите ключевые слова для поиска (через пробел):\n\n'
        'Например: <i>шум соседи</i> или <i>возврат товара</i>',
        reply_markup=BackKeyboard().get_markup()
    )


@router.message(SearchStates.waiting_for_query, F.text)
async def perform_search(message: Message, state: FSMContext, session: AsyncSession):
    """Выполнить поиск по запросу."""
    query = message.text.strip()

    if query == 'Назад':
        await state.clear()
        await message.answer(
            '🔍 Поиск отменён.',
            reply_markup=MainMenuKeyboard().get_markup()
        )
        return

    if len(query) < 2:
        await message.answer('Введите минимум 2 символа для поиска.')
        return

    service = SearchService(session)
    results = await service.search_cases(query)

    await state.clear()

    if not results:
        await message.answer(
            'Ничего не найдено.\n\n'
            'Попробуйте изменить запрос или обратитесь в обратную связь, '
            'если вашей ситуации нет в боте.',
            reply_markup=BackKeyboard().get_markup()
        )
        return

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
        'Введите ключевые слова для поиска (через пробел):',
        reply_markup=BackKeyboard().get_markup()
    )
    await callback.answer()
