import base64

from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework import serializers

from recipes.models import (Ingredient, Recipe, RecipeIngredient,
                            RecipeFavorite, ShoppingCart, Tag)
from users.models import Follow
from .mixins import (UsernameValidationMixin, EmailValidationMixin,
                     FavoriteValidationMixin, FollowValidationMixin,
                     RecipeValidationMixin,
                     ShoppingCartValidationMixin,
                     TagValidationMixin)

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class UserBaseSerializer(EmailValidationMixin,
                         UsernameValidationMixin,
                         serializers.ModelSerializer):
    """ Базовый сериализатор для работы с пользователем. """

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar']

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if isinstance(obj, AnonymousUser):
            return False
        if not request or not request.user.is_authenticated:
            return False
        return request.user.following.filter(user_being_followed=obj).exists()


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
    recipes_count = serializers.IntegerField(read_only=True)

    class Meta(UserBaseSerializer.Meta):
        fields = UserBaseSerializer.Meta.fields + ['recipes', 'recipes_count']

    def get_recipes(self, obj):
        if hasattr(obj, 'limited_recipes'):
            recipes = obj.limited_recipes
        else:
            recipes = obj.recipes.all()
        return RecipeReducedSerializer(
            recipes,
            many=True,
            context={'request': self.context.get('request')}).data


class FollowSerializer(FollowValidationMixin, serializers.ModelSerializer):
    """ Сериализатор для работы с подписками. """

    user_being_followed = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )

    class Meta:
        model = Follow
        fields = ('user_is_following', 'user_being_followed',)
        read_only_fields = ('user_is_following',)

    def create(self, validated_data):
        validated_data['user_is_following'] = self.context.get('request').user
        return super().create(validated_data)


class IngredientSerializer(serializers.ModelSerializer):
    """ Сериализатор для работы с ингредиентами. """

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(TagValidationMixin, serializers.ModelSerializer):
    """ Сериализатор для работы с тегами. """

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """ Сериализатор для работы с ингредиентами в рецептах. """

    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all(),
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


class RecipeWriteSerializer(RecipeValidationMixin,
                            serializers.ModelSerializer):
    """ Сериализатор рецепта для записи. """

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )
    ingredients = RecipeIngredientSerializer(
        required=True,
        many=True,
        source='recipeingredients'
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'ingredients', 'name', 'image',
                  'text', 'cooking_time')
        read_only_fields = ('id', 'author')

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipeingredients')
        validated_data['author'] = self.context.get('request').user
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        for ingredient_data in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient_data['ingredient'],
                amount=ingredient_data['amount']
            )
        return recipe

    def update_ingredients(self, instance, new_ingredients):
        old_ingredients = instance.recipeingredients.all()
        old_ingredients_dict = {ri.ingredient_id: ri for ri in old_ingredients}
        new_ingredients_dict = {
            ri['ingredient'].id: ri for ri in new_ingredients
        }
        ingredients_to_remove = (set(old_ingredients_dict.keys())
                                 - set(new_ingredients_dict.keys()))
        ingredients_to_create = []
        ingredients_to_update = []
        for ingredient_id, new_value in new_ingredients_dict.items():
            if ingredient_id in old_ingredients_dict:
                old_ri = old_ingredients_dict[ingredient_id]
                if new_value['amount'] != old_ri.amount:
                    old_ri.amount = new_value['amount']
                    ingredients_to_update.append(old_ri)
            else:
                ingredients_to_create.append(RecipeIngredient(
                    recipe=instance,
                    ingredient=new_value['ingredient'],
                    amount=new_value['amount']
                ))
        RecipeIngredient.objects.filter(
            recipe=instance,
            ingredient_id__in=ingredients_to_remove
        ).delete()
        RecipeIngredient.objects.bulk_create(ingredients_to_create)
        RecipeIngredient.objects.bulk_update(ingredients_to_update,
                                             fields=('amount',))

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', None)
        ingredients_data = validated_data.pop('recipeingredients', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tags_data is not None:
            instance.tags.set(tags_data)
        if ingredients_data is not None:
            self.update_ingredients(instance, ingredients_data)
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance,
            context={'request': self.context.get('request')}
        ).data


class RecipeReadSerializer(serializers.ModelSerializer):
    """ Сериализатор для работы с расширенным рецептом. """

    tags = TagSerializer(many=True, read_only=True)
    author = UserBaseSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
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


class RecipeFavoriteSerializer(FavoriteValidationMixin,
                               serializers.ModelSerializer):
    """ Сериализатор для работы с избранным. """

    class Meta:
        model = RecipeFavorite
        fields = ('recipe',)

    def create(self, validated_data):
        validated_data['user'] = self.context.get('request').user
        return super().create(validated_data)


class RecipeShoppingCartSerializer(ShoppingCartValidationMixin,
                                   serializers.ModelSerializer):
    """ Сериализатор для работы с корзиной. """

    class Meta:
        model = ShoppingCart
        fields = ('recipe',)

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
