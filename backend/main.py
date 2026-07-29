"""Фабрика и точка запуска FastAPI-приложения."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from backend import admin, api
from config import BackendConfig, DBConfig, required_env
from database.base import Database
from logger import bot_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Открывает пул БД при старте и гарантированно закрывает при остановке."""

    app.state.database = Database(DBConfig())
    yield
    await app.state.database.engine.dispose()


def create_app() -> FastAPI:
    """Создаёт backend с безопасными production-настройками."""

    production = BackendConfig.ENVIRONMENT == 'production'
    session_secret = required_env('SESSION_SECRET')
    if len(session_secret) < 32:
        raise ValueError('SESSION_SECRET должен содержать минимум 32 символа')
    BackendConfig.client_api_key('telegram')
    BackendConfig.client_api_key('vk')

    app = FastAPI(
        title='ПравоТека API',
        docs_url=None if production else '/docs',
        redoc_url=None,
        lifespan=lifespan,
    )
    app.add_middleware(
        SessionMiddleware,
        secret_key=session_secret,
        same_site='lax',
        https_only=production,
        max_age=3600,
    )

    @app.middleware('http')
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self' 'unsafe-inline'"
        if production:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    @app.exception_handler(Exception)
    async def unexpected_error(_: Request, error: Exception):
        bot_logger.exception('Необработанная ошибка backend: {}', type(error).__name__)
        return JSONResponse({'detail': 'Внутренняя ошибка сервера'}, status_code=500)

    @app.get('/health')
    async def health():
        return {'status': 'ok'}

    @app.get('/', include_in_schema=False)
    async def root():
        return RedirectResponse('/admin')

    app.include_router(api.router)
    app.include_router(admin.router)
    return app


app = create_app()
