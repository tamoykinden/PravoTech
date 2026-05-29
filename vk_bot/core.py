import os

from dotenv import load_dotenv
from vk_api import VkApi
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll

from config import DBConfig
from database.base import init_connection
from logger import bot_logger
from vk_bot.handlers.common import CommonHandler


class BotCore:
    """Основной класс VK-бота."""

    def __init__(self) -> None:
        load_dotenv()

        self.vk_token = os.getenv('VK_BOT_TOKEN')
        self.group_id = os.getenv('VK_GROUP_ID')

        if not self.vk_token or not self.group_id:
            raise ValueError('VK_BOT_TOKEN или VK_GROUP_ID не найдены в .env')

        self.vk_session = VkApi(token=self.vk_token)
        self.vk = self.vk_session.get_api()
        self.longpoll = VkBotLongPoll(self.vk_session, int(self.group_id))
        self.db = None

        self._init_db()
        self._setup_handlers()

        bot_logger.info('Ядро VK-бота инициализировано')

    def _init_db(self) -> None:
        bot_logger.info('Подключение к базе данных...')
        self.db = init_connection(DBConfig())
        bot_logger.info('База данных подключена')

    def _setup_handlers(self) -> None:
        """Регистрация обработчиков."""

        self.common_handler = CommonHandler(self)

    def start(self) -> None:
        bot_logger.info('Запуск VK-бота')

        for event in self.longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                self.common_handler.handle(event)
