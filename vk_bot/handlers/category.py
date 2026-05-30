from vkbottle import GroupEventType
from vkbottle.bot import BotLabeler, Message, MessageEvent
from sqlalchemy.ext.asyncio import AsyncSession

from config import ButtonConfig, MessageConfig
from vk_bot.handlers.base import BaseHandlers
from vk_bot.handlers.helpers import action_rule
from vk_bot.keyboards.base import BaseInlineKeyboard, make_payload
from vk_bot.keyboards.category import CasesByCategoryKeyboard, CategoriesKeyboard
from vk_bot.keyboards.main_menu import MainMenuKeyboard
from vk_bot.services.case import CaseService
from vk_bot.services.category import CategoryService


class CategoriesHandler(BaseHandlers):
    """Обработчик категорий."""

    def __init__(self):
        self.labeler = BotLabeler()
        self._register()

    def _register(self) -> None:
        @self.labeler.private_message(text=ButtonConfig.CATEGORIES)
        async def show_categories(message: Message, session: AsyncSession):
            service = CategoryService(session)
            categories = await service.get_all_categories()

            if not categories:
                await self.send_message(
                    message,
                    MessageConfig.NO_CATEGORIES,
                    MainMenuKeyboard().get_markup(),
                )
                return

            await self.cleanup_current_and_previous(message)

            keyboard = CategoriesKeyboard(categories).get_markup()
            keyboard = BaseInlineKeyboard.append_buttons(keyboard, [
                (ButtonConfig.MAIN_MENU, make_payload('back_to_main_menu')),
            ])
            await self.send_message(message, '📂 Выберите категорию:', keyboard)

        @self.labeler.raw_event(
            GroupEventType.MESSAGE_EVENT,
            MessageEvent,
            action_rule('cat'),
        )
        async def show_cases_by_category(event: MessageEvent, session: AsyncSession):
            category_id = event.payload['id']

            category_service = CategoryService(session)
            category = await category_service.get_category_by_id(category_id)
            case_service = CaseService(session)
            cases = await case_service.get_cases_by_category(category_id)

            if not cases:
                keyboard = BaseInlineKeyboard()._build_inline_markup([
                    (ButtonConfig.BACK_TO_CATEGORIES, make_payload('back_to_categories')),
                    (ButtonConfig.MAIN_MENU, make_payload('back_to_main_menu')),
                ])
                await event.send_empty_answer()
                await event.edit_message(MessageConfig.NO_CASES_IN_CAT, keyboard=keyboard)
                return

            keyboard = CasesByCategoryKeyboard(cases, category_id).get_markup()
            keyboard = BaseInlineKeyboard.append_buttons(keyboard, [
                (ButtonConfig.MAIN_MENU, make_payload('back_to_main_menu')),
            ])

            await event.send_empty_answer()
            await event.edit_message(
                f'📂 Категория: {category.name}\n\nВыберите кейс:',
                keyboard=keyboard,
            )

        @self.labeler.raw_event(
            GroupEventType.MESSAGE_EVENT,
            MessageEvent,
            action_rule('back_to_categories'),
        )
        async def back_to_categories(event: MessageEvent, session: AsyncSession):
            service = CategoryService(session)
            categories = await service.get_all_categories()

            keyboard = CategoriesKeyboard(categories).get_markup()
            keyboard = BaseInlineKeyboard.append_buttons(keyboard, [
                (ButtonConfig.MAIN_MENU, make_payload('back_to_main_menu')),
            ])

            await event.send_empty_answer()
            await event.edit_message('📂 Выберите категорию:', keyboard=keyboard)


categories_handler = CategoriesHandler()
categories_router = categories_handler.labeler
