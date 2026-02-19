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
    list_display = ('id', 'user_is_following', 'user_being_followed')
    list_filter = ('user_is_following', 'user_being_followed')
    list_display_links = ('user_is_following',)


class FollowInLine(admin.TabularInline):
    model = Follow
    extra = 1
    fk_name = 'user_is_following'


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
        'first_name', 'last_name', 'is_active', 'is_superuser', 'get_avatar'
    )
    list_filter = ('is_active', 'is_superuser')
    search_fields = ('username', 'email')
    list_display_links = ('username',)

    @admin.display(description='Аватар')
    def get_avatar(self, obj):
        if obj.avatar and obj.avatar.url:
            return mark_safe(f'<img src={obj.avatar.url} '
                             'width="60" height="60">')
