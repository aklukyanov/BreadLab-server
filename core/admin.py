from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """User model admin interface"""

    list_display = (
        'id',
        'external_id',
        'channel',
        'first_name',
        'last_name',
        'username',
        'registered_at',
        'last_active'
    )

    list_filter = ('channel', 'registered_at', 'last_active')

    search_fields = ('external_id', 'first_name', 'last_name', 'username')

    readonly_fields = ('registered_at', 'last_active')

    fieldsets = (
        ('Identification', {
            'fields': ('external_id', 'channel')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'username', 'gender')
        }),
        ('Platforms', {
            'fields': ('platforms',)
        }),
        ('Metadata', {
            'fields': ('registered_at', 'last_active'),
            'classes': ('collapse',)
        }),
    )