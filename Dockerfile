FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копирование файлов проекта
COPY requirements.txt .
COPY config.py .
COPY database.py .
COPY keyboards.py .
COPY main.py .
COPY handlers/ ./handlers/

# Установка Python-зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Создание директории для базы данных
RUN mkdir -p /app/data

# Переменные окружения (переопределяются при запуске)
ENV BOT_TOKEN="YOUR_BOT_TOKEN_HERE"
ENV YOOKASSA_SHOP_ID="YOUR_SHOP_ID"
ENV YOOKASSA_SECRET_KEY="YOUR_SECRET_KEY"
ENV ADMIN_IDS=""

# Запуск бота
CMD ["python", "main.py"]
