# Используем официальный образ Python 3.11
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

# Создаем директорию для базы данных и файлов
RUN mkdir -p /app/data /app/files

# Указываем переменные окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    BOT_TOKEN="YOUR_BOT_TOKEN_HERE" \
    YOOKASSA_SHOP_ID="YOUR_SHOP_ID_HERE" \
    YOOKASSA_SECRET_KEY="YOUR_SECRET_KEY_HERE" \
    YOOKASSA_PAYMENT_TOKEN="YOUR_PAYMENT_TOKEN_HERE" \
    ADMIN_IDS="[123456789]"

# Открываем порт (если нужно)
EXPOSE 8080

# Команда для запуска бота
CMD ["python", "main.py"]
