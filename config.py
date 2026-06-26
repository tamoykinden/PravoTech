import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

class BaseConfig:
    """Базовые настройки проекта."""

    BASE_DIR = Path(__file__).parent
    LOGS_DIR = BASE_DIR / 'logs'

    @classmethod
    def ensure_dirs(cls):
        cls.LOGS_DIR.mkdir(exist_ok=True)

class DBConfig:
    """Настройки подключения к БД."""

    DB_NAME = os.getenv('DB_NAME')
    DB_USER = os.getenv(
        'DB_USER',
    )
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')

    @property
    def database_url(self) -> str:
        """Возвращает строку подключения к PostgreSQL."""

        return f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'


class MessageConfig:
    """Тексты сообщений бота."""

    START = (
        '👋 Привет! Я бот «ПравоТека».\n\n'
        'Я помогу вам найти пошаговые инструкции для решения типовых правовых ситуаций.\n\n'
        'Выберите действие в меню ниже:'
    )

    HELP = (
        'Справка\n\n'
        'Список кейсов — показать все доступные кейсы\n'
        'Поиск кейса — найти кейс по ключевым словам\n'
        'Категории — выбрать кейс по категории\n'
        'Обратная связь — отправить сообщение разработчикам\n\n'
        'Если у вас возникла ситуация, которой нет в боте — напишите в обратную связь, мы добавим ее.'
    )
    NO_CASES = 'Кейсы пока не добавлены.'
    NO_FIND_CASES = 'Кейс не найден.'
    NO_FIND_FILE = 'Файл не найден.'
    NO_CATEGORIES = 'Категории пока не добавлены.'
    NO_CASES_IN_CAT = 'В этой категории пока нет кейсов.'
    FEEDBACK = (
        'Напишите ваше сообщение или опишите ситуацию, которой нет в боте.'
        'Мы рассмотрим и добавим ее в ближайшее время.'
        'Чтобы отменить — нажмите "Назад".'
    )
    FEEDBACK_CANCEL = 'Обратная связь отменена.'
    PLEASE_FOR_FEEDBACK = 'Пожалуйста, напишите сообщение подробнее (минимум 5 символов).'
    THANKS_FOR_FEEDBACK = 'Спасибо за обратную связь! Мы обязательно рассмотрим ваше сообщение.'
    INSTRUCTIONS_FOR_SEARCH = (
        'Введите ключевые слова для поиска (через пробел):'
        'Например: <i>шум соседи</i> или <i>возврат товара</i>'
    )
    SEARCH_CANCELED = 'Поиск отменен.'
    TWO_SIMBOLS = 'Введите минимум 2 символа для поиска.'
    FOUND_NOTHING = (
        'Ничего не найдено.'
        'Попробуйте изменить запрос или обратитесь в обратную связь, '
        'если вашей ситуации нет в боте.'
    )
    MAIN_WORD = 'Введите ключевые слова для поиска (через пробел):'
    BACK_TO_MAIN_MENU = (
        '🏠 Добро пожаловать в главное меню!\n\n'
        'Выберите действие из списка ниже:'
    )
    PD_AGREEMENT_TEXT = (
        'Согласие на обработку персональных данных\n\n'
        'Для использования бота «ПравоТека» нам необходимо ваше согласие '
        'на обработку персональных данных.\n\n'
    'Данные используются только для:\n'
    '• идентификации пользователя\n'
    '• сбора статистики использования\n'
    '• обработки обратной связи\n\n'
    'Нажимая «Согласен», вы подтверждаете, что ознакомлены и согласны '
    'с обработкой ваших данных.\n\n'
    'Вы можете отозвать согласие в любой момент, написав нам.'
    )
    PD_DISAGREE_TEXT = (
        'Доступ ограничен\n'
        'К сожалению, мы не можем предоставить вам доступ к боту '
        'без согласия на обработку персональных данных.\n'
        'Если вы передумаете, нажмите кнопку «Войти в бота».'
    )

    SELECT_CASE = '📋 Выберите кейс:'
    SELECT_CATEGORY = '📂 Выберите категорию:'
    SELECT_CATEGORY_CASES = '📂 Категория: {name}\n\nВыберите кейс:'
    SEARCH_FOUND = '🔎 Найдено кейсов: {count}\n\nВыберите подходящий:'
    SEARCH_RESULTS = (
        '🔎 Результаты поиска по запросу "{query}":\n\n'
        'Найдено кейсов: {count}\n\nВыберите подходящий:'
    )
    DOCUMENT_TITLE = '📄 {title}'

    ADMIN_FEEDBACK_VK = (
        '📝 Новая обратная связь (VK)!\n\n'
        '👤 Пользователь: ID {user_id}\n'
        '💬 Сообщение:\n{text}'
    )


