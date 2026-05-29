from abc import ABC, abstractmethod


class BaseHandler(ABC):
    """Базовый класс для всех обработчиков VK-бота."""

    def __init__(self, bot):
        self.bot = bot

    @abstractmethod
    def handle(self, event) -> None:
        """Обрабатывает событие."""

        pass
