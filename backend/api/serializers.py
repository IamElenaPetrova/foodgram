from drf_extra_fields.fields import Base64ImageField

from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import UserSerializer as DjoserSerializer
from rest_framework import serializers

from recipes.models import (Ingredient, Recipe, RecipeIngredient,
                            RecipeFavorite, ShoppingCart, Tag)
from users.models import Follow
from recipes.constants import (AMOUNT_RANGE_ERROR,
                               COOKING_TIME_ERROR,
                               ERROR_ALREADY_EXISTS,
                               ERROR_AMOUNT_MUST_BE_POSITIVE,
                               ERROR_COOKING_TIME_LESS_1,
                               ERROR_DOUBLE_FOLLOW,
                               ERROR_NO_DATA,
                               ERROR_NON_UNIQUE_INGREDIENTS,
                               ERROR_NON_UNIQUE_TAGS,
                               ERROR_NO_INGREDIENTS,
                               ERROR_NO_TAGS,
                               ERROR_SELF_FOLLOW,
                               MIN_AMOUNT,
                               MAX_AMOUNT,
                               MIN_COOKING_TIME,
                               MAX_COOKING_TIME
                               )

User = get_user_model()


class UserBaseSerializer(DjoserSerializer):
    """Базовый сериализатор для работы с пользователем."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta(DjoserSerializer.Meta):
        fields = DjoserSerializer.Meta.fields + (
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and request.user.subscriptions.filter(author=obj).exists()
        )


class UserSerializerSetAndDelAvatar(serializers.ModelSerializer):
    """ Сериализатор для работы с аватаром пользователя. """

    avatar = Base64ImageField(write_only=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def to_representation(self, instance):
        request = self.context.get('request')
        if instance.avatar:
            return {
                'avatar': request.build_absolute_uri(instance.avatar.url)
            }
        return {'avatar': None}


class UserSerializerWithRecipeCount(
    UserBaseSerializer
):
    """ Сериализатор для работы расширенной версией пользователя. """

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True, default=0)

    class Meta(UserBaseSerializer.Meta):
        fields = UserBaseSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        queryset = obj.recipes.all()
        request = self.context.get('request')
        if request:
            limit = request.query_params.get('recipes_limit')
            try:
                limit = int(limit)
            except (TypeError, ValueError):
                limit = None
            if limit and limit > 0:
                queryset = queryset[:limit]
        return RecipeReducedSerializer(queryset, many=True,
                                       context=self.context).data


class FollowSerializer(serializers.ModelSerializer):
    """ Сериализатор для работы с подписками. """

    class Meta:
        model = Follow
        fields = ('user', 'author',)
        read_only_fields = ('user',)

    def validate(self, attrs):
        request = self.context['request']
        user = request.user
        author = attrs.get('author')
        if user == author:
            raise serializers.ValidationError(
                {'user': [ERROR_SELF_FOLLOW]},
            )
        if user.subscriptions.filter(
            author=author
        ).exists():
            raise serializers.ValidationError(
                {'author': [ERROR_DOUBLE_FOLLOW]},
            )
        return attrs

    def to_representation(self, instance):
        return UserSerializerWithRecipeCount(
            instance.author, context=self.context
        ).data


class IngredientSerializer(serializers.ModelSerializer):
    """ Сериализатор для работы с ингредиентами. """

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    """ Сериализатор для работы с тегами. """

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """ Сериализатор на чтение для работы с ингредиентами в рецептах. """

    id = serializers.IntegerField(
        source='ingredient.id',
        read_only=True
    )
    name = serializers.CharField(
        source='ingredient.name',
        read_only=True
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'amount', 'measurement_unit')


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов рецепта (запись)."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    amount = serializers.IntegerField(
        min_value=MIN_AMOUNT,
        max_value=MAX_AMOUNT,
        error_messages={'min_value': ERROR_AMOUNT_MUST_BE_POSITIVE,
                        'max_value': AMOUNT_RANGE_ERROR}
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeWriteSerializer(serializers.ModelSerializer):
    """ Сериализатор рецепта для записи. """

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )
    ingredients = RecipeIngredientWriteSerializer(
        required=True,
        many=True,
        source='recipeingredients'
    )
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME,
        max_value=MAX_COOKING_TIME,
        error_messages={'min_value': ERROR_COOKING_TIME_LESS_1,
                        'max_value': COOKING_TIME_ERROR}
    )
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'ingredients', 'name', 'image',
                  'text', 'cooking_time')
        read_only_fields = ('id', 'author')

    @staticmethod
    def bulk_create_ingredients(recipe, ingredients):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe, ingredient=item['ingredient'],
                amount=item['amount'])
            for item in ingredients])

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipeingredients')
        validated_data['author'] = self.context.get('request').user
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.bulk_create_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('recipeingredients', None)
        instance = super().update(instance, validated_data)
        if tags:
            instance.tags.set(tags)
        if ingredients:
            instance.recipeingredients.all().delete()
            self.bulk_create_ingredients(instance, ingredients)
        return instance

    def validate(self, data):
        errors = {}
        tags = data.get('tags')
        if not tags:
            errors['tags'] = [ERROR_NO_TAGS]
        elif len(tags) != len(set(tags)):
            errors['tags'] = [ERROR_NON_UNIQUE_TAGS]

        ingredients = data.get('recipeingredients')
        if not ingredients:
            errors['ingredients'] = [ERROR_NO_INGREDIENTS]
        else:
            unique_ingredients = [ing.get('ingredient') for ing in ingredients]
            if len(ingredients) != len(set(unique_ingredients)):
                errors['ingredients'] = [ERROR_NON_UNIQUE_INGREDIENTS]
        image = data.get('image')
        if not image:
            errors['image'] = [ERROR_NO_DATA]
        if errors:
            raise serializers.ValidationError(errors)
        return data

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class RecipeReadSerializer(serializers.ModelSerializer):
    """ Сериализатор для работы с расширенным рецептом. """

    tags = TagSerializer(many=True, read_only=True)
    author = UserBaseSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        many=True,
        source='recipeingredients'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image',
                  'text', 'cooking_time',)
        read_only_fields = ('id', 'author')

    def get_is_favorited(self, obj):
        return bool(getattr(obj, 'user_favorites', []))

    def get_is_in_shopping_cart(self, obj):
        return bool(getattr(obj, 'user_shopping_cart', []))


class RecipeReducedSerializer(serializers.ModelSerializer):
    """ Сериализатор для работы с краткой информацией о рецепте. """

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class BaseUserRecipeRelationSerializer(serializers.ModelSerializer):
    """ Базовый сериализатор для связей пользователь-рецепт.
    Родительский класс для Избранного и Корзины. """

    def validate(self, attrs):
        user = self.context['request'].user
        recipe = attrs.get('recipe')
        model = self.Meta.model
        if model.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                {'recipe': [
                    f'{model._meta.verbose_name} {ERROR_ALREADY_EXISTS}'
                ]})
        return attrs

    def to_representation(self, instance):
        return RecipeReducedSerializer(
            instance.recipe, context=self.context).data


class RecipeFavoriteSerializer(BaseUserRecipeRelationSerializer):
    """ Сериализатор для работы с избранным. """

    class Meta:
        model = RecipeFavorite
        fields = ('recipe',)


class RecipeShoppingCartSerializer(BaseUserRecipeRelationSerializer):
    """ Сериализатор для работы с корзиной. """

    class Meta:
        model = ShoppingCart
        fields = ('recipe',)
