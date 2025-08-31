# Настройка проекта с Poetry

## Быстрый старт

```bash
# 1. Переключите Poetry на Python 3.11
poetry env use python3.11

# 2. Установите зависимости
poetry install

# 3. Создайте папку для логов
mkdir -p logs

# 4. Настройте .env файл с токеном бота
# BOT_TOKEN=your_bot_token_here
# USE_LOCAL_SERVER=false

# 5. Запустите бота
poetry run python -B no_fap.py
```

## Конфигурация

### .env файл
```env
BOT_TOKEN=your_bot_token_here
USE_LOCAL_SERVER=false  # true для локального Telegram API
LOCAL_SERVER_URL=http://localhost:8081
```

### Команды Poetry
```bash
poetry install          # Установка зависимостей
poetry add package_name # Добавление новой зависимости
poetry shell           # Активация виртуального окружения
```

## Примечания

- Требуется Python 3.11 (aiogram 2.25.1 не совместим с Python 3.13)
- Флаг `-B` предотвращает создание `.pyc` файлов
- Все зависимости управляются через `pyproject.toml`
