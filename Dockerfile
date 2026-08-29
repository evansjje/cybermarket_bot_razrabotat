FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта
COPY . .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Создаем том для базы данных
VOLUME ["/app/data"]

# Устанавливаем переменную окружения для пути к БД
ENV DB_PATH=/app/data/cybermarket.db

# Команда запуска
CMD ["python", "main.py"]
