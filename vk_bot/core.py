import asyncio
import os

from dotenv import load_dotenv
from vkbottle import Bot

from config import DBConfig
from database.base import init_connection
from logger import bot_logger
from vk_bot.middleware.user import make_bot_middleware, make_user_middleware


class BotCore:
    """
    Основной класс ядра VK-бота.

    Отвечает за инициализацию бота, подключение к БД и регистрацию хендлеров.
    """

    def __init__(self) -> None:
        load_dotenv()

        self.vk_token = os.getenv('VK_BOT_TOKEN')
        if not self.vk_token:
            raise ValueError('VK_BOT_TOKEN не найден в .env')

        self.bot = Bot(token=self.vk_token)
        self.db = None
        self._handlers_registered = False
        self._middlewares_registered = False

        bot_logger.info('Ядро VK-бота инициализировано')

    def register_handlers(self, router) -> None:
        """Регистрирует роутер в боте."""
        self.bot.labeler.load(router)
        self._handlers_registered = True
        bot_logger.info(f'Загружен роутер: {router}')

    def register_middlewares(self) -> None:
        """Регистрирует middleware для message и callback событий."""
        if self._middlewares_registered or not self.db:
            return

        user_middleware = make_user_middleware(self.db.session_maker, self.bot)
        bot_middleware = make_bot_middleware(self.bot)

        self.bot.labeler.message_view.register_middleware(user_middleware)
        self.bot.labeler.message_view.register_middleware(bot_middleware)
        self.bot.labeler.raw_event_view.register_middleware(user_middleware)
        self.bot.labeler.raw_event_view.register_middleware(bot_middleware)

        self._middlewares_registered = True
        bot_logger.info('Middleware VK-бота зарегистрированы')

    async def init_database(self) -> None:
        """Инициализирует подключение к базе данных."""
        bot_logger.info('Подключение к базе данных...')
        self.db = await init_connection(DBConfig())
        bot_logger.info('База данных подключена')

    async def start(self) -> None:
        """Запускает бота."""
        if not self._handlers_registered:
            raise RuntimeError(
                'Обработчики не зарегистрированы. '
                'Вызовите register_handlers() перед запуском.'
            )

        await self.init_database()
        self.register_middlewares()

        bot_logger.info('Запуск VK-бота')

        # vkbottle: внутри asyncio.run() loop уже запущен — иначе run_polling() падает
        self.bot.loop_wrapper.loop = asyncio.get_running_loop()
        self.bot.loop_wrapper._running = True
        await self.bot.run_polling()

    async def stop(self) -> None:
        """Корректная остановка бота."""
        bot_logger.info('Остановка VK-бота')

        if self.db and self.db.engine:
            await self.db.engine.dispose()
            bot_logger.info('Соединения с БД закрыты')
