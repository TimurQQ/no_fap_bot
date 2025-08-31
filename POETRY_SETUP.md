# Настройка проекта с Poetry

## Быстрый старт

```bash
# 1. Переключите Poetry на Python 3.11
poetry env use python3.11

# 2. Установите зависимости
poetry install

# Примечание: poetry.lock не включен в репозиторий для избежания конфликтов
# при развертывании на разных системах. Зависимости будут разрешены из pyproject.toml

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

# S3 Configuration for database backups
S3_ENABLED=true
S3_BUCKET_NAME=your-bucket-name
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key
S3_REGION=ru-central1  # Регион
S3_ENDPOINT=https://storage.yandexcloud.net  # ОБЯЗАТЕЛЬНО! Endpoint S3-совместимого сервиса
```

### Команды Poetry
```bash
poetry install          # Установка зависимостей
poetry add package_name # Добавление новой зависимости
poetry shell           # Активация виртуального окружения
```

## Настройка Yandex Cloud для S3 бэкапов

### 1. Создание сервисного аккаунта
```bash
# В Yandex Cloud Console:
# 1. Перейдите в IAM → Сервисные аккаунты
# 2. Создайте новый сервисный аккаунт
# 3. Назначьте роли: storage.editor, storage.viewer
```

### 2. Создание статических ключей доступа
```bash
# В консоли Yandex Cloud:
# 1. Выберите сервисный аккаунт
# 2. Перейдите в "Статические ключи доступа"
# 3. Создайте новый ключ
# 4. Сохраните Access Key ID и Secret Access Key
```

### 3. Создание Object Storage bucket
```bash
# В Yandex Cloud Console:
# 1. Перейдите в Object Storage
# 2. Создайте новый bucket (например: nofap-challenge)
# 3. Настройте права доступа для сервисного аккаунта
```

### 4. Настройка .env для Yandex Cloud
```env
# Обязательные настройки для Yandex Cloud
S3_ENABLED=true
S3_BUCKET_NAME=nofap-challenge
S3_ACCESS_KEY=YCAJExxxxxxxxxx  # Access Key ID из п.2
S3_SECRET_KEY=YCPsAKxxxxxxxxx  # Secret Access Key из п.2
S3_REGION=ru-central1          # Регион Yandex Cloud
S3_ENDPOINT=https://storage.yandexcloud.net  # ОБЯЗАТЕЛЬНО для Yandex Cloud
```

### Альтернативные S3-совместимые сервисы
```env
# MinIO
S3_ENDPOINT=https://your-minio-server.com

# DigitalOcean Spaces
S3_ENDPOINT=https://fra1.digitaloceanspaces.com
S3_REGION=fra1

# Wasabi
S3_ENDPOINT=https://s3.wasabisys.com
S3_REGION=us-east-1

# AWS S3 (используйте endpoint для совместимости)
S3_REGION=us-west-2
S3_ENDPOINT=https://s3.us-west-2.amazonaws.com
```

### 5. Функциональность S3 бэкапов
- **Автоматический бэкап**: каждый день в 22:00 MSK (база данных + мемы)
- **Восстановление БД**: автоматически при отсутствии локальной БД
- **Восстановление мемов**: автоматически при пустой/отсутствующей папке мемов
- **Логирование**: детальная информация о ревизии БД и мемов
- **Безопасность**: приложение падает если нет БД ни локально, ни в S3
- **Отказоустойчивость**: бот продолжает работу без мемов если S3 недоступен
- **Деплой бэкап**: скрипт `pull_up_changes.sh` создает бэкапы при обновлении
- **Архивирование**: мемы сжимаются в ZIP архивы для экономии места

### 6. Скрипт деплоя
```bash
# Запуск обновления с бэкапами
./pull_up_changes.sh
```

Скрипт выполняет:
1. 📥 Обновление кода из репозитория
2. 🛑 Остановка текущего бота (поддержка Poetry процессов)
3. 💾 Локальные бэкапы (БД + мемы) с временными метками
4. ☁️ S3 бэкапы (БД + мемы) если S3 включен
5. 📦 Обновление зависимостей через Poetry
6. 🚀 Запуск обновленного бота через Poetry

**Простое завершение процессов:**
- Использует `pkill -f "no_fap.py"` для надежного поиска и завершения
- Работает независимо от способа запуска (python, poetry run, полный путь)
- Простая и надежная логика без сложных циклов

### 7. Структура S3 бэкапов
```
bucket/
├── database_backups/
│   ├── all_scores_saved_2025-08-31_15-28-20.json
│   └── all_scores_saved_latest.json
└── memes_backups/
    ├── memes_2025-08-31_15-28-20.zip
    └── memes_latest.zip
```

### 8. Логика автовосстановления
При запуске бота проверяется:

**База данных:**
- Если `storage/all_scores_saved.json` отсутствует → восстановление из S3
- Если восстановление не удалось → **бот падает с ошибкой**

**Мемы:**
- Если `storage/memes/` отсутствует или пуста → восстановление из S3
- Если восстановление не удалось → **бот продолжает работу** (создается пустая папка)

## Примечания

- Требуется Python 3.11 (aiogram 2.25.1 не совместим с Python 3.13)
- Флаг `-B` предотвращает создание `.pyc` файлов
- Все зависимости управляются через `pyproject.toml`
- `S3_ENDPOINT` обязателен для всех S3-совместимых сервисов (включая AWS)
- Приложение упадет с ошибкой если `S3_ENDPOINT` не задан
