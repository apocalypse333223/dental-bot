# Запуск без ПК

Проект подготовлен для облачного запуска через Docker. Секреты не хранятся в архиве.

## Переменные окружения

Обязательные:
- `BOT_TOKEN` — токен Telegram-бота.
- `ADMIN_TELEGRAM_IDS` — Telegram ID администратора.

Для AI-классификации:
- `LLM_API_KEY`
- `LLM_API_BASE_URL` (можно оставить пустым для OpenAI)
- `LLM_MODEL`

`DATABASE_URL` по умолчанию использует SQLite для тестового запуска.

## Важно

Не загружайте настоящий `.env` в GitHub. Токен Telegram храните только в Secrets/Environment Variables облачного сервиса.

В проекте есть `Dockerfile` и `render.yaml` для сервисов, поддерживающих Docker/worker. Для Render используется worker, потому что бот работает через Telegram long polling, а не через HTTP-сервер.
