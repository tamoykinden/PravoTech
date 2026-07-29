from vkbottle import BaseStateGroup
from vkbottle.bot import BotLabeler, Message

from backend.schemas import UserRead
from bot_client import BackendClient
from config import ButtonConfig, CallbackAction, MenuConfig, MessageConfig
from vk_bot.handlers.base import BaseHandlers
from vk_bot.keyboards.base import BaseInlineKeyboard
from vk_bot.keyboards.main_menu import MainMenuKeyboard
from vk_bot.services.feedback import FeedbackService
from vk_bot.support.dispatch import VkDispatchSupport


class FeedbackStates(BaseStateGroup):
    WAITING = 'waiting_for_message'


class FeedbackHandler(BaseHandlers):
    """Обработчик обратной связи."""

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
        @self.labeler.private_message(text=ButtonConfig.FEEDBACK)
        async def start_feedback(message: Message, state_dispenser):
            state_peer = await state_dispenser.get(message.peer_id)
            if state_peer and state_peer.state == FeedbackStates.WAITING:
                return

            await self.cleanup_current_and_previous(message)

            keyboard = BaseInlineKeyboard.build_inline_markup([self._main_menu_button()])
            prompt_msg = await self.send_inline_message(
                message,
                MessageConfig.FEEDBACK,
                keyboard,
            )
            await state_dispenser.set(
                message.peer_id,
                FeedbackStates.WAITING,
                prompt_msg_id=VkDispatchSupport.sent_message_cmid(prompt_msg),
            )

        @self.labeler.private_message(state=FeedbackStates.WAITING)
        async def save_feedback(
            message: Message,
            session: BackendClient,
            user: UserRead,
            state_dispenser,
            bot,
        ):
            feedback_text = message.text.strip()

            if feedback_text in MenuConfig.MAIN_MENU_BUTTONS:
                await VkDispatchSupport.safe_delete_state(state_dispenser, message.peer_id)
                if message.conversation_message_id:
                    await self.safe_delete_message(message, message.conversation_message_id)
                return

            state_peer = await state_dispenser.get(message.peer_id)
            prompt_msg_id = state_peer.payload.get('prompt_msg_id') if state_peer else None

            if prompt_msg_id:
                await self.safe_delete_message(message, prompt_msg_id)

            if len(feedback_text) < 5:
                keyboard = BaseInlineKeyboard.build_inline_markup([self._main_menu_button()])
                await self.send_inline_message(message, MessageConfig.PLEASE_FOR_FEEDBACK, keyboard)
                return

            service = FeedbackService(session)
            await service.save_feedback(user.id, feedback_text)
            await service.notify_admin(bot.api, user, feedback_text)

            await VkDispatchSupport.safe_delete_state(state_dispenser, message.peer_id)
            await self.send_message(
                message,
                MessageConfig.THANKS_FOR_FEEDBACK,
                MainMenuKeyboard().get_markup(),
            )


feedback_handler = FeedbackHandler()
feedback_router = feedback_handler.labeler
