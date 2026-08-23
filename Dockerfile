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

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Создание директории для данных
RUN mkdir -p /app/data

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Запуск бота
CMD ["python", "main.py"]
