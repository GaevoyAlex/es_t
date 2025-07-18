FROM python:3.13-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && \
    apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Установка Poetry
RUN pip install poetry==1.8.2

# Копирование файлов конфигурации Poetry
COPY pyproject.toml poetry.lock* ./

# Настройка Poetry и установка зависимостей
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

# Установка дополнительных пакетов если нужно
RUN pip install pydantic-settings

# Копирование кода приложения
COPY . .

# Создание директории для логов
RUN mkdir -p /app/logs

# Запуск приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]