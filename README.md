# 🍞 BreadLab

Помощник домашнего пекаря: расчёты, рецепты и документация выпечки.

Проект состоит из двух частей:
*   **Клиентская** (VK-бот + Redis для хранения сессий и состояний)
*   **Серверная** (Django API + PostgreSQL для данных и расчётов)

Взаимодействуют через HTTP API. Основной функционал покрыт тестами.

---

📋 Серверная часть: API для расчётов, хранения и обработки рецептов.


## Функционал

**📚 CRUD для рецептов:** создание, чтение, обновление и удаление рецептов с пагинацией.
**🧮 Расчёт закваски:** эндпоинты для пересчёта опары 50% ↔ 100% влажности и умножения рецептов.
**🤖 LLM-интеграция:** запросы к Ollama api для распознавания рецептов по тексту и фото, а также редактирования на естесственном языке.


---

## 🛠️ Стек

*   Python 3.14
*   Django / Django REST Framework
*   PostgreSQL
*   Ollama (LLM)
*   pytest
*   Docker / docker-compose

---

## 🚀 Локальный запуск

1.  **Клонируйте репозиторий**
    ```bash
    git clone https://github.com/aklukyanov/BreadLab-server.git
    cd BreadLab-server

2. **Создайте файл .env в корне проекта:**
    ```env
    DJANGO_SECRET_KEY=ваш_секретный_ключ
    POSTGRES_DB=breadlab-db
    POSTGRES_USER=breadlab_user
    POSTGRES_PASSWORD=пароль_для_базы
    OLLAMA_API_KEY=ключ_ollama_api
    
3.  **Запустите через Docker**
    ```bash
    docker-compose up --build

Клиентская часть: https://github.com/aklukyanov/BreadLabBot_vk

