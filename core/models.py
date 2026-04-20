from django.db import models



class User(models.Model):
    """Пользователь бота (универсальный для всех каналов)"""

    external_id = models.CharField(max_length=100, db_index=True, verbose_name="Social network ID")

    channel = models.CharField(
        max_length=20,
        choices=[
            ('vk', 'VK'),
            ('web', 'Web'),
            ('telegram', 'Telegram'),
        ],
        default='vk',
        verbose_name="Channel"
    )

    # Личные данные
    first_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="First name")
    last_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Last name")
    username = models.CharField(max_length=255, blank=True, null=True, verbose_name="Username")
    gender = models.CharField(
        max_length=20,
        choices=[('male', 'Male'), ('female', 'Female')],
        blank=True,
        null=True,
        verbose_name="Gender"
    )

    # Платформы (откуда заходил)
    platforms = models.JSONField(default=list, blank=True, verbose_name="Platforms")

    # Мета
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name="Registered at")
    last_active = models.DateTimeField(auto_now=True, verbose_name="Last active")

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        constraints = [
            models.UniqueConstraint(
                fields=['external_id', 'channel'],
                name='unique_user_per_channel'
            )
        ]
        indexes = [
            models.Index(fields=['external_id', 'channel']),
            models.Index(fields=['last_active']),
        ]

    def __str__(self):
        name = f"{self.first_name} {self.last_name}".strip()
        if name:
            return f"{self.channel}:{self.external_id} ({name})"
        return f"{self.channel}:{self.external_id}"


class Recipe(models.Model):
    """Рецепт пользователя"""
    id: int

    # Связь с пользователем
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name="User"
    )

    #Название рецепта
    title = models.CharField(max_length=255, blank=True)

    # JSON-данные рецепта
    recipe = models.JSONField(
        blank=True,
        verbose_name="Recipe",
        help_text="Сырой JSON от Qwen"
    )

    parents=models.JSONField(default=list, blank=True, verbose_name="Parents")

    hydration = models.FloatField(
        blank=True,
        null=True,
        verbose_name="Hydration %",
        help_text="(wet_sum / dry_sum) * 100"
    )

    # Метаданные
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Creation time"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Update time"
    )

    class Meta:
        verbose_name = "Recipe"
        verbose_name_plural = "Recipes"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['hydration']),
        ]

    def __str__(self):
        recipe_name = self.recipe.get('name', 'Unnamed') if self.recipe else 'Empty'
        return f"{recipe_name} ({self.user})"

