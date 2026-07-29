from vkbottle import GroupEventType
from vkbottle.bot import BotLabeler, MessageEvent

from bot_client import BackendClient, BackendError
from config import ButtonConfig, CallbackAction, MessageConfig
from logger import bot_logger
from vk_bot.handlers.base import BaseHandlers
from vk_bot.keyboards.base import BaseInlineKeyboard
from vk_bot.keyboards.case import CaseDetailKeyboard
from vk_bot.services.document import DocumentService
from vk_bot.support.dispatch import VkDispatchSupport


class DocumentHandler(BaseHandlers):
    """Обработчик отправки документов."""

    def __init__(self):
        self.labeler = BotLabeler()
        self._register()

    def _register(self) -> None:
        @self.labeler.raw_event(
            GroupEventType.MESSAGE_EVENT,
            MessageEvent,
            VkDispatchSupport.action_rule(CallbackAction.DOCUMENT),
        )
        async def send_document(
            event: MessageEvent,
            session: BackendClient,
        ):
            doc_id = event.payload['id']

            service = DocumentService(session)
            document = await service.crud.get_by_id(doc_id)

            if not document:
                await event.show_snackbar(MessageConfig.NO_FIND_FILE)
                return

            await self.safe_answer_event(event)

            try:
                await service.send_document(event.ctx_api, event.peer_id, document)
            except (BackendError, ValueError):
                bot_logger.exception('Не удалось получить документ через backend')
                await event.show_snackbar(MessageConfig.NO_FIND_FILE)
                return

            await self.safe_delete_event_message(event)

            origin = event.payload.get('origin', 'all')
            keyboard = BaseInlineKeyboard.build_inline_markup([
                (
                    ButtonConfig.BACK_TO_CASE,
                    BaseInlineKeyboard.make_payload(
                        CallbackAction.BACK_TO_CASE,
                        case_id=document.case_id,
                        origin=origin,
                    ),
                ),
                (
                    ButtonConfig.MAIN_MENU,
                    BaseInlineKeyboard.make_payload(
                        CallbackAction.BACK_TO_MAIN_MENU
                    ),
                ),
            ])
            await event.ctx_api.messages.send(
                peer_id=event.peer_id,
                message='📄 Выберите действие:',
                keyboard=keyboard,
                random_id=VkDispatchSupport.random_id(),
            )

        @self.labeler.raw_event(
            GroupEventType.MESSAGE_EVENT,
            MessageEvent,
            VkDispatchSupport.action_rule(CallbackAction.BACK_TO_CASE),
        )
        async def back_to_case(
            event: MessageEvent,
            session: BackendClient,
        ):
            await self.show_parent_case(event, session)

    async def show_parent_case(
        self,
        event: MessageEvent,
        session: BackendClient,
    ) -> None:
        """Возвращает от документа к кейсу с исходной навигацией."""

        case_id = event.payload['case_id']
        origin = event.payload.get('origin', 'all')

        try:
            case = await session.get_case(case_id)
        except BackendError:
            bot_logger.exception(
                'Не удалось вернуться к кейсу через backend'
            )
            await event.show_snackbar(MessageConfig.NO_FIND_CASES)
            return

        keyboard = CaseDetailKeyboard(
            case.documents,
            case.id,
            origin=origin,
        ).get_markup()
        keyboard = BaseInlineKeyboard.append_buttons(
            keyboard,
            [
                *self._origin_buttons(origin),
                (
                    ButtonConfig.MAIN_MENU,
                    BaseInlineKeyboard.make_payload(
                        CallbackAction.BACK_TO_MAIN_MENU
                    ),
                ),
            ],
        )

        await self.safe_answer_event(event)
        await self.safe_delete_event_message(event)
        if (
            event.conversation_message_id
            and event.conversation_message_id > 1
        ):
            await self._delete_by_cmid(
                event.ctx_api,
                event.peer_id,
                event.conversation_message_id - 1,
            )

        await event.ctx_api.messages.send(
            peer_id=event.peer_id,
            message=f'{case.title}\n\n{case.solution}',
            keyboard=keyboard,
            random_id=VkDispatchSupport.random_id(),
        )

    @staticmethod
    def _origin_buttons(origin: str) -> list[tuple[str, dict]]:
        """Возвращает кнопки перехода на исходный экран."""

        if origin == 'search':
            return [(
                ButtonConfig.BACK_TO_SEARCH_RESULTS,
                BaseInlineKeyboard.make_payload(
                    CallbackAction.BACK_TO_SEARCH_RESULTS
                ),
            )]

        if origin.startswith('cat-'):
            category_id = int(origin.removeprefix('cat-'))
            return [
                (
                    ButtonConfig.BACK_TO_CASES,
                    BaseInlineKeyboard.make_payload(
                        CallbackAction.BACK_TO_CASES_FROM_CAT,
                        category_id=category_id,
                    ),
                ),
                (
                    ButtonConfig.BACK_TO_CATEGORIES,
                    BaseInlineKeyboard.make_payload(
                        CallbackAction.BACK_TO_CATEGORIES
                    ),
                ),
            ]

        return [(
            ButtonConfig.BACK_TO_CASES,
            BaseInlineKeyboard.make_payload(
                CallbackAction.BACK_TO_CASES
            ),
        )]


document_handler = DocumentHandler()
document_router = document_handler.labeler
