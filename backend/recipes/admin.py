from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.safestring import mark_safe

from recipes.models import (Ingredient, Recipe, RecipeIngredient,
                            RecipeFavorite,
                            ShoppingCart, Tag)


class CookingTimeFilter(SimpleListFilter):
    title = 'Время готовки'
    parameter_name = 'cooking_time'

    def lookups(self, request, model_admin):
        return (
            ('fast', 'Быстрые (до 30 мин)'),
            ('medium', 'Средние (30-60 мин)'),
            ('long', 'Долгие (от 60 мин)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'fast':
            return queryset.filter(cooking_time__lte=30)
        if self.value() == 'medium':
            return queryset.filter(
                cooking_time__gt=30,
                cooking_time__lte=60
            )
        if self.value() == 'long':
            return queryset.filter(cooking_time__gt=60)
        return queryset


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    list_display_links = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_display_links = ('name',)


class IngredientsInLine(admin.StackedInline):
    model = RecipeIngredient
    min_num = 1
    validate_min = True
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'pub_date', 'text',
                    'ingredients_list', 'tags_list',
                    'favorites_amount')
    search_fields = ('name', 'author__username')
    list_filter = ('author', 'name', 'tags', CookingTimeFilter)
    filter_horizontal = ('tags',)
    list_display_links = ('name',)
    inlines = (IngredientsInLine,)
    empty_value_display = 'Поле не заполнено'

    @admin.display(description='Добавлено в избранное')
    def favorites_amount(self, obj):
        return obj.favorite_recipes.count()

    @admin.display(description='Ингредиенты')
    def ingredients_list(self, obj):
        return ', '.join(
            ingredient.name for ingredient in obj.ingredients.all()
        )

    @admin.display(description='Теги')
    def tags_list(self, obj):
        return ', '.join(tag.name for tag in obj.tags.all())

    @admin.display(description='Картинка')
    def image_preview(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" width="80" height="60" />'
            )
        return 'Нет изображения'


@admin.register(RecipeFavorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe',)
    search_fields = ('user__username', 'recipe__name',)
    list_filter = ('user', )
    list_display_links = ('user',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe',)
    search_fields = ('user__username', 'recipe__name',)
    list_filter = ('user', )
    list_display_links = ('user',)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount',)
    search_fields = ('recipe__name', 'ingredient__name')
    list_filter = ('recipe', )
