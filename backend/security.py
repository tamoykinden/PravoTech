"""Аутентификация клиентов и администратора."""

import hashlib
import hmac
import os
from dataclasses import dataclass

from fastapi import HTTPException, Request, status
from pwdlib import PasswordHash

from config import required_env

password_hash = PasswordHash.recommended()


@dataclass(frozen=True)
class AdminSettings:
    """Учётные данные администратора из безопасного окружения."""

    username: str
    password_hash: str

    @classmethod
    def load(cls) -> 'AdminSettings':
        """Загружает обязательные настройки администратора."""

        return cls(
            username=required_env('ADMIN_USERNAME'),
            password_hash=required_env('ADMIN_PASSWORD_HASH'),
        )


def authenticate_admin(username: str, password: str) -> bool:
    """Проверяет логин и Argon2-хеш пароля без утечки по времени."""

    settings = AdminSettings.load()
    username_ok = hmac.compare_digest(username, settings.username)
    try:
        password_ok = password_hash.verify(password, settings.password_hash)
    except Exception:
        password_ok = False
    return username_ok and password_ok


def require_admin(request: Request) -> str:
    """Разрешает доступ только активной административной сессии."""

    username = request.session.get('admin_username')
    if not username:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={'Location': '/admin/login'},
        )
    return str(username)


def api_key_fingerprint(value: str) -> str:
    """Формирует безопасный отпечаток ключа для диагностики."""

    return hashlib.sha256(value.encode()).hexdigest()[:12]
