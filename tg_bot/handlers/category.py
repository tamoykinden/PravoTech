from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy.ext.asyncio import AsyncSession

from config import ButtonConfig, MessageConfig
from tg_bot.handlers.base import BaseHandlers
from tg_bot.keyboards.category import CasesByCategoryKeyboard, CategoriesKeyboard
from tg_bot.keyboards.main_menu import MainMenuKeyboard
from tg_bot.services.case import CaseService
from tg_bot.services.category import CategoryService


class CategoriesHandler(BaseHandlers):
    """Обработчик категорий."""

    def __init__(self):
        self.router = Router()
        self.router.message(F.text == ButtonConfig.CATEGORIES)(self.show_categories)
        self.router.callback_query(F.data.startswith('cat_'))(self.show_cases_by_category)
        self.router.callback_query(F.data == 'back_to_categories')(self.back_to_categories)
        self.router.callback_query(F.data == 'back_to_main_menu')(self.back_to_main_menu)

    async def show_categories(self, message: Message, session: AsyncSession):
        """Показать все категории."""

        service = CategoryService(session)
        categories = await service.get_all_categories()

        if not categories:
            await message.answer(
                MessageConfig.NO_CATEGORIES,
                reply_markup=MainMenuKeyboard().get_markup()
            )
            return

        await self.cleanup_current_and_previous(message)

        keyboard = CategoriesKeyboard(categories).get_markup()
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text=ButtonConfig.MAIN_MENU, callback_data='back_to_main_menu')]
        )

        await message.answer('📂 Выберите категорию:', reply_markup=keyboard)

    async def show_cases_by_category(self, callback: CallbackQuery, session: AsyncSession):
        """Показать кейсы из выбранной категории."""

        category_id = int(callback.data.split('_')[1])

        service = CategoryService(session)
        category = await service.get_category_by_id(category_id)
        case_service = CaseService(session)
        cases = await case_service.get_cases_by_category(category_id)

        if not cases:
            await callback.message.edit_text(
                MessageConfig.NO_CASES_IN_CAT,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=ButtonConfig.BACK_TO_CATEGORIES, callback_data='back_to_categories')],
                    [InlineKeyboardButton(text=ButtonConfig.MAIN_MENU, callback_data='back_to_main_menu')]
                ])
            )
            await callback.answer()
            return

        keyboard = CasesByCategoryKeyboard(cases, category_id).get_markup()
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text=ButtonConfig.MAIN_MENU, callback_data='back_to_main_menu')]
        )

        await callback.message.edit_text(
            f'📂 Категория: {category.name}\n\nВыберите кейс:',
            reply_markup=keyboard
        )
        await callback.answer()

    async def back_to_categories(self, callback: CallbackQuery, session: AsyncSession):
        """Вернуться к списку категорий."""

        service = CategoryService(session)
        categories = await service.get_all_categories()

        keyboard = CategoriesKeyboard(categories).get_markup()
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text=ButtonConfig.MAIN_MENU, callback_data='back_to_main_menu')]
        )

        await callback.message.edit_text('📂 Выберите категорию:', reply_markup=keyboard)
        await callback.answer()

    async def back_to_main_menu(self, callback: CallbackQuery):
        """Вернуться в главное меню."""

        await callback.message.delete()
        await callback.message.answer(
            MessageConfig.BACK_TO_MAIN_MENU,
            reply_markup=MainMenuKeyboard().get_markup()
        )
        await callback.answer()


categories_handler = CategoriesHandler()
categories_router = categories_handler.router
