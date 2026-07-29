"""Обратная связь Telegram через backend."""

from tg_bot.services.base import BaseService


class FeedbackService(BaseService):
    """Сервис обратной связи."""

    async def save_feedback(self, user_id: int, message: str) -> None:
        await self.session.create_feedback(user_id, message)
