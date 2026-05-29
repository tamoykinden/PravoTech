from config import MessageConfig
from vk_bot.handlers.base import BaseHandler
from vk_bot.keyboards.main_menu import MainMenuKeyboard


class CommonHandler(BaseHandler):
    """Обработчик общих команд."""

    def send_message(self, user_id: int, text: str, keyboard=None) -> None:
        """Отправляет сообщение."""

        self.bot.vk.messages.send(
            user_id=user_id,
            message=text,
            random_id=0,
            keyboard=keyboard
        )

    def handle(self, event) -> None:
        """Обрабатывает сообщение."""

        user_id = event.obj.message['from_id']
        text = event.obj.message.get('text', '')

        if text in ['Начать', 'Старт', '/start']:
            self.send_message(
                user_id,
                MessageConfig.START,
                MainMenuKeyboard().get_markup()
            )
        elif text in ['Помощь', '/help']:
            self.send_message(user_id, MessageConfig.HELP)
        else:
            self.send_message(user_id, 'Неизвестная команда. Напишите "Начать"')
