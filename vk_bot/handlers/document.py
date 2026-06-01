from vkbottle import GroupEventType
from vkbottle.bot import BotLabeler, MessageEvent
from sqlalchemy.ext.asyncio import AsyncSession

from config import CallbackAction, MessageConfig
from vk_bot.handlers.base import BaseHandlers
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
            session: AsyncSession,
            bot,
        ):
            doc_id = event.payload['id']
            service = DocumentService(session)
            document = await service.crud.get_by_id(doc_id)

            if not document or not document.vk_attachment:
                await event.show_snackbar(MessageConfig.NO_FIND_FILE)
                return

            await self.safe_answer_event(event)
            await service.send_document(bot.api, event.peer_id, document)


document_handler = DocumentHandler()
document_router = document_handler.labeler
