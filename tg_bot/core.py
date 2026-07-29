import os
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from dotenv import load_dotenv

from bot_client import BackendClient
from logger import bot_logger
from tg_bot.middleware.pd_agreement import PDAgreementMiddleware
from tg_bot.middleware.user import UserMiddleware


class BotCore:
    """
    Основной класс для Telegram-бота ПравоТека.

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
        self.tg_proxy_url: Optional[str] = (os.getenv('TG_PROXY_URL') or '').strip() or None

        if not self.tg_bot_token:
            raise ValueError('TG_BOT_TOKEN не найден в .env')

        if self.tg_proxy_url:
            bot_logger.info('Telegram: используется прокси')
        else:
            bot_logger.info('Telegram: прямое подключение (без прокси)')

        session = AiohttpSession(proxy=self.tg_proxy_url) if self.tg_proxy_url else None
        self.bot: Bot = Bot(
            token=self.tg_bot_token,
            session=session,
            default=DefaultBotProperties(parse_mode='HTML')
        )
        self.dp: Dispatcher = Dispatcher()
        self.backend = BackendClient('telegram')
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

        await self.backend.healthcheck()
        user_middleware = UserMiddleware(self.backend)
        pd_middleware = PDAgreementMiddleware()

        self.dp.message.middleware(user_middleware)
        self.dp.message.middleware(pd_middleware)
        self.dp.callback_query.middleware(user_middleware)
        self.dp.callback_query.middleware(pd_middleware)

        bot_logger.info('Запуск бота')
        try:
            await self.bot.delete_webhook(drop_pending_updates=True)
        except Exception as e:
            if self.tg_proxy_url:
                raise RuntimeError(
                    'Не удалось подключиться к Telegram через прокси. '
                    'Проверьте TG_PROXY_URL или уберите его из .env для прямого подключения.'
                ) from e
            raise
        await self.dp.start_polling(self.bot)

    async def stop(self):
        """
        Корректная остановка бота.

        Закрывает сессию бота для избежания memory leaks.
        """

        bot_logger.info('Остановка бота')

        await self.backend.close()
        await self.bot.session.close()
