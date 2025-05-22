FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование только необходимых файлов
COPY backend/ ./backend/
COPY Procfile .

# Переменные окружения по умолчанию - будут переопределены Railway
ENV PORT=8000
ENV HOST=0.0.0.0
ENV DATABASE_URL=sqlite:///./users.db
ENV SECRET_KEY=insecure_key_change_in_production
ENV ACCESS_TOKEN_EXPIRE_MINUTES=30
ENV FRONTEND_URL=*
ENV ADMIN_URL=*

# Установка рабочей директории для запуска и настройка портов
EXPOSE $PORT

# Команда для запуска приложения
CMD uvicorn backend.main:app --host $HOST --port $PORT 