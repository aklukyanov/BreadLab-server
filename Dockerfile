FROM python:3.14-slim
WORKDIR /app

# 1. Копируем файлы зависимостей (для кэширования)
COPY pyproject.toml uv.lock ./

# 2. Устанавливаем uv и зависимости в одном слое
RUN pip install --no-cache-dir uv && \
    uv sync --no-dev --frozen

# 3. Копируем всё остальное
COPY . .

# 4. Запускаем сервер
CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]