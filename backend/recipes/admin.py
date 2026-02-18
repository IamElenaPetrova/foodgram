from django.core.exceptions import ValidationError
from django.contrib import admin
from django.forms.models import BaseInlineFormSet

from recipes.forms import RecipeAdminForm
from recipes.models import (Ingredient, Recipe, RecipeIngredient,
                            RecipeFavorite,
                            ShoppingCart, Tag)
from .constants import ERROR_NON_UNIQUE_INGREDIENTS, ERROR_NO_INGREDIENTS


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


class RecipeIngredientInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        ingredients = []
        for form in self.forms:
            if (form.cleaned_data
                    and not form.cleaned_data.get('DELETE', False)):
                ingredient = form.cleaned_data.get('ingredient')
                if ingredient in ingredients:
                    raise ValidationError(ERROR_NON_UNIQUE_INGREDIENTS)
                ingredients.append(ingredient)

        if not ingredients:
            raise ValidationError(ERROR_NO_INGREDIENTS)


class IngredientsInLine(admin.StackedInline):
    model = RecipeIngredient
    formset = RecipeIngredientInlineFormSet
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    form = RecipeAdminForm
    list_display = ('id', 'name', 'author', 'pub_date', 'text',
                    'favorites_amount')
    search_fields = ('name', 'author__username')
    list_filter = ('author', 'name', 'tags')
    filter_horizontal = ('tags',)
    list_display_links = ('name',)
    inlines = (IngredientsInLine,)
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
