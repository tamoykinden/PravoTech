from vkbottle import ABCAPI

from backend.schemas import UserRead
from config import LogConfig, MessageConfig, VkEnvConfig
from logger import bot_logger
from vk_bot.services.base import BaseService
from vk_bot.support.dispatch import VkDispatchSupport


class FeedbackService(BaseService):
    """Сервис для обратной связи VK."""

    async def save_feedback(self, user_id: int, message: str) -> None:
        await self.session.create_feedback(user_id, message)

    async def notify_admin(
        self,
        api: ABCAPI,
        user: UserRead,
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
