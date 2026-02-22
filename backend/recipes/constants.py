TAG_NAME_FIELD_LENGTH = 32
TAG_SLUG_FIELD_LENGTH = 32

INGREDIENT_NAME_FIELD_LENGTH = 128
INGREDIENT_UNIT_FIELD_LENGTH = 64

RECIPE_NAME_FIELD_LENGTH = 256

MAX_STR_LENGTH = 20

MIN_COOKING_TIME = 1
MAX_COOKING_TIME = 2880

MIN_AMOUNT = 1
MAX_AMOUNT = 1000

COOKING_TIME_ERROR = ('Время приготовления должно быть '
                      'от 1 до 2880 минут(48 часов)')

AMOUNT_RANGE_ERROR = 'Количество должно быть от 1 до 10000'

ERROR_ALREADY_EXISTS = 'уже существует.'

WRONG_SLUG_MESSAGE = (
    'Предложенный слаг некорректен. '
    'Допустимы только латинские буквы, цифры, дефисы и подчеркивания.')

ERROR_NON_UNIQUE_INGREDIENT_MEASURE = (
    'Ингредиент с таким названием и'
    ' единицей измерения уже существует.'
)

ERROR_SELF_FOLLOW = (
    'Невозможно оформить подписку на самого себя!'
)

ERROR_DOUBLE_FOLLOW = (
    'Вы уже подписаны на этого пользователя!'
)

ERROR_NO_FOLLOW = (
    'Вы не подписаны на этого пользователя'
)

ERROR_DOUBLE_FAVORITE = (
    'Этот рецепт уже добавлен в избранное'
)

ERROR_NO_RECIPE_FOUND = (
    'Рецепт не найден'
)

ERROR_NO_RECIPE_IN_FAVORITE = (
    'Рецепт не найден в избранном'
)

ERROR_DOUBLE_SHOPPING_CART = (
    'Этот рецепт уже добавлен в корзину'
)

ERROR_NO_RECIPE_IN_SHOPPING_CART = (
    'Рецепт не найден в корзине'
)

ERROR_EMPTY_SHOPPING_CART = (
    'Корзина пуста'
)

ERROR_EMPTY_TAGS = (
    'Переданы пустые теги'
)

ERROR_COOKING_TIME_LESS_1 = (
    'Время приготовления не может быть меньше 1'
)

ERROR_EMPTY_INGREDIENTS = (
    'Переданы пустые ингредиенты'
)

ERROR_NON_UNIQUE_TAGS = (
    'Теги не уникальны'
)

ERROR_NON_UNIQUE_INGREDIENTS = (
    'Ингредиенты не уникальны'
)

ERROR_NO_INGREDIENTS = (
    'Ингредиенты обязательны'
)

ERROR_NO_TAGS = (
    'Тэги обязательны'
)

ERROR_AMOUNT_MUST_BE_POSITIVE = (
    'Количество должно быть больше 0'
)

ERROR_NO_DATA = (
    'Отсутствует обязательное поле'
)

ERROR_AVATAR_IS_NOT_FOUND = (
    'Аватар не найден'
)
