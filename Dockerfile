# Используем стабильную версию Python на базе Linux Debian
FROM python:3.12-slim

# Устанавливаем рабочую папку в контейнере
WORKDIR /app

# Копируем файл с зависимостями
COPY requirements.txt .

# Обновляем pip и устанавливаем библиотеки
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем весь оставшийся код нашего API
COPY . .

# Открываем порт 8000
EXPOSE 8000

# Запускаем uvicorn. Флаг --host 0.0.0.0 обязателен для Docker!
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
