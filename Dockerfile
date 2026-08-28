FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы проекта
COPY . .

# Создаем том для базы данных
VOLUME ["/app/data"]

# Устанавливаем переменную окружения для пути к БД
ENV DB_PATH=/app/data/cybermarket.db

# Запускаем бота
CMD ["python", "main.py"]
