import asyncio
import os

from dotenv import load_dotenv
from vkbottle import Bot

from bot_client import BackendClient
from logger import bot_logger
from vk_bot.middleware.user import BotMiddleware, UserMiddleware


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
        self.backend = BackendClient('vk')
        self._handlers_registered = False
        self._middlewares_registered = False

        bot_logger.info('Ядро VK-бота инициализировано')

    def register_handlers(self, router) -> None:
        """Регистрирует роутер в боте."""
        if not hasattr(self, '_loaded_routers'):
            self._loaded_routers = set()

        router_id = id(router)
        if router_id in self._loaded_routers:
            bot_logger.warning(f'Роутер уже загружен, пропуск: {router}')
            return

        self.bot.labeler.load(router)
        self._loaded_routers.add(router_id)
        self._handlers_registered = True
        bot_logger.info(f'Загружен роутер: {router}')

    def register_middlewares(self) -> None:
        """Регистрирует middleware для message и callback событий."""
        if self._middlewares_registered:
            return

        UserMiddleware.configure(self.backend, self.bot)
        BotMiddleware.configure(self.bot)

        self.bot.labeler.message_view.register_middleware(UserMiddleware)
        self.bot.labeler.message_view.register_middleware(BotMiddleware)
        self.bot.labeler.raw_event_view.register_middleware(UserMiddleware)
        self.bot.labeler.raw_event_view.register_middleware(BotMiddleware)

        self._middlewares_registered = True
        bot_logger.info('Middleware VK-бота зарегистрированы')

    async def start(self) -> None:
        """Запускает бота."""
        if not self._handlers_registered:
            raise RuntimeError(
                'Обработчики не зарегистрированы. '
                'Вызовите register_handlers() перед запуском.'
            )

        await self.backend.healthcheck()
        self.register_middlewares()

        bot_logger.info('Запуск VK-бота')

        # vkbottle: внутри asyncio.run() loop уже запущен — иначе run_polling() падает
        self.bot.loop_wrapper.loop = asyncio.get_running_loop()
        self.bot.loop_wrapper._running = True
        await self.bot.run_polling()

    async def stop(self) -> None:
        """Корректная остановка бота."""
        bot_logger.info('Остановка VK-бота')

        await self.backend.close()
