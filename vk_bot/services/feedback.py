import os

from sqlalchemy.ext.asyncio import AsyncSession
from vkbottle import ABCAPI

from database.crud import VKFeedbackCRUD
from database.models import VKFeedback, VKUser
from logger import bot_logger
from vk_bot.handlers.helpers import random_id
from vk_bot.services.base import BaseService


def get_admin_peer_id() -> int | None:
    """
    Peer ID чата/пользователя для уведомлений администратора в VK.

    Для личных сообщений — id пользователя.
    Для беседы — 2000000000 + local_chat_id.
    """
    peer_id = os.getenv('VK_ADMIN_PEER_ID') or os.getenv('VK_ADMIN_CHAT_ID')
    if not peer_id:
        return None
    return int(peer_id)


class FeedbackService(BaseService):
    """Сервис для обратной связи VK."""

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.crud = VKFeedbackCRUD(session)

    async def save_feedback(self, user_id: int, message: str) -> VKFeedback:
        return await self.crud.create(user_id=user_id, message=message)

    async def notify_admin(
        self,
        api: ABCAPI,
        user: VKUser,
        feedback_text: str,
    ) -> None:
        """Отправляет уведомление об обратной связи в админский peer VK."""

        peer_id = get_admin_peer_id()
        if peer_id is None:
            bot_logger.warning(
                'VK_ADMIN_PEER_ID не задан — уведомление об обратной связи не отправлено'
            )
            return

        try:
            await api.messages.send(
                peer_id=peer_id,
                message=(
                    f'📝 Новая обратная связь (VK)!\n\n'
                    f'👤 Пользователь: [user_{user.id}] (vk_id: {user.vk_id})\n'
                    f'💬 Сообщение:\n{feedback_text}'
                ),
                random_id=random_id(),
            )
        except Exception as e:
            bot_logger.error(f'Ошибка отправки обратной связи в админ-чат VK: {e}')
