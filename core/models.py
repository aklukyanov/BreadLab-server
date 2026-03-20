from django.db import models


class User(models.Model):
    """Пользователь бота (универсальный для всех каналов)"""

    # Поле id у Django уже есть по умолчанию (автоинкремент)
    # Для хранения ID из VK/Telegram нужно другое имя
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