from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from vkbottle.tools import Callback, Keyboard, KeyboardButtonColor, Text


class BaseKeyboard(ABC):
    """Базовый класс для всех клавиатур VK."""

    @abstractmethod
    def get_markup(self) -> str:
        pass


class BaseReplyKeyboard(BaseKeyboard):
    """Базовый класс для reply-клавиатур."""

    def _build_reply_markup(
        self,
        rows: list[list[str]],
        *,
        one_time: bool = False,
    ) -> str:
        keyboard = Keyboard(one_time=one_time, inline=False)
        for row in rows:
            keyboard.row()
            for label in row:
                keyboard.add(Text(label), color=KeyboardButtonColor.PRIMARY)
        return keyboard.get_json()


class EmptyReplyKeyboard(BaseReplyKeyboard):
    """Пустая reply-клавиатура — явно скрывает кнопки главного меню."""

    def get_markup(self) -> str:
        return self._build_reply_markup([])


class BaseInlineKeyboard(BaseKeyboard):
    """Базовый класс для inline-клавиатур."""

    @staticmethod
    def make_payload(action: str, **data: Any) -> dict[str, Any]:
        return {'action': action, **data}

    @staticmethod
    def build_inline_markup(
        buttons: list[tuple[str, dict[str, Any]]],
        row_width: int = 1,
    ) -> str:
        keyboard = Keyboard(inline=True)
        for index, (label, payload) in enumerate(buttons):
            if index % row_width == 0:
                keyboard.row()
            keyboard.add(
                Callback(label, payload=payload),
                color=KeyboardButtonColor.PRIMARY,
            )
        return keyboard.get_json()

    def _build_inline_markup(
        self,
        buttons: list[tuple[str, dict[str, Any]]],
        row_width: int = 1,
    ) -> str:
        return self.build_inline_markup(buttons, row_width=row_width)

    @staticmethod
    def append_buttons(
        markup: str,
        buttons: list[tuple[str, dict[str, Any]]],
    ) -> str:
        """Добавляет кнопки в существующую inline-клавиатуру."""

        import json

        data = json.loads(markup)
        for label, payload in buttons:
            data['buttons'].append([{
                'action': {
                    'type': 'callback',
                    'label': label,
                    'payload': json.dumps(payload, ensure_ascii=False),
                },
                'color': 'primary',
            }])
        return json.dumps(data, ensure_ascii=False)
