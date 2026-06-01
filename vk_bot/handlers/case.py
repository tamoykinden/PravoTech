from vkbottle import GroupEventType
from vkbottle.bot import BotLabeler, Message, MessageEvent
from sqlalchemy.ext.asyncio import AsyncSession

from config import ButtonConfig, CallbackAction, MessageConfig
from vk_bot.handlers.base import BaseHandlers
from vk_bot.keyboards.base import BaseInlineKeyboard
from vk_bot.keyboards.case import CaseDetailKeyboard, CasesListKeyboard
from vk_bot.services.case import CaseService
from vk_bot.support.dispatch import VkDispatchSupport


class CasesHandler(BaseHandlers):
    """Обработчик кейсов."""

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
        @self.labeler.private_message(text=ButtonConfig.CASES)
        async def list_cases(message: Message, session: AsyncSession):
            service = CaseService(session)
            cases = await service.get_all_cases()

            if not cases:
                await self.restore_main_menu(
                    message.peer_id,
                    message.ctx_api,
                    MessageConfig.NO_CASES,
                )
                return

            await self.cleanup_current_and_previous(message)

            keyboard = CasesListKeyboard(cases).get_markup()
            keyboard = BaseInlineKeyboard.append_buttons(keyboard, [self._main_menu_button()])
            await self.send_inline_message(message, MessageConfig.SELECT_CASE, keyboard)

        @self.labeler.raw_event(
            GroupEventType.MESSAGE_EVENT,
            MessageEvent,
            VkDispatchSupport.action_rule(CallbackAction.CASE_LIST),
        )
        async def view_case_from_list(event: MessageEvent, session: AsyncSession):
            case_id = event.payload['id']
            await self._show_case(event, session, case_id, back_buttons=[
                (
                    ButtonConfig.BACK_TO_CASES,
                    BaseInlineKeyboard.make_payload(CallbackAction.BACK_TO_CASES),
                ),
                self._main_menu_button(),
            ])

        @self.labeler.raw_event(
            GroupEventType.MESSAGE_EVENT,
            MessageEvent,
            VkDispatchSupport.action_rule(CallbackAction.CASE_CAT),
        )
        async def view_case_from_category(event: MessageEvent, session: AsyncSession):
            case_id = event.payload['id']
            category_id = event.payload['category_id']
            await self._show_case(event, session, case_id, back_buttons=[
                (
                    ButtonConfig.BACK_TO_CASES,
                    BaseInlineKeyboard.make_payload(
                        CallbackAction.BACK_TO_CASES_FROM_CAT,
                        category_id=category_id,
                    ),
                ),
                (
                    ButtonConfig.BACK_TO_CATEGORIES,
                    BaseInlineKeyboard.make_payload(CallbackAction.BACK_TO_CATEGORIES),
                ),
                self._main_menu_button(),
            ])

        @self.labeler.raw_event(
            GroupEventType.MESSAGE_EVENT,
            MessageEvent,
            VkDispatchSupport.action_rule(CallbackAction.BACK_TO_CASES),
        )
        async def back_to_cases_list(event: MessageEvent, session: AsyncSession):
            await self._show_cases_list(event, session)

        @self.labeler.raw_event(
            GroupEventType.MESSAGE_EVENT,
            MessageEvent,
            VkDispatchSupport.action_rule(CallbackAction.BACK_TO_CASES_FROM_CAT),
        )
        async def back_to_cases_by_category(event: MessageEvent, session: AsyncSession):
            category_id = event.payload['category_id']
            service = CaseService(session)
            cases = await service.get_cases_by_category(category_id)

            keyboard = CasesListKeyboard(cases).get_markup()
            keyboard = BaseInlineKeyboard.append_buttons(keyboard, [
                (
                    ButtonConfig.BACK_TO_CATEGORIES,
                    BaseInlineKeyboard.make_payload(CallbackAction.BACK_TO_CATEGORIES),
                ),
                self._main_menu_button(),
            ])

            await self.safe_answer_event(event)
            await event.edit_message(MessageConfig.SELECT_CASE, keyboard=keyboard)

    async def _show_case(
        self,
        event: MessageEvent,
        session: AsyncSession,
        case_id: int,
        back_buttons: list,
    ) -> None:
        service = CaseService(session)
        case, documents = await service.get_case_with_documents(case_id)
        text = await service.format_case_text(case)

        keyboard = CaseDetailKeyboard(documents, case.id).get_markup()
        keyboard = BaseInlineKeyboard.append_buttons(keyboard, back_buttons)

        await self.safe_answer_event(event)
        await event.edit_message(text, keyboard=keyboard)

    async def _show_cases_list(self, event: MessageEvent, session: AsyncSession) -> None:
        service = CaseService(session)
        cases = await service.get_all_cases()

        keyboard = CasesListKeyboard(cases).get_markup()
        keyboard = BaseInlineKeyboard.append_buttons(keyboard, [self._main_menu_button()])

        await self.safe_answer_event(event)
        await event.edit_message(MessageConfig.SELECT_CASE, keyboard=keyboard)


cases_handler = CasesHandler()
cases_router = cases_handler.labeler
