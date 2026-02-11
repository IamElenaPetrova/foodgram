from django_filters import FilterSet, ModelMultipleChoiceFilter, NumberFilter
from rest_framework.filters import SearchFilter

from recipes.models import Recipe, Tag


class NameSearchFilter(SearchFilter):
    """ Фильтр с параметром name. """
    search_param = 'name'


class RecipeFilter(FilterSet):
    """ Фильтр для рецепта. """
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )

    is_favorited = NumberFilter()
    is_in_shopping_cart = NumberFilter()

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']

    def filter_is_favorited(self, queryset, name, value):
        if not self.request.user.is_authenticated:
            return queryset
        if value == 1:
            return queryset.filter(favorite_recipes__user=self.request.user)
        elif value == 0:
            return queryset.exclude(favorite_recipes__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if not self.request.user.is_authenticated:
            return queryset
        if value == 1:
            return queryset.filter(
                shopping_cart_recipes__user=self.request.user
            )
        elif value == 0:
            return queryset.exclude(
                shopping_cart_recipes__user=self.request.user
            )
        return queryset
