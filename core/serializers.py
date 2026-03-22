from rest_framework import serializers
from core.models import User, Recipe

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'external_id', 'channel', 'first_name', 'last_name', 'username', 'gender', 'platforms', 'registered_at', 'last_active')
        read_only_fields = ('id','registered_at', 'last_active')

class RecipeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'user', 'user_id', 'parents', 'recipe', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at', 'parents')