from vkbottle import BaseStateGroup, GroupEventType
from vkbottle.bot import BotLabeler, Message, MessageEvent

from bot_client import BackendClient
from config import ButtonConfig, CallbackAction, MenuConfig, MessageConfig
from vk_bot.handlers.base import BaseHandlers
from vk_bot.keyboards.base import BaseInlineKeyboard
from vk_bot.keyboards.case import CaseDetailKeyboard
from vk_bot.keyboards.search import SearchCasesListKeyboard
from vk_bot.services.case import CaseService
from vk_bot.services.search import SearchService
from vk_bot.support.dispatch import VkDispatchSupport


class SearchStates(BaseStateGroup):
    WAITING = 'waiting_for_query'
    VIEWING = 'viewing_results'


class SearchHandler(BaseHandlers):
    """Обработчик поиска."""

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
        @self.labeler.private_message(text=ButtonConfig.SEARCH)
        async def start_search(message: Message, state_dispenser):
            state_peer = await state_dispenser.get(message.peer_id)
            if state_peer and state_peer.state == SearchStates.WAITING:
                return

            await self.cleanup_current_and_previous(message)

            keyboard = BaseInlineKeyboard.build_inline_markup([self._main_menu_button()])
            search_msg = await self.send_inline_message(
                message,
                MessageConfig.INSTRUCTIONS_FOR_SEARCH,
                keyboard,
            )
            await state_dispenser.set(
                message.peer_id,
                SearchStates.WAITING,
                search_msg_id=VkDispatchSupport.sent_message_cmid(search_msg),
            )

        @self.labeler.private_message(state=SearchStates.WAITING)
        async def perform_search(message: Message, session: BackendClient, state_dispenser):
            query = message.text.strip()

            if query in MenuConfig.MAIN_MENU_BUTTONS:
                await VkDispatchSupport.safe_delete_state(state_dispenser, message.peer_id)
                if message.conversation_message_id:
                    await self.safe_delete_message(message, message.conversation_message_id)
                return

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
                keyboard = BaseInlineKeyboard.build_inline_markup([
                    (ButtonConfig.BACK_TO_SEARCH, BaseInlineKeyboard.make_payload(CallbackAction.BACK_TO_SEARCH)),
                    self._main_menu_button(),
                ])
                await VkDispatchSupport.safe_delete_state(state_dispenser, message.peer_id)
                await self.send_inline_message(message, MessageConfig.FOUND_NOTHING, keyboard)
                return

            await state_dispenser.set(
                message.peer_id,
                SearchStates.VIEWING,
                search_results=[case.id for case in results],
                search_query=query,
                search_page=0,
            )

            keyboard = SearchCasesListKeyboard(results, page=0).get_markup()
            keyboard = BaseInlineKeyboard.append_buttons(keyboard, [
                (ButtonConfig.BACK_TO_SEARCH, BaseInlineKeyboard.make_payload(CallbackAction.BACK_TO_SEARCH)),
                self._main_menu_button(),
            ])

            await self.send_inline_message(
                message,
                MessageConfig.SEARCH_FOUND.format(count=len(results)),
                keyboard,
            )

        @self.labeler.raw_event(
            GroupEventType.MESSAGE_EVENT,
            MessageEvent,
            VkDispatchSupport.action_rule('search_page'),
        )
        async def paginate_search(event: MessageEvent, session: BackendClient, state_dispenser):
            page = event.payload['page']
            state_peer = await state_dispenser.get(event.peer_id)
            case_ids = state_peer.payload.get('search_results', []) if state_peer else []

            cases = await self._get_cases_by_ids(session, case_ids)

            await state_dispenser.set(
                event.peer_id,
                SearchStates.VIEWING,
                search_results=case_ids,
                search_query=state_peer.payload.get('search_query', ''),
                search_page=page,
            )

            keyboard = SearchCasesListKeyboard(cases, page=page).get_markup()
            keyboard = BaseInlineKeyboard.append_buttons(keyboard, [
                (ButtonConfig.BACK_TO_SEARCH, BaseInlineKeyboard.make_payload(CallbackAction.BACK_TO_SEARCH)),
                self._main_menu_button(),
            ])

            await self.safe_answer_event(event)
            await event.edit_message(
                MessageConfig.SEARCH_FOUND.format(count=len(cases)),
                keyboard=keyboard,
            )

        @self.labeler.raw_event(
            GroupEventType.MESSAGE_EVENT,
            MessageEvent,
            VkDispatchSupport.action_rule(CallbackAction.CASE_SEARCH),
        )
        async def view_case_from_search(event: MessageEvent, session: BackendClient, state_dispenser):
            case_id = event.payload['id']
            state_peer = await state_dispenser.get(event.peer_id)
            case_ids = state_peer.payload.get('search_results', []) if state_peer else []
            query = state_peer.payload.get('search_query', '') if state_peer else ''
            page = state_peer.payload.get('search_page', 0) if state_peer else 0

            case_service = CaseService(session)
            case, documents = await case_service.get_case_with_documents(case_id)
            text = await case_service.format_case_text(case)

            keyboard = CaseDetailKeyboard(
                documents,
                case.id,
                origin='search',
            ).get_markup()
            keyboard = BaseInlineKeyboard.append_buttons(keyboard, [
                (ButtonConfig.BACK_TO_SEARCH_RESULTS, BaseInlineKeyboard.make_payload(CallbackAction.BACK_TO_SEARCH_RESULTS)),
                self._main_menu_button(),
            ])

            await state_dispenser.set(
                event.peer_id,
                SearchStates.VIEWING,
                search_results=case_ids,
                search_query=query,
                search_page=page,
            )

            await self.safe_answer_event(event)
            await event.edit_message(text, keyboard=keyboard)

        @self.labeler.raw_event(
            GroupEventType.MESSAGE_EVENT,
            MessageEvent,
            VkDispatchSupport.action_rule(CallbackAction.BACK_TO_SEARCH_RESULTS),
        )
        async def back_to_search_results(event: MessageEvent, session: BackendClient, state_dispenser):
            state_peer = await state_dispenser.get(event.peer_id)
            case_ids = state_peer.payload.get('search_results', []) if state_peer else []
            query = state_peer.payload.get('search_query', '') if state_peer else ''
            page = state_peer.payload.get('search_page', 0) if state_peer else 0

            if not case_ids:
                await back_to_search(event, state_dispenser)
                return

            cases = await self._get_cases_by_ids(session, case_ids)

            keyboard = SearchCasesListKeyboard(cases, page=page).get_markup()
            keyboard = BaseInlineKeyboard.append_buttons(keyboard, [
                (ButtonConfig.BACK_TO_SEARCH, BaseInlineKeyboard.make_payload(CallbackAction.BACK_TO_SEARCH)),
                self._main_menu_button(),
            ])

            await self.safe_answer_event(event)
            await event.edit_message(
                MessageConfig.SEARCH_RESULTS.format(query=query, count=len(cases)),
                keyboard=keyboard,
            )

        @self.labeler.raw_event(
            GroupEventType.MESSAGE_EVENT,
            MessageEvent,
            VkDispatchSupport.action_rule(CallbackAction.BACK_TO_SEARCH),
        )
        async def back_to_search(event: MessageEvent, state_dispenser):
            keyboard = BaseInlineKeyboard.build_inline_markup([self._main_menu_button()])

            await self.safe_answer_event(event)
            await event.edit_message(
                MessageConfig.INSTRUCTIONS_FOR_SEARCH,
                keyboard=keyboard,
            )
            await state_dispenser.set(
                event.peer_id,
                SearchStates.WAITING,
                search_msg_id=event.conversation_message_id,
            )

    @staticmethod
    async def _get_cases_by_ids(
        session: BackendClient,
        case_ids: list[int],
    ) -> list:
        """Восстанавливает сохранённую выдачу через центральный backend."""

        available_cases = {
            case.id: case
            for case in await CaseService(session).get_all_cases()
        }
        return [
            available_cases[case_id]
            for case_id in case_ids
            if case_id in available_cases
        ]


search_handler = SearchHandler()
search_router = search_handler.labeler
