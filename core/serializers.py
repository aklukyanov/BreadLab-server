from rest_framework import serializers
from core.models import User, Recipe, BakingSession, BakingNote


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели User.

    Используется для представления данных пользователя.
    Вложен в RecipeSerializer и BakingSessionSerializer.

    Пример ответа (GET):
        {
            "id": 1,
            "external_id": "12345678",
            "channel": "vk",
            "first_name": "Алексей",
            "last_name": "Иванов",
            "username": "alexey",
            "gender": "male",
            "platforms": ["vk", "web"],
            "registered_at": "2026-01-15T10:30:00Z",
            "last_active": "2026-09-09T12:00:00Z"
        }
    """

    class Meta:
        model = User
        fields = ('id', 'external_id', 'channel', 'first_name', 'last_name', 'username', 'gender', 'platforms', 'registered_at', 'last_active')
        read_only_fields = ('id', 'registered_at', 'last_active')


class RecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели Recipe.

    Сериализует рецепт с вложенными данными пользователя.
    user (read_only) — полный объект пользователя.
    user_id (write_only) — ID пользователя для создания рецепта.
    Пример запроса (POST /recipes/):
        {
            "user_id": 1,
            "recipe": {
                "status": "ok",
                "data": {
                    "title": "БОРОДИНСКИЙ",
                    "groups": [
                        {
                            "name": "Основа",
                            "ingredients": [
                                {"name": "Мука", "quantity": 500, "unit": "г."},
                                {"name": "Вода", "quantity": 350, "unit": "мл."}
                            ]
                        }
                    ],
                    "dry_sum": 500,
                    "wet_sum": 350,
                    "hydration": 70.0
                }
            }
        }

    Пример ответа (GET /recipes/1/):
        {
            "id": 1,
            "user": {
                "id": 1,
                "external_id": "12345678",
                "channel": "vk",
                "first_name": "Алексей",
                "last_name": "Иванов",
                "username": "alexey",
                "gender": "male",
                "platforms": ["vk", "web"],
                "registered_at": "2026-01-15T10:30:00Z",
                "last_active": "2026-09-09T12:00:00Z"
            },
            "parents": [],
            "recipe": {
                "status": "ok",
                "data": {
                    "title": "БОРОДИНСКИЙ",
                    "groups": [...],
                    "dry_sum": 500,
                    "wet_sum": 350,
                    "hydration": 70.0
                }
            },
            "created_at": "2026-09-09T10:00:00Z",
            "updated_at": "2026-09-09T10:00:00Z"
        }
    """

    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'user', 'user_id', 'parents', 'recipe', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at', 'parents')


class BakingSessionSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели BakingSession.

    Сериализует сессию выпечки — факт выпечки конкретного рецепта пользователем.

    Пример запроса (POST /baking_sessions/):
        {
            "user_id": 1,
            "recipe_id": 5,
            "status": "unfinished"
        }

    Пример ответа (GET /baking_sessions/1/):
        {
            "id": 1,
            "recipe_title": "Сита",
            "status": "unfinished",
            "created_at": "2026-09-09T12:00:00Z",
            "updated_at": "2026-09-09T12:00:00Z"
        }

    Пример обновления (PATCH /baking_sessions/1/):
        {
            "status": "finished"
        }

    Пример ответа после обновления:
        {
            "id": 1,
            "recipe_title": "Сита",
            "status": "finished",
            "created_at": "2026-09-09T12:00:00Z",
            "updated_at": "2026-09-09T13:00:00Z"
        }
    """

    user_id = serializers.IntegerField(write_only=True)
    recipe_id = serializers.IntegerField(write_only=True)
    recipe_title = serializers.CharField(source='recipe.title', read_only=True)

    class Meta:
        model = BakingSession
        fields = (
            'id',
            'user_id',
            'recipe_title', 'recipe_id',
            'status',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'recipe_title', 'created_at', 'updated_at')


class BakingNoteSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели BakingNote.

    Сериализует заметку, привязанную к сессии выпечки.
    Заметка может быть текстом или ссылкой на фото в VK.

    Пример запроса — текстовая заметка (POST /baking_notes/):
        {
            "baking_session_id": 1,
            "type": "text",
            "note": "Тесто поднялось за 3 часа, очень пышное"
        }

    Пример запроса — фото (POST /baking_notes/):
        {
            "baking_session_id": 1,
            "type": "photo",
            "note": "https://vk.com/photo-123_456"
        }

    Пример ответа (GET /baking_notes/1/):
        {
            "id": 1,
            "baking_session_id": 1,
            "note": "Тесто поднялось за 3 часа, очень пышное",
            "type": "text",
            "created_at": "2026-09-09T12:05:00Z",
            "updated_at": "2026-09-09T12:05:00Z"
        }

    Пример обновления (PATCH /baking_notes/1/):
        {
            "note": "Тесто поднялось за 2.5 часа"
        }

    Пример ответа после обновления:
        {
            "id": 1,
            "baking_session_id": 1,
            "note": "Тесто поднялось за 2.5 часа",
            "type": "text",
            "created_at": "2026-09-09T12:05:00Z",
            "updated_at": "2026-09-09T12:10:00Z"
        }
    """

    baking_session_id = serializers.IntegerField()

    class Meta:
        model = BakingNote
        fields = (
            'id',
            'baking_session_id',
            'note',
            'type',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
