FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код проекта
COPY . .

# Создаем том для базы данных
VOLUME ["/app/data"]

# Устанавливаем переменные окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DB_PATH=/app/data/cybermarket.db

# Открываем порт (если нужен для вебхуков)
EXPOSE 8080

# Команда для запуска бота
CMD ["python", "main.py"]
