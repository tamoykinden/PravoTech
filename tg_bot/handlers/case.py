from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message

from bot_client import BackendClient
from config import ButtonConfig, MessageConfig
from tg_bot.handlers.base import BaseHandlers
from tg_bot.keyboards.case import CaseDetailKeyboard, CasesListKeyboard
from tg_bot.keyboards.main_menu import MainMenuKeyboard
from tg_bot.services.case import CaseService


class CasesHandler(BaseHandlers):
    """Обработчик кейсов."""

    def __init__(self):
        self.router = Router()
        self.router.message(F.text == ButtonConfig.CASES)(self.list_cases)
        self.router.callback_query(F.data.startswith('case_list_'))(self.view_case_from_list)
        self.router.callback_query(F.data.startswith('case_cat_'))(self.view_case_from_category)
        self.router.callback_query(F.data == 'back_to_cases')(self.back_to_cases_list)
        self.router.callback_query(F.data.startswith('back_to_cases_from_cat_'))(self.back_to_cases_by_category)
        self.router.callback_query(F.data == 'back_to_main_menu')(self.back_to_main_menu)

    async def list_cases(self, message: Message, session: BackendClient):
        """Показать список всех кейсов (из главного меню)."""

        service = CaseService(session)
        cases = await service.get_all_cases()

        if not cases:
            await message.answer(
                MessageConfig.NO_CASES,
                reply_markup=MainMenuKeyboard().get_markup()
            )
            return

        await self.cleanup_current_and_previous(message)

        keyboard = CasesListKeyboard(cases).get_markup()
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text=ButtonConfig.MAIN_MENU, callback_data='back_to_main_menu')]
        )

        await message.answer('📋 Выберите кейс:', reply_markup=keyboard)

    async def view_case_from_list(self, callback: CallbackQuery, session: BackendClient):
        """Показать кейс из общего списка."""

        case_id = int(callback.data.split('_')[2])

        service = CaseService(session)
        case, documents = await service.get_case_with_documents(case_id)
        text = await service.format_case_text(case)

        keyboard = CaseDetailKeyboard(
            documents,
            case.id,
            origin='all',
        ).get_markup()
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text=ButtonConfig.BACK_TO_CASES, callback_data='back_to_cases')]
        )
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text=ButtonConfig.MAIN_MENU, callback_data='back_to_main_menu')]
        )

        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()

    async def view_case_from_category(self, callback: CallbackQuery, session: BackendClient):
        """Показать кейс из категории."""

        parts = callback.data.split('_')
        case_id = int(parts[2])
        category_id = int(parts[3])

        service = CaseService(session)
        case, documents = await service.get_case_with_documents(case_id)
        text = await service.format_case_text(case)

        keyboard = CaseDetailKeyboard(
            documents,
            case.id,
            origin=f'cat-{category_id}',
        ).get_markup()
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text=ButtonConfig.BACK_TO_CASES, callback_data=f'back_to_cases_from_cat_{category_id}')]
        )
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text=ButtonConfig.BACK_TO_CATEGORIES, callback_data='back_to_categories')]
        )
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text=ButtonConfig.MAIN_MENU, callback_data='back_to_main_menu')]
        )

        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()

    async def back_to_cases_list(self, callback: CallbackQuery, session: BackendClient):
        """Вернуться к списку всех кейсов."""

        service = CaseService(session)
        cases = await service.get_all_cases()

        keyboard = CasesListKeyboard(cases).get_markup()
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text=ButtonConfig.MAIN_MENU, callback_data='back_to_main_menu')]
        )

        await callback.message.delete()
        await callback.message.answer('📋 Выберите кейс:', reply_markup=keyboard)
        await callback.answer()

    async def back_to_cases_by_category(self, callback: CallbackQuery, session: BackendClient):
        """Вернуться к списку кейсов по категории."""

        category_id = int(callback.data.split('_')[-1])

        case_service = CaseService(session)
        cases = await case_service.get_cases_by_category(category_id)

        keyboard = CasesListKeyboard(cases).get_markup()
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text=ButtonConfig.BACK_TO_CATEGORIES, callback_data='back_to_categories')]
        )
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text=ButtonConfig.MAIN_MENU, callback_data='back_to_main_menu')]
        )

        await callback.message.edit_text('📋 Выберите кейс:', reply_markup=keyboard)
        await callback.answer()

    async def back_to_main_menu(self, callback: CallbackQuery):
        """Вернуться в главное меню."""

        await callback.message.delete()
        await callback.message.answer(
            MessageConfig.BACK_TO_MAIN_MENU,
            reply_markup=MainMenuKeyboard().get_markup()
        )
        await callback.answer()


cases_handler = CasesHandler()
cases_router = cases_handler.router
