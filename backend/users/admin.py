from django.db.models import Count
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from django.utils.safestring import mark_safe

from .models import Follow
from recipes.models import RecipeFavorite

User = get_user_model()

admin.site.unregister(Group)
admin.site.empty_value_display = 'Не задано'


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    list_filter = ('user', 'author')
    list_display_links = ('user',)


class FollowInLine(admin.TabularInline):
    model = Follow
    extra = 1
    fk_name = 'user'


class RecipeFavoriteInLine(admin.TabularInline):
    model = RecipeFavorite
    extra = 1


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    filter_horizontal = ()
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'avatar')}),
        ('Permissions', {'fields': ('is_active', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    inlines = (FollowInLine, RecipeFavoriteInLine)
    list_display = (
        'id', 'username', 'email',
        'first_name', 'last_name',
        'is_active', 'is_superuser',
        'recipes_count', 'followers_count', 'get_avatar'
    )
    list_filter = ('is_active', 'is_superuser')
    search_fields = ('username', 'email')
    list_display_links = ('username',)

    @admin.display(description='Аватар')
    def get_avatar(self, obj):
        if obj.avatar and obj.avatar.url:
            return mark_safe(f'<img src={obj.avatar.url} '
                             'width="60" height="60">')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            recipes_count=Count('recipes'),
            followers_count=Count('follows_to_author')
        )

    @admin.display(description='Количество рецептов',
                   ordering='recipes_count')
    def recipes_count(self, obj):
        return obj.recipes_count

    @admin.display(description='Количество подписчиков',
                   ordering='followers_count')
    def followers_count(self, obj):
        return obj.followers_count
