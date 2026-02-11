from django.db import models
from django.contrib.auth import get_user_model

from .constants import (INGREDIENT_NAME_FIELD_LENGTH,
                        INGREDIENT_UNIT_FIELD_LENGTH,
                        RECIPE_NAME_FIELD_LENGTH,
                        TAG_NAME_FIELD_LENGTH,
                        TAG_SLUG_FIELD_LENGTH)

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
        return f'{self.name}, {self.measurement_unit}'


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
        blank=True,
        null=True,
        verbose_name='Слаг'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """ Модель рецептов. """
    name = models.CharField(
        max_length=RECIPE_NAME_FIELD_LENGTH,
        verbose_name='Название'
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        null=True,
        blank=True,
        verbose_name='Фото'
    )
    text = models.TextField('Описание')
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    cooking_time = models.PositiveSmallIntegerField('Время приготовления')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    tags = models.ManyToManyField(Tag, through='RecipeTag')
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient'
    )

    class Meta:
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class RecipeTag(models.Model):
    """ Модель тег-рецепт. """
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               verbose_name='Рецепт')
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE,
                            verbose_name='Тег')

    class Meta:
        default_related_name = 'recipetags'
        verbose_name = 'Тег для рецепта'
        verbose_name_plural = 'Теги для рецептов'
        constraints = (
            models.UniqueConstraint(
                fields=('tag', 'recipe'),
                name='%(app_label)s_%(class)s_unique_tag_and_recipe'),
        )

    def __str__(self):
        return f'{self.recipe.name} - {self.tag.name}'


class RecipeIngredient(models.Model):
    """ Модель рецепт-ингредиент. """
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               verbose_name='Рецепт')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                   verbose_name='Ингредиент')
    amount = models.IntegerField('Количество')

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
        return f'{self.recipe.name} - {self.ingredient.name} - {self.amount}'


class RecipeFavorite(models.Model):
    """ Модель рецепт в избранном. """
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name='У кого в избранном'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        default_related_name = 'favorite_recipes'
        verbose_name = 'Рецепт в избранном'
        verbose_name_plural = 'Рецепты в избранном'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='%(app_label)s_%(class)s_'
                'unique_user_and_favourite_recipe'
            ),
        )

    def __str__(self):
        return (f'{self.recipe.name} в избранном у'
                f' пользователя {self.user.username}')


class ShoppingCart(models.Model):
    """ Модель корзина. """
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name='Чей список покупок'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        default_related_name = 'shopping_cart_recipes'
        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списке покупок'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='%(app_label)s_%(class)s_unique_user_and_recipe'
                '_in_shopping_cart'),
        )

    def __str__(self):
        return (f'{self.recipe.name} в корзине у пользователя '
                f'{self.user.username}')
