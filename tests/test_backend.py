"""Smoke- и security-тесты центрального backend."""

from fastapi.testclient import TestClient

from backend.main import app
from config import BackendConfig


def test_health_and_security_headers() -> None:
    """Health endpoint отвечает и содержит защитные заголовки."""

    with TestClient(app) as client:
        response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}
    assert response.headers['x-content-type-options'] == 'nosniff'
    assert response.headers['x-frame-options'] == 'DENY'


def test_client_api_rejects_missing_key() -> None:
    """Клиентское API недоступно без платформенного ключа."""

    with TestClient(app) as client:
        response = client.get('/api/v1/telegram/categories')
    assert response.status_code == 401


def test_client_api_accepts_platform_key() -> None:
    """Корректный Telegram-ключ разрешает чтение категорий."""

    with TestClient(app) as client:
        response = client.get(
            '/api/v1/telegram/categories',
            headers={'X-API-Key': BackendConfig.client_api_key('telegram')},
        )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_admin_rejects_wrong_password() -> None:
    """Админка не создаёт сессию при неверном пароле."""

    with TestClient(app) as client:
        response = client.post(
            '/admin/login',
            data={'username': 'admin', 'password': 'definitely-wrong'},
        )
    assert response.status_code == 401
    assert 'Неверные учётные данные' in response.text
