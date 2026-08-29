FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы проекта
COPY . .

# Создаем том для базы данных
VOLUME ["/app/data"]

# Указываем переменную окружения для пути к базе данных
ENV DB_PATH=/app/data/cybermarket.db

# Команда для запуска бота
CMD ["python", "main.py"]
