from abc import ABC, abstractmethod


class BaseKeyboard(ABC):
    """Базовый класс для клавиатур VK."""

    @abstractmethod
    def get_markup(self) -> str:
        """Возвращает JSON-клавиатуру."""

        pass
