import os
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from dotenv import load_dotenv

from config import DBConfig
from database.base import Database, init_connection
from logger import bot_logger
from tg_bot.middleware.user import UserMiddleware


class BotCore:
    """
    Основной класс для Telegram-бота для курсов 3D-печати.

    Этот класс инкапсулирует всю базовую логику инициализации и работы бота.
    Используется как точка входа для настройки и запуска.

    Атрибуты:
        bot (Bot): Экземпляр Telegram бота
        dp (Dispatcher): Диспетчер для обработки сообщений
        bot_token (str): Токен бота из .env файла
        _handlers_registered (bool): Флаг, указывающий зарегистрированы ли обработчики
    """

    def __init__(self):
        """
        Инициализация ядра бота.

        Выполняет:
        1. Загрузку токена из .env файла
        2. Создание экземпляра Bot с настройками по умолчанию
        3. Создание экземпляра Dispatcher

        Исключения:
            ValueError: Если TG_BOT_TOKEN не найден в .env файле
        """

        load_dotenv()

        self.tg_bot_token: Optional[str] = os.getenv('TG_BOT_TOKEN')
        self.tg_proxy_url: Optional[str] = os.getenv('TG_PROXY_URL')

        if not self.tg_bot_token:
            raise ValueError('TG_BOT_TOKEN не найден в .env')

        session = AiohttpSession(proxy=self.tg_proxy_url) if self.tg_proxy_url else None
        self.bot: Bot = Bot(
            token=self.tg_bot_token,
            session=session,
            default=DefaultBotProperties(parse_mode='HTML')
        )
        self.dp: Dispatcher = Dispatcher()
        self.db: Optional[Database] = None
        self._handlers_registered: bool = False

        bot_logger.info('Ядро бота инициализировано')

    def register_handlers(self, router):
        """
        Регистрация обработчиков команд в диспетчере.

        Args:
            router: Роутер с обработчиками команд

        Этот метод должен быть вызван перед запуском бота.
        Устанавливает флаг _handlers_registered в True.
        """

        self.dp.include_router(router)
        self._handlers_registered = True

    async def init_database(self):
        """
        Инициализация подключения к базе данных.

        Создает пул соединений с PostgreSQL и проверяет доступность БД.
        Должна вызываться перед запуском бота.
        """

        bot_logger.info('Подключение к базе данных...')

        self.db = await init_connection(DBConfig())

        bot_logger.info('База данных подключена')

    async def start(self):
        """
        Запуск бота в режиме long-polling.

        Выполняет:
        1. Проверку регистрации обработчиков
        2. Удаление вебхука (если был)
        3. Запуск опроса серверов Telegram

        Исключения:
            RuntimeError: Если обработчики не зарегистрированы
        """

        if not self._handlers_registered:
            raise RuntimeError('Обработчики не зарегистрированы. Вызовите register_handlers() перед запуском.')

        await self.init_database()

        self.dp.message.middleware(UserMiddleware(self.db.session_maker))
        self.dp.callback_query.middleware(UserMiddleware(self.db.session_maker))

        bot_logger.info('Запуск бота')
        await self.bot.delete_webhook(drop_pending_updates=True)
        await self.dp.start_polling(self.bot)

    async def stop(self):
        """
        Корректная остановка бота.

        Закрывает сессию бота для избежания memory leaks.
        """

        bot_logger.info('Остановка бота')

        if self.db and self.db.engine:
            await self.db.engine.dispose()
            bot_logger.info('Соединения с БД закрыты')

        await self.bot.session.close()
