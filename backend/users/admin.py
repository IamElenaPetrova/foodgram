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


class FollowInLine(admin.TabularInline):
    model = Follow
    extra = 1
    fk_name = 'user_is_following'


class RecipeFavoriteInLine(admin.TabularInline):
    model = RecipeFavorite
    extra = 1


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (FollowInLine, RecipeFavoriteInLine)
    list_display = (
        'id', 'username', 'email',
        'first_name', 'last_name', 'is_staff', 'get_avatar'
    )
    list_filter = ('is_staff', 'is_superuser')
    search_fields = ('username', 'email')

    @admin.display(description='Аватар')
    def get_avatar(self, obj):
        if obj.avatar and obj.avatar.url:
            return mark_safe(f'<img src={obj.avatar.url} '
                             'width="60" height="60">')