class ButtonConfig:
    """Текст кнопок."""

    BACK = 'Назад'
    CASES = 'Список кейсов'
    CATEGORIES = 'Категории'
    FEEDBACK = 'Обратная связь'
    SEARCH = 'Поиск кейса'
    BACK_TO_CASES = 'Назад к кейсам'
    BACK_TO_CATEGORIES = 'Назад к категориям'
    BACK_TO_SEARCH = 'Назад к поиску'
    MAIN_MENU = 'Главное меню'
    BACK_TO_SEARCH_RESULTS = 'Назад к результатам поиска'
    PD_RETRY_BUTTON = 'Войти в бота'
    PD_AGREE_BUTTON = 'Согласен'
    PD_DISAGREE_BUTTON = 'Не согласен'


class CallbackAction:
    """Идентификаторы action в payload inline-кнопок VK."""

    BACK_TO_MAIN_MENU = 'back_to_main_menu'
    BACK_TO_SEARCH = 'back_to_search'
    BACK_TO_SEARCH_RESULTS = 'back_to_search_results'
    BACK_TO_CASES = 'back_to_cases'
    BACK_TO_CASES_FROM_CAT = 'back_to_cases_from_cat'
    BACK_TO_CATEGORIES = 'back_to_categories'
    CASE_LIST = 'case_list'
    CASE_CAT = 'case_cat'
    CASE_SEARCH = 'case_search'
    CATEGORY = 'cat'
    DOCUMENT = 'doc'
    PD_AGREE = 'pd_agree'
    PD_DISAGREE = 'pd_disagree'
    PD_RETRY = 'pd_retry'


class MenuConfig:
    """Тексты команд и reply-кнопок главного меню."""

    START_TEXTS = frozenset({
        '/start',
        'Начать', 'Старт',
        'начать', 'старт',
        'Привет', 'привет',
        'Хай', 'хай',
        'Салют', 'салют',
        'Здравствуйте', 'здравствуйте',
        'Здравствуй', 'здравствуй',
        'Добрый день', 'добрый день',
        'Доброе утро', 'доброе утро',
        'Добрый вечер', 'добрый вечер',
        'Доброй ночи', 'доброй ночи',
    })
    HELP_TEXTS = frozenset({'/help', 'Помощь', 'помощь'})
    MAIN_MENU_BUTTONS = frozenset({
        ButtonConfig.CASES,
        ButtonConfig.CATEGORIES,
        ButtonConfig.SEARCH,
        ButtonConfig.FEEDBACK,
        *START_TEXTS,
    })


class PdConfig:
    """Настройки согласия на обработку ПДн."""

    CALLBACK_ACTIONS = frozenset({
        CallbackAction.PD_AGREE,
        CallbackAction.PD_DISAGREE,
        CallbackAction.PD_RETRY,
    })


class VkEnvConfig:
    """Переменные окружения VK (без секретов в коде)."""

    CHAT_PEER_OFFSET = 2_000_000_000

    @classmethod
    def get_admin_peer_id(cls) -> int | None:
        raw_peer = os.getenv('VK_ADMIN_PEER_ID')
        if raw_peer:
            return int(raw_peer)

        raw_chat = os.getenv('VK_ADMIN_CHAT_ID')
        if raw_chat:
            return cls.CHAT_PEER_OFFSET + int(raw_chat)

        return None


class LogConfig:
    """Сообщения для логов (не показываются пользователю)."""

    VK_ADMIN_PEER_NOT_SET = (
        'VK_ADMIN_PEER_ID не задан — уведомление об обратной связи не отправлено'
    )
    VK_ADMIN_NOTIFY_FAILED = 'Ошибка отправки обратной связи в админ-чат VK'
