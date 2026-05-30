from vkbottle import BaseStateGroup, GroupEventType
from vkbottle.bot import BotLabeler, Message, MessageEvent
from sqlalchemy.ext.asyncio import AsyncSession

from config import ButtonConfig, MessageConfig
from vk_bot.handlers.base import BaseHandlers
from vk_bot.handlers.helpers import action_rule, random_id
from vk_bot.keyboards.base import BaseInlineKeyboard, make_payload
from vk_bot.keyboards.case import CaseDetailKeyboard
from vk_bot.keyboards.main_menu import MainMenuKeyboard
from vk_bot.keyboards.search import SearchCasesListKeyboard
from vk_bot.services.case import CaseService
from vk_bot.services.search import SearchService


class SearchStates(BaseStateGroup):
    WAITING = 'waiting_for_query'
    VIEWING = 'viewing_results'


class SearchHandler(BaseHandlers):
    """Обработчик поиска."""

    def __init__(self):
        self.labeler = BotLabeler()
        self._register()

    def _register(self) -> None:
        @self.labeler.private_message(text=ButtonConfig.SEARCH)
        async def start_search(message: Message, state_dispenser):
            await state_dispenser.set(message.peer_id, SearchStates.WAITING)

            await self.cleanup_current_and_previous(message)

            keyboard = BaseInlineKeyboard()._build_inline_markup([
                (ButtonConfig.MAIN_MENU, make_payload('back_to_main_menu')),
            ])
            search_msg = await self.send_message(
                message,
                MessageConfig.INSTRUCTIONS_FOR_SEARCH,
                keyboard,
            )
            await state_dispenser.set(
                message.peer_id,
                SearchStates.WAITING,
                search_msg_id=search_msg.conversation_message_id,
            )

        @self.labeler.private_message(state=SearchStates.WAITING)
        async def perform_search(message: Message, session: AsyncSession, state_dispenser):
            query = message.text.strip()

            if len(query) < 2:
                await self.send_message(message, MessageConfig.TWO_SIMBOLS)
                return

            search_service = SearchService(session)
            results = await search_service.search_cases(query)

            state_peer = await state_dispenser.get(message.peer_id)
            search_msg_id = state_peer.payload.get('search_msg_id') if state_peer else None

            if message.conversation_message_id:
                await self.safe_delete_message(message, message.conversation_message_id)

            if search_msg_id:
                await self.safe_delete_message(message, search_msg_id)

            if not results:
                keyboard = BaseInlineKeyboard()._build_inline_markup([
                    (ButtonConfig.BACK_TO_SEARCH, make_payload('back_to_search')),
                    (ButtonConfig.MAIN_MENU, make_payload('back_to_main_menu')),
                ])
                await state_dispenser.delete(message.peer_id)
                await self.send_message(message, MessageConfig.FOUND_NOTHING, keyboard)
                return

            await state_dispenser.set(
                message.peer_id,
                SearchStates.VIEWING,
                search_results=[case.id for case in results],
                search_query=query,
            )

            keyboard = SearchCasesListKeyboard(results).get_markup()
            keyboard = BaseInlineKeyboard.append_buttons(keyboard, [
                (ButtonConfig.BACK_TO_SEARCH, make_payload('back_to_search')),
                (ButtonConfig.MAIN_MENU, make_payload('back_to_main_menu')),
            ])

            await self.send_message(
                message,
                f'🔎 Найдено кейсов: {len(results)}\n\nВыберите подходящий:',
                keyboard,
            )

        @self.labeler.raw_event(
            GroupEventType.MESSAGE_EVENT,
            MessageEvent,
            action_rule('case_search'),
        )
        async def view_case_from_search(
            event: MessageEvent,
            session: AsyncSession,
            state_dispenser,
        ):
            case_id = event.payload['id']
            state_peer = await state_dispenser.get(event.peer_id)
            case_ids = state_peer.payload.get('search_results', []) if state_peer else []
            query = state_peer.payload.get('search_query', '') if state_peer else ''

            case_service = CaseService(session)
            case, documents = await case_service.get_case_with_documents(case_id)
            text = await case_service.format_case_text(case)

            keyboard = CaseDetailKeyboard(documents, case.id).get_markup()
            keyboard = BaseInlineKeyboard.append_buttons(keyboard, [
                (ButtonConfig.BACK_TO_SEARCH_RESULTS, make_payload('back_to_search_results')),
                (ButtonConfig.MAIN_MENU, make_payload('back_to_main_menu')),
            ])

            await state_dispenser.set(
                event.peer_id,
                SearchStates.VIEWING,
                search_results=case_ids,
                search_query=query,
            )

            await event.send_empty_answer()
            await event.edit_message(text, keyboard=keyboard)

        @self.labeler.raw_event(
            GroupEventType.MESSAGE_EVENT,
            MessageEvent,
            action_rule('back_to_search_results'),
        )
        async def back_to_search_results(
            event: MessageEvent,
            session: AsyncSession,
            state_dispenser,
        ):
            state_peer = await state_dispenser.get(event.peer_id)
            case_ids = state_peer.payload.get('search_results', []) if state_peer else []
            query = state_peer.payload.get('search_query', '') if state_peer else ''

            if not case_ids:
                await back_to_search(event, state_dispenser)
                return

            case_service = CaseService(session)
            cases = []
            for cid in case_ids:
                case = await case_service.case_crud.get_by_id(cid)
                if case:
                    cases.append(case)

            keyboard = SearchCasesListKeyboard(cases).get_markup()
            keyboard = BaseInlineKeyboard.append_buttons(keyboard, [
                (ButtonConfig.BACK_TO_SEARCH, make_payload('back_to_search')),
                (ButtonConfig.MAIN_MENU, make_payload('back_to_main_menu')),
            ])

            await event.send_empty_answer()
            await event.edit_message(
                f'🔎 Результаты поиска по запросу "{query}":\n\n'
                f'Найдено кейсов: {len(cases)}\n\nВыберите подходящий:',
                keyboard=keyboard,
            )

        @self.labeler.raw_event(
            GroupEventType.MESSAGE_EVENT,
            MessageEvent,
            action_rule('back_to_search'),
        )
        async def back_to_search(event: MessageEvent, state_dispenser):
            await state_dispenser.set(event.peer_id, SearchStates.WAITING)

            keyboard = BaseInlineKeyboard()._build_inline_markup([
                (ButtonConfig.MAIN_MENU, make_payload('back_to_main_menu')),
            ])

            await event.send_empty_answer()
            await event.edit_message(
                MessageConfig.INSTRUCTIONS_FOR_SEARCH,
                keyboard=keyboard,
            )


search_handler = SearchHandler()
search_router = search_handler.labeler
