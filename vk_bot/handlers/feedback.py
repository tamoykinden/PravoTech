from vkbottle import BaseStateGroup
from vkbottle.bot import BotLabeler, Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import ButtonConfig, MessageConfig
from database.models import VKUser
from vk_bot.handlers.base import BaseHandlers
from vk_bot.keyboards.base import BaseInlineKeyboard, make_payload
from vk_bot.keyboards.main_menu import MainMenuKeyboard
from vk_bot.services.feedback import FeedbackService


class FeedbackStates(BaseStateGroup):
    WAITING = 'waiting_for_message'


class FeedbackHandler(BaseHandlers):
    """Обработчик обратной связи."""

    def __init__(self):
        self.labeler = BotLabeler()
        self._register()

    def _register(self) -> None:
        @self.labeler.private_message(text=ButtonConfig.FEEDBACK)
        async def start_feedback(message: Message, state_dispenser):
            await state_dispenser.set(message.peer_id, FeedbackStates.WAITING)

            await self.cleanup_current_and_previous(message)

            keyboard = BaseInlineKeyboard()._build_inline_markup([
                (ButtonConfig.MAIN_MENU, make_payload('back_to_main_menu')),
            ])
            prompt_msg = await self.send_message(
                message,
                MessageConfig.FEEDBACK,
                keyboard,
            )
            await state_dispenser.set(
                message.peer_id,
                FeedbackStates.WAITING,
                prompt_msg_id=prompt_msg.conversation_message_id,
            )

        @self.labeler.private_message(state=FeedbackStates.WAITING)
        async def save_feedback(
            message: Message,
            session: AsyncSession,
            user: VKUser,
            state_dispenser,
            bot,
        ):
            feedback_text = message.text.strip()

            state_peer = await state_dispenser.get(message.peer_id)
            prompt_msg_id = state_peer.payload.get('prompt_msg_id') if state_peer else None

            if prompt_msg_id:
                await self.safe_delete_message(message, prompt_msg_id)

            if len(feedback_text) < 5:
                keyboard = BaseInlineKeyboard()._build_inline_markup([
                    (ButtonConfig.MAIN_MENU, make_payload('back_to_main_menu')),
                ])
                await self.send_message(message, MessageConfig.PLEASE_FOR_FEEDBACK, keyboard)
                return

            service = FeedbackService(session)
            await service.save_feedback(user.id, feedback_text)
            await service.notify_admin(bot.api, user, feedback_text)

            await state_dispenser.delete(message.peer_id)
            await self.send_message(
                message,
                MessageConfig.THANKS_FOR_FEEDBACK,
                MainMenuKeyboard().get_markup(),
            )


feedback_handler = FeedbackHandler()
feedback_router = feedback_handler.labeler
