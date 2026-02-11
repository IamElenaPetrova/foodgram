from rest_framework import serializers
from django.contrib.auth import get_user_model
from re import match

from recipes.constants import WRONG_SLUG_MESSAGE
from recipes.models import Ingredient
from users.constants import (EMAIL_NON_UNIQUE,
                             REGEXVALIDATOR_USERNAME_MESSAGE)
from recipes.constants import (ERROR_AMOUNT_MUST_BE_POSITIVE,
                               ERROR_COOKING_TIME_LESS_1,
                               ERROR_DOUBLE_FAVORITE,
                               ERROR_DOUBLE_FOLLOW,
                               ERROR_DOUBLE_SHOPPING_CART,
                               ERROR_EMPTY_INGREDIENTS,
                               ERROR_EMPTY_TAGS,
                               ERROR_NON_UNIQUE_INGREDIENTS,
                               ERROR_NON_UNIQUE_INGREDIENT_MEASURE,
                               ERROR_NON_UNIQUE_TAGS,
                               ERROR_NO_INGREDIENTS,
                               ERROR_NO_TAGS,
                               ERROR_SELF_FOLLOW,
                               )

User = get_user_model()


class UsernameValidationMixin:
    """ Миксин для валидации username. """
    def validate_username(self, value):
        if not match(r'^[\w.@+-]+\Z', value):
            raise serializers.ValidationError(
                [REGEXVALIDATOR_USERNAME_MESSAGE],)
        return value


class UsernameAndEmailValidationMixin:
    """ Миксин для валидации username и e-mail."""
    def validate(self, data):
        if (User.objects.filter(
            email=data.get('email', '').lower()).exists()
           and not User.objects.filter(
               username=data.get('username', '')).exists()):
            raise serializers.ValidationError(
                {'email': [EMAIL_NON_UNIQUE]},)
        return data


class TagValidationMixin:
    """ Миксин для валидации slug. """
    def validate_slug(self, value):
        if not match(r'^[-a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError(
                [WRONG_SLUG_MESSAGE],)
        return value


class IngredientValidationMixin:
    """ Миксин для валидации ингредиента. """
    def validate(self, data):
        if Ingredient.objects.filter(
            name__iexact=data['name'],
            measurement_unit__iexact=data['measurement_unit']
        ).exists():
            raise serializers.ValidationError(
                [ERROR_NON_UNIQUE_INGREDIENT_MEASURE],
            )
        return data


class FollowValidationMixin:
    """ Миксин для валидации подписок. """
    def validate(self, attrs):
        request = self.context['request']
        user_is_following = request.user
        user_being_followed = attrs.get('user_being_followed')
        if user_is_following == user_being_followed:
            raise serializers.ValidationError(
                {'user_is_following': [ERROR_SELF_FOLLOW]},
            )
        if user_is_following.following.filter(
            user_being_followed=user_being_followed
        ).exists():
            raise serializers.ValidationError(
                {'user_being_followed': [ERROR_DOUBLE_FOLLOW]},
            )
        return attrs


class FavoriteValidationMixin:
    """ Миксин для валидации избранного. """
    def validate(self, attrs):
        user = self.context['request'].user
        recipe = attrs.get('recipe')
        if user.favorite_recipes.filter(
            recipe=recipe
        ).exists():
            raise serializers.ValidationError(
                {'recipe': [ERROR_DOUBLE_FAVORITE]},
            )
        return attrs


class ShoppingCartValidationMixin:
    """ Миксин для валидации корзины. """
    def validate(self, attrs):
        user = self.context['request'].user
        recipe = attrs.get('recipe')
        print(recipe.id)
        if user.shopping_cart_recipes.filter(recipe=recipe):
            raise serializers.ValidationError(
                {'recipe': [ERROR_DOUBLE_SHOPPING_CART]},
            )
        return attrs


class RecipeValidationMixin:
    """ Миксин для валидации рецепта. """
    def validate(self, data):
        ingredients = data.get('recipeingredients')
        if ingredients is None:
            raise serializers.ValidationError(
                {'ingredients': [ERROR_NO_INGREDIENTS]},
            )
        tags = data.get('tags')
        if tags is None:
            raise serializers.ValidationError(
                {'tags': [ERROR_NO_TAGS]},
            )
        return data

    def check_ingredients_positive_amount(self, ingredients):
        for ingredient in ingredients:
            if ingredient.get('amount') <= 0:
                raise serializers.ValidationError(
                    f'{ingredient.get("ingredient").name}: '
                    f'{ERROR_AMOUNT_MUST_BE_POSITIVE}',
                )

    def check_ingredients_unique_list(self, ingredients):
        unique_ingredients = [ing.get('ingredient') for ing in ingredients]
        if len(ingredients) != len(set(unique_ingredients)):
            raise serializers.ValidationError(
                [ERROR_NON_UNIQUE_INGREDIENTS],
            )

    def check_tags_unique_list(self, tags):
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                [ERROR_NON_UNIQUE_TAGS],
            )

    def validate_ingredients(self, value):
        if len(value) == 0:
            raise serializers.ValidationError(
                [ERROR_EMPTY_INGREDIENTS],
            )
        self.check_ingredients_positive_amount(value)
        self.check_ingredients_unique_list(value)
        return value

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError(
                [ERROR_COOKING_TIME_LESS_1],
            )
        return value

    def validate_tags(self, value):
        if len(value) == 0:
            raise serializers.ValidationError(
                [ERROR_EMPTY_TAGS],
            )
        self.check_tags_unique_list(value)
        return value
