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
        'Если у вас возникла ситуация, которой нет в боте — напишите в обратную связь, мы добавим её.'
    )
    NO_CASES = 'Кейсы пока не добавлены.'
    NO_FIND_CASES = 'Кейс не найден.'
    NO_FIND_FILE = 'Файл не найден.'
    NO_CATEGORIES = 'Категории пока не добавлены.'
    NO_CASES_IN_CAT = 'В этой категории пока нет кейсов.'
    FEEDBACK = (
        'Напишите ваше сообщение или опишите ситуацию, которой нет в боте.\n\n'
        'Мы рассмотрим и добавим её в ближайшее время.\n\n'
        'Чтобы отменить — нажмите "Назад".'
    )
    FEEDBACK_CANCEL = 'Обратная связь отменена.'
    PLEASE_FOR_FEEDBACK = 'Пожалуйста, напишите сообщение подробнее (минимум 5 символов).'
    THANKS_FOR_FEEDBACK = 'Спасибо за обратную связь! Мы обязательно рассмотрим ваше сообщение.'
    INSTRUCTIONS_FOR_SEARCH = (
        'Введите ключевые слова для поиска (через пробел):\n\n'
        'Например: <i>шум соседи</i> или <i>возврат товара</i>'
    )
    SEARCH_CANCELED = 'Поиск отменён.'
    TWO_SIMBOLS = 'Введите минимум 2 символа для поиска.'
    FOUND_NOTHING = (
        'Ничего не найдено.\n\n'
        'Попробуйте изменить запрос или обратитесь в обратную связь, '
        'если вашей ситуации нет в боте.',
    )
    MAIN_WORD = 'Введите ключевые слова для поиска (через пробел):'

class ButtonConfig:
    """Текст кнопок."""

    BACK = 'Назад'
    CASES = 'Список кейсов'
    CATEGORIES = 'Категории'
    FEEDBACK = 'Обратная связь'
    SEARCH = 'Поиск кейса'
