# Развёртывание ПравоТеки

Проект можно запустить через Docker Compose или напрямую на Linux-сервере.
Docker Compose — рекомендуемый вариант для production: он поднимает PostgreSQL,
применяет миграции, запускает backend и оба бота, а Caddy обеспечивает HTTPS.

## 1. Подготовка конфигурации

Создайте локальный файл окружения:

```bash
cp .env.example .env
chmod 600 .env
```

Заполните как минимум:

- `TG_BOT_TOKEN` и `VK_BOT_TOKEN`;
- `DB_NAME`, `DB_USER` и `DB_PASSWORD`;
- `YANDEX_DISK_TOKEN` и `YANDEX_DISK_BASE_PATH`;
- `TG_BACKEND_API_KEY` и `VK_BACKEND_API_KEY`;
- `SESSION_SECRET`, `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH`.

Для Docker-развёртывания также задайте:

- `APP_DOMAIN`;
- `LETSENCRYPT_EMAIL`;
- при необходимости `CONTAINER_NAME` и `DB_CONTAINER_NAME`.

При запуске без Docker дополнительно настройте `DB_HOST`, `DB_PORT`,
`BACKEND_URL`, `BACKEND_HOST` и `BACKEND_PORT`.

Для каждого ключа и секрета используйте отдельное случайное значение:

```bash
uv run --locked python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Argon2-хеш административного пароля:

```bash
uv run --locked python -c "from pwdlib import PasswordHash; print(PasswordHash.recommended().hash(input('Новый пароль: ')))"
```

Исходный пароль администратора в `.env` хранить не нужно.

## 2. Запуск через Docker Compose

### Требования

- Linux-сервер;
- Docker Engine;
- Docker Compose v2;
- домен с A/AAAA-записью на сервер;
- открытые TCP-порты 80 и 443.

UDP-порт 443 можно открыть для HTTP/3; основной HTTPS продолжит работать без
него.

Проверка и сборка:

```bash
docker compose config
docker compose build
```

Запуск:

```bash
docker compose up -d
docker compose ps
docker compose logs --tail=100 migrate backend
```

Порядок запуска управляется автоматически:

1. PostgreSQL проходит healthcheck.
2. Одноразовый контейнер `migrate` применяет миграции.
3. Запускается backend.
4. После healthcheck backend запускаются Telegram- и VK-боты.
5. Caddy принимает внешний HTTPS-трафик.

Проверка после запуска:

```text
https://<ваш-домен>/health
https://<ваш-домен>/admin
```

Ручная синхронизация контента:

```bash
docker compose exec backend python -m backend.sync_cases
```

Просмотр логов:

```bash
docker compose logs -f --tail=200
```

Остановка:

```bash
docker compose down
```

Команда `docker compose down -v` дополнительно удаляет данные PostgreSQL и
сертификаты Caddy. Не используйте `-v`, если требуется сохранить production
данные.

### Обновление

Сначала сделайте резервную копию БД, затем:

```bash
git pull --ff-only
docker compose build
docker compose up -d
docker compose ps
```

## 3. Запуск без Docker

### Требования

- Linux или macOS;
- Python 3.11–3.13;
- uv;
- PostgreSQL;
- отдельный reverse proxy с HTTPS для публичного production-запуска.

Установка production-зависимостей:

```bash
uv sync --locked --no-dev
```

В `.env` укажите адрес доступного PostgreSQL. Для локальной БД это обычно:

```env
DB_HOST=127.0.0.1
DB_PORT=5432
BACKEND_URL=http://127.0.0.1:8000
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
```

Создайте пользователя и пустую базу PostgreSQL, затем примените миграции:

```bash
uv run --locked --no-dev alembic upgrade head
```

Запустите три независимых процесса:

```bash
uv run --locked --no-dev python -m backend
uv run --locked --no-dev python -m tg_bot
uv run --locked --no-dev python -m vk_bot
```

В примере указаны три команды: backend и каждый бот должны работать постоянно
в отдельных процессах. На Linux-сервере используйте systemd, Supervisor или
другой process manager с автоматическим перезапуском.

Для публичного доступа backend должен слушать внутренний серверный интерфейс,
а reverse proxy — принимать HTTPS и передавать запросы на Uvicorn. Не
публикуйте PostgreSQL в интернет.

Ручная синхронизация:

```bash
uv run --locked --no-dev python -m backend.sync_cases
```

## 4. Резервное копирование PostgreSQL

Пример для Docker:

```bash
mkdir -p backups
docker compose exec -T postgres \
  sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' \
  > "backups/pravoteka-$(date +%F).dump"
```

Пример без Docker при экспортированных `DB_USER` и `DB_NAME`:

```bash
pg_dump -U "$DB_USER" -d "$DB_NAME" -Fc \
  > "backups/pravoteka-$(date +%F).dump"
```

Храните резервные копии отдельно от сервера приложения, шифруйте их и
периодически проверяйте восстановление на тестовой базе.

## 5. Проверка после развёртывания

- `/health` отвечает `{"status":"ok"}`;
- административная панель открывается только по HTTPS;
- миграции находятся на последней ревизии;
- Telegram и VK показывают меню и результаты поиска;
- переходы назад возвращают к исходному списку или категории;
- DOCX скачиваются;
- ручная синхронизация не создаёт дубликаты;
- в логах нет токенов, паролей и персональных данных.
