from sqlalchemy.ext.asyncio import AsyncSession
from vkbottle import ABCAPI

from config import LogConfig, MessageConfig, VkEnvConfig
from database.crud import VKFeedbackCRUD
from database.models import VKFeedback, VKUser
from logger import bot_logger
from vk_bot.services.base import BaseService
from vk_bot.support.dispatch import VkDispatchSupport


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
        peer_id = VkEnvConfig.get_admin_peer_id()
        if peer_id is None:
            bot_logger.warning(LogConfig.VK_ADMIN_PEER_NOT_SET)
            return

        try:
            await api.messages.send(
                peer_ids=[peer_id],
                message=MessageConfig.ADMIN_FEEDBACK_VK.format(
                    user_id=user.id,
                    text=feedback_text,
                ),
                random_id=VkDispatchSupport.random_id(),
            )
        except Exception:
            bot_logger.exception(LogConfig.VK_ADMIN_NOTIFY_FAILED)
