# Development Setup

## Pre-commit Hooks

Этот проект использует pre-commit hooks для автоматического форматирования кода и проверок качества.

### Установка

После клонирования репозитория:

```bash
# Установка зависимостей
poetry install

# Установка pre-commit hooks
poetry run pre-commit install
```

### Что делают hooks

1. **isort** - сортирует и группирует импорты
2. **black** - форматирует код по стандарту PEP 8
3. **trailing-whitespace** - удаляет лишние пробелы в конце строк
4. **end-of-file-fixer** - добавляет перенос строки в конце файлов
5. **check-yaml** - проверяет синтаксис YAML файлов
6. **check-added-large-files** - предотвращает добавление больших файлов
7. **check-merge-conflict** - проверяет наличие merge conflicts

### Ручной запуск

```bash
# Запуск всех hooks на всех файлах
poetry run pre-commit run --all-files

# Запуск только black
poetry run black .

# Запуск только isort
poetry run isort .
```

### Обход hooks (не рекомендуется)

```bash
git commit --no-verify -m "commit message"
```

### Обновление hooks

```bash
poetry run pre-commit autoupdate
```

## Конфигурация

- **Black**: конфигурация в `pyproject.toml` под `[tool.black]`
- **isort**: конфигурация в `pyproject.toml` под `[tool.isort]`
- **Pre-commit**: конфигурация в `.pre-commit-config.yaml`

## Примечания

Pre-commit hooks автоматически запускаются при каждом `git commit`.
