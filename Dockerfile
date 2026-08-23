# Используем официальный образ Python 3.11 на базе Alpine Linux для минимального размера
FROM python:3.11-alpine

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Устанавливаем системные зависимости, необходимые для сборки некоторых Python-пакетов
# (например, aiosqlite требует компиляции, а pydantic-core — Rust)
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    libffi-dev \
    && apk add --no-cache \
    sqlite \
    && pip install --no-cache-dir --upgrade pip

# Копируем файл с зависимостями Python
COPY requirements.txt .

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код проекта в контейнер
COPY . .

# Создаем директорию для базы данных и файлов (если потребуется)
RUN mkdir -p /app/data

# Указываем порт (необязательно для Telegram-бота, но полезно для healthcheck)
EXPOSE 8080

# Запускаем бота
CMD ["python", "main.py"]
