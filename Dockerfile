FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы проекта
COPY . .

# Создаем том для базы данных (чтобы данные сохранялись между перезапусками)
VOLUME ["/app/data"]

# Устанавливаем переменную окружения для пути к БД (опционально)
ENV DB_PATH=/app/data/cybermarket.db

# Команда запуска бота
CMD ["python", "main.py"]
