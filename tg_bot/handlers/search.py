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
from tg_bot.handlers.base import BaseHandlers
from tg_bot.keyboards.case import CaseDetailKeyboard
from tg_bot.keyboards.main_menu import MainMenuKeyboard
from tg_bot.keyboards.search import SearchCasesListKeyboard
from tg_bot.services.case import CaseService
from tg_bot.services.search import SearchService


class SearchStates(StatesGroup):
    waiting_for_query = State()


class SearchHandler(BaseHandlers):
    """Обработчик поиска."""

    def __init__(self):
        self.router = Router()
        self.router.message(F.text == ButtonConfig.SEARCH)(self.start_search)
        self.router.message(SearchStates.waiting_for_query, F.text)(self.perform_search)
        self.router.callback_query(F.data.startswith('case_search_'))(self.view_case_from_search)
        self.router.callback_query(F.data == 'back_to_search')(self.back_to_search)
        self.router.callback_query(F.data == 'back_to_search_results')(self.back_to_search_results)
        self.router.callback_query(F.data == 'back_to_main_menu')(self.back_to_main_menu)

    async def start_search(self, message: Message, state: FSMContext):
        """Начать поиск — запросить ключевые слова."""

        await state.set_state(SearchStates.waiting_for_query)

        await self.cleanup_current_and_previous(message)

        search_msg = await message.answer(
            MessageConfig.INSTRUCTIONS_FOR_SEARCH,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=ButtonConfig.MAIN_MENU, callback_data='back_to_main_menu')]
            ])
        )

        await state.update_data(search_msg_id=search_msg.message_id)

    async def perform_search(self, message: Message, state: FSMContext, session: AsyncSession):
        """Выполнить поиск по запросу."""

        query = message.text.strip()

        if len(query) < 2:
            await message.answer(MessageConfig.TWO_SIMBOLS)
            return

        search_service = SearchService(session)
        results = await search_service.search_cases(query)

        await message.delete()

        data = await state.get_data()
        search_msg_id = data.get('search_msg_id')

        if search_msg_id:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=search_msg_id)
            except Exception:
                pass

        await state.clear()

        if not results:
            await message.answer(
                MessageConfig.FOUND_NOTHING,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=ButtonConfig.BACK_TO_SEARCH, callback_data='back_to_search')],
                    [InlineKeyboardButton(text=ButtonConfig.MAIN_MENU, callback_data='back_to_main_menu')]
                ])
            )
            return

        await state.update_data(search_results=[case.id for case in results], search_query=query)

        keyboard = SearchCasesListKeyboard(results).get_markup()
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text=ButtonConfig.BACK_TO_SEARCH, callback_data='back_to_search')]
        )
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text=ButtonConfig.MAIN_MENU, callback_data='back_to_main_menu')]
        )

        await message.answer(
            f'🔎 Найдено кейсов: {len(results)}\n\nВыберите подходящий:',
            reply_markup=keyboard
        )

    async def view_case_from_search(self, callback: CallbackQuery, session: AsyncSession, state: FSMContext):
        """Показать кейс из результатов поиска."""

        case_id = int(callback.data.split('_')[2])

        data = await state.get_data()
        case_ids = data.get('search_results', [])
        query = data.get('search_query', '')

        case_service = CaseService(session)
        case, documents = await case_service.get_case_with_documents(case_id)
        text = await case_service.format_case_text(case)

        keyboard = CaseDetailKeyboard(documents, case.id).get_markup()
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text=ButtonConfig.BACK_TO_SEARCH_RESULTS, callback_data='back_to_search_results')]
        )
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text=ButtonConfig.MAIN_MENU, callback_data='back_to_main_menu')]
        )

        await state.update_data(search_results=case_ids, search_query=query)

        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()

    async def back_to_search_results(self, callback: CallbackQuery, state: FSMContext, session: AsyncSession):
        """Вернуться к результатам поиска."""

        data = await state.get_data()
        case_ids = data.get('search_results', [])
        query = data.get('search_query', '')

        if not case_ids:
            await self.back_to_search(callback, state)
            return

        case_service = CaseService(session)
        cases = []
        for case_id in case_ids:
            case = await case_service.case_crud.get_by_id(case_id)
            if case:
                cases.append(case)

        keyboard = SearchCasesListKeyboard(cases).get_markup()
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text=ButtonConfig.BACK_TO_SEARCH, callback_data='back_to_search')]
        )
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text=ButtonConfig.MAIN_MENU, callback_data='back_to_main_menu')]
        )

        await callback.message.edit_text(
            f'🔎 Результаты поиска по запросу "{query}":\n\nНайдено кейсов: {len(cases)}\n\nВыберите подходящий:',
            reply_markup=keyboard
        )
        await callback.answer()

    async def back_to_search(self, callback: CallbackQuery, state: FSMContext):
        """Вернуться к поиску."""

        await state.set_state(SearchStates.waiting_for_query)

        await callback.message.edit_text(
            MessageConfig.INSTRUCTIONS_FOR_SEARCH,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=ButtonConfig.MAIN_MENU, callback_data='back_to_main_menu')]
            ])
        )

        await state.update_data(search_msg_id=callback.message.message_id)
        await callback.answer()

    async def back_to_main_menu(self, callback: CallbackQuery, state: FSMContext):
        """Вернуться в главное меню."""

        await state.clear()
        await callback.message.delete()
        await callback.message.answer(
            MessageConfig.BACK_TO_MAIN_MENU,
            reply_markup=MainMenuKeyboard().get_markup()
        )
        await callback.answer()


search_handler = SearchHandler()
search_router = search_handler.router
