from django.contrib import admin

from recipes.models import (Ingredient, Recipe, RecipeIngredient,
                            RecipeFavorite,
                            RecipeTag, ShoppingCart, Tag)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    list_display_links = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)
    list_display_links = ('name',)


class IngredientsInLine(admin.StackedInline):
    model = RecipeIngredient
    extra = 1


class TagsInLine(admin.StackedInline):
    model = RecipeTag
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'pub_date', 'text',
                    'favorites_amount')
    search_fields = ('name', 'author__username')
    list_filter = ('author', 'name', 'tags')
    list_display_links = ('name',)
    inlines = (IngredientsInLine, TagsInLine)
    empty_value_display = 'Поле не заполнено'

    @admin.display(description='Добавлено в избранное')
    def favorites_amount(self, obj):
        return obj.favorite_recipes.count()


@admin.register(RecipeFavorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe',)
    search_fields = ('user__username', 'recipe__name',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe',)
    search_fields = ('user__username', 'recipe__name',)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount',)
    search_fields = ('recipe__name', 'ingredient__name')


@admin.register(RecipeTag)
class RecipeTagAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'tag',)
    search_fields = ('recipe__name', 'tag__name')
