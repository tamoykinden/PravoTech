from vkbottle import GroupEventType
from vkbottle.bot import BotLabeler, Message, MessageEvent
from sqlalchemy.ext.asyncio import AsyncSession

from config import ButtonConfig, MessageConfig
from vk_bot.handlers.base import BaseHandlers
from vk_bot.handlers.helpers import action_rule
from vk_bot.keyboards.base import BaseInlineKeyboard, make_payload
from vk_bot.keyboards.case import CaseDetailKeyboard, CasesListKeyboard
from vk_bot.keyboards.main_menu import MainMenuKeyboard
from vk_bot.services.case import CaseService


class CasesHandler(BaseHandlers):
    """Обработчик кейсов."""

    def __init__(self):
        self.labeler = BotLabeler()
        self._register()

    def _register(self) -> None:
        @self.labeler.private_message(text=ButtonConfig.CASES)
        async def list_cases(message: Message, session: AsyncSession):
            service = CaseService(session)
            cases = await service.get_all_cases()

            if not cases:
                await self.send_message(
                    message,
                    MessageConfig.NO_CASES,
                    MainMenuKeyboard().get_markup(),
                )
                return

            await self.cleanup_current_and_previous(message)

            keyboard = CasesListKeyboard(cases).get_markup()
            keyboard = BaseInlineKeyboard.append_buttons(keyboard, [
                (ButtonConfig.MAIN_MENU, make_payload('back_to_main_menu')),
            ])
            await self.send_message(message, '📋 Выберите кейс:', keyboard)

        @self.labeler.raw_event(
            GroupEventType.MESSAGE_EVENT,
            MessageEvent,
            action_rule('case_list'),
        )
        async def view_case_from_list(event: MessageEvent, session: AsyncSession):
            case_id = event.payload['id']
            await self._show_case(event, session, case_id, back_buttons=[
                (ButtonConfig.BACK_TO_CASES, make_payload('back_to_cases')),
                (ButtonConfig.MAIN_MENU, make_payload('back_to_main_menu')),
            ])

        @self.labeler.raw_event(
            GroupEventType.MESSAGE_EVENT,
            MessageEvent,
            action_rule('case_cat'),
        )
        async def view_case_from_category(event: MessageEvent, session: AsyncSession):
            case_id = event.payload['id']
            category_id = event.payload['category_id']
            await self._show_case(event, session, case_id, back_buttons=[
                (
                    ButtonConfig.BACK_TO_CASES,
                    make_payload('back_to_cases_from_cat', category_id=category_id),
                ),
                (ButtonConfig.BACK_TO_CATEGORIES, make_payload('back_to_categories')),
                (ButtonConfig.MAIN_MENU, make_payload('back_to_main_menu')),
            ])

        @self.labeler.raw_event(
            GroupEventType.MESSAGE_EVENT,
            MessageEvent,
            action_rule('back_to_cases'),
        )
        async def back_to_cases_list(event: MessageEvent, session: AsyncSession):
            await self._show_cases_list(event, session)

        @self.labeler.raw_event(
            GroupEventType.MESSAGE_EVENT,
            MessageEvent,
            action_rule('back_to_cases_from_cat'),
        )
        async def back_to_cases_by_category(event: MessageEvent, session: AsyncSession):
            category_id = event.payload['category_id']
            service = CaseService(session)
            cases = await service.get_cases_by_category(category_id)

            keyboard = CasesListKeyboard(cases).get_markup()
            keyboard = BaseInlineKeyboard.append_buttons(keyboard, [
                (ButtonConfig.BACK_TO_CATEGORIES, make_payload('back_to_categories')),
                (ButtonConfig.MAIN_MENU, make_payload('back_to_main_menu')),
            ])

            await event.send_empty_answer()
            await event.edit_message('📋 Выберите кейс:', keyboard=keyboard)

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

        await event.send_empty_answer()
        await event.edit_message(text, keyboard=keyboard)

    async def _show_cases_list(self, event: MessageEvent, session: AsyncSession) -> None:
        service = CaseService(session)
        cases = await service.get_all_cases()

        keyboard = CasesListKeyboard(cases).get_markup()
        keyboard = BaseInlineKeyboard.append_buttons(keyboard, [
            (ButtonConfig.MAIN_MENU, make_payload('back_to_main_menu')),
        ])

        await event.send_empty_answer()
        await event.edit_message('📋 Выберите кейс:', keyboard=keyboard)


cases_handler = CasesHandler()
cases_router = cases_handler.labeler
