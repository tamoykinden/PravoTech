from sqlalchemy.ext.asyncio import AsyncSession
from vkbottle import GroupEventType
from vkbottle.bot import BotLabeler, Message, MessageEvent

from config import ButtonConfig, CallbackAction, MessageConfig
from vk_bot.handlers.base import BaseHandlers
from vk_bot.keyboards.base import BaseInlineKeyboard
from vk_bot.keyboards.category import CasesByCategoryKeyboard, CategoriesKeyboard
from vk_bot.services.case import CaseService
from vk_bot.services.category import CategoryService
from vk_bot.support.dispatch import VkDispatchSupport


class CategoriesHandler(BaseHandlers):
    """Обработчик категорий."""

    def __init__(self):
        self.labeler = BotLabeler()
        self._register()

    @staticmethod
    def _main_menu_button() -> tuple[str, dict]:
        return (
            ButtonConfig.MAIN_MENU,
            BaseInlineKeyboard.make_payload(CallbackAction.BACK_TO_MAIN_MENU),
        )

    def _register(self) -> None:
        @self.labeler.private_message(text=ButtonConfig.CATEGORIES)
        async def show_categories(message: Message, session: AsyncSession):
            service = CategoryService(session)
            categories = await service.get_all_categories()

            if not categories:
                await self.restore_main_menu(
                    message.peer_id,
                    message.ctx_api,
                    MessageConfig.NO_CATEGORIES,
                )
                return

            await self.cleanup_current_and_previous(message)

            keyboard = CategoriesKeyboard(categories).get_markup()
            keyboard = BaseInlineKeyboard.append_buttons(keyboard, [self._main_menu_button()])
            await self.send_inline_message(message, MessageConfig.SELECT_CATEGORY, keyboard)

        @self.labeler.raw_event(
            GroupEventType.MESSAGE_EVENT,
            MessageEvent,
            VkDispatchSupport.action_rule(CallbackAction.CATEGORY),
        )
        async def show_cases_by_category(event: MessageEvent, session: AsyncSession):
            category_id = event.payload['id']
            await self._show_category_cases(
                event,
                session,
                category_id,
                page=0,
            )

        @self.labeler.raw_event(
            GroupEventType.MESSAGE_EVENT,
            MessageEvent,
            VkDispatchSupport.action_rule('category_case_page'),
        )
        async def paginate_category_cases(
            event: MessageEvent,
            session: AsyncSession,
        ):
            await self._show_category_cases(
                event,
                session,
                category_id=event.payload['category_id'],
                page=event.payload['page'],
            )

        @self.labeler.raw_event(
            GroupEventType.MESSAGE_EVENT,
            MessageEvent,
            VkDispatchSupport.action_rule(CallbackAction.BACK_TO_CATEGORIES),
        )
        async def back_to_categories(event: MessageEvent, session: AsyncSession):
            service = CategoryService(session)
            categories = await service.get_all_categories()

            keyboard = CategoriesKeyboard(categories).get_markup()
            keyboard = BaseInlineKeyboard.append_buttons(keyboard, [self._main_menu_button()])

            await self.safe_answer_event(event)
            await event.edit_message(MessageConfig.SELECT_CATEGORY, keyboard=keyboard)

    async def _show_category_cases(
        self,
        event: MessageEvent,
        session: AsyncSession,
        category_id: int,
        page: int,
    ) -> None:
        """Показывает одну допустимую VK страницу кейсов категории."""

        category_service = CategoryService(session)
        category = await category_service.get_category_by_id(category_id)
        case_service = CaseService(session)
        cases = await case_service.get_cases_by_category(category_id)

        if not cases:
            keyboard = BaseInlineKeyboard.build_inline_markup([
                (
                    ButtonConfig.BACK_TO_CATEGORIES,
                    BaseInlineKeyboard.make_payload(
                        CallbackAction.BACK_TO_CATEGORIES
                    ),
                ),
                self._main_menu_button(),
            ])
            await self.safe_answer_event(event)
            await event.edit_message(
                MessageConfig.NO_CASES_IN_CAT,
                keyboard=keyboard,
            )
            return

        keyboard = CasesByCategoryKeyboard(
            cases,
            category_id,
            page=page,
        ).get_markup()
        keyboard = BaseInlineKeyboard.append_buttons(
            keyboard,
            [
                (
                    ButtonConfig.BACK_TO_CATEGORIES,
                    BaseInlineKeyboard.make_payload(
                        CallbackAction.BACK_TO_CATEGORIES
                    ),
                ),
                self._main_menu_button(),
            ],
        )

        await self.safe_answer_event(event)
        await event.edit_message(
            MessageConfig.SELECT_CATEGORY_CASES.format(
                name=category.name
            ),
            keyboard=keyboard,
        )


categories_handler = CategoriesHandler()
categories_router = categories_handler.labeler
