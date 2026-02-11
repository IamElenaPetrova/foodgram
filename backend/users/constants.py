USERNAME_FIELD_LENGTH = 150
FIRST_NAME_FIELD_LENGTH = 150
LAST_NAME_FIELD_LENGTH = 150
EMAIL_FIELD_LENGTH = 150


REGEXVALIDATOR_USERNAME_MESSAGE = (
    'Предложенное имя пользователя некорректо. '
    'Допустимы только латинские буквы, цифры и знаки @/./+/-/_ .')

REGEXVALIDATOR_USERNAME_CODE = 'incorrect username'

EMAIL_NON_UNIQUE = 'Пользователь с таким email уже существует '

USERNAME_NON_UNIQUE_ERROR = 'Пользователь c таким username ' \
                            'зарегистрирован с другим email'
