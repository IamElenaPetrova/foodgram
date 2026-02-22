from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

from .constants import (AMOUNT_RANGE_ERROR,
                        ERROR_AMOUNT_MUST_BE_POSITIVE,
                        ERROR_COOKING_TIME_LESS_1,
                        INGREDIENT_NAME_FIELD_LENGTH,
                        INGREDIENT_UNIT_FIELD_LENGTH,
                        COOKING_TIME_ERROR,
                        MIN_AMOUNT,
                        MIN_COOKING_TIME,
                        MAX_AMOUNT,
                        MAX_COOKING_TIME,
                        MAX_STR_LENGTH,
                        RECIPE_NAME_FIELD_LENGTH,
                        TAG_NAME_FIELD_LENGTH,
                        TAG_SLUG_FIELD_LENGTH)
from .utils import truncate

User = get_user_model()


class Ingredient(models.Model):
    """ Модель ингредиентов. """

    name = models.CharField(
        max_length=INGREDIENT_NAME_FIELD_LENGTH,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=INGREDIENT_UNIT_FIELD_LENGTH,
        verbose_name='Единица измерения'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='%(app_label)s_%(class)s_unique_ingredient'
            ),
        )

    def __str__(self):
        return f'{truncate(self.name)}, {truncate(self.measurement_unit)}'


class Tag(models.Model):
    """ Модель тегов. """

    name = models.CharField(
        max_length=TAG_NAME_FIELD_LENGTH,
        unique=True,
        verbose_name='Название'
    )

    slug = models.SlugField(
        max_length=TAG_SLUG_FIELD_LENGTH,
        unique=True,
        verbose_name='Слаг'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return truncate(self.name)


class Recipe(models.Model):
    """ Модель рецептов. """

    name = models.CharField(
        max_length=RECIPE_NAME_FIELD_LENGTH,
        verbose_name='Название'
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Фото'
    )
    text = models.TextField('Описание')
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=[
            MinValueValidator(MIN_COOKING_TIME,
                              message=ERROR_COOKING_TIME_LESS_1),
            MaxValueValidator(MAX_COOKING_TIME,
                              message=COOKING_TIME_ERROR)
        ])
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        related_name='recipes'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        through='RecipeIngredient'
    )

    class Meta:
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return truncate(self.name)


class RecipeIngredient(models.Model):
    """ Модель рецепт-ингредиент. """

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               verbose_name='Рецепт')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                   verbose_name='Ингредиент')
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[
            MinValueValidator(MIN_AMOUNT,
                              message=ERROR_AMOUNT_MUST_BE_POSITIVE),
            MaxValueValidator(MAX_AMOUNT,
                              message=AMOUNT_RANGE_ERROR)
        ])

    class Meta:
        default_related_name = 'recipeingredients'
        verbose_name = 'Ингредиенты для рецепта'
        verbose_name_plural = 'Ингредиенты для рецептов'
        constraints = (
            models.UniqueConstraint(
                fields=('ingredient', 'recipe'),
                name='%(app_label)s_%(class)s_unique_ingredient_and_recipe'),
        )

    def __str__(self):
        half_length = MAX_STR_LENGTH // 2
        return (
            f'{truncate(self.recipe.name, half_length)} - '
            f'{truncate(self.ingredient.name, half_length)} - '
            f'{self.amount}'
        )


class UserRecipeBase(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='%(app_label)s_%(class)s_unique_user_recipe'
            ),
        )

    def __str__(self):
        half_length = MAX_STR_LENGTH // 2
        return (
            f'{truncate(self.recipe.name, half_length)} — '
            f'{self._meta.verbose_name} — '
            f'{truncate(self.user.username, half_length)}'
        )


class RecipeFavorite(UserRecipeBase):
    """ Модель рецепт в избранном. """

    class Meta(UserRecipeBase.Meta):
        default_related_name = 'favorite_recipes'
        verbose_name = 'Рецепт в избранном'
        verbose_name_plural = 'Рецепты в избранном'


class ShoppingCart(UserRecipeBase):
    """ Модель корзина. """

    class Meta(UserRecipeBase.Meta):
        default_related_name = 'shopping_cart_recipes'
        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списке покупок'
