from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from .constants import (REGEXVALIDATOR_USERNAME_MESSAGE,
                        REGEXVALIDATOR_USERNAME_CODE,
                        USERNAME_FIELD_LENGTH, EMAIL_FIELD_LENGTH,
                        FIRST_NAME_FIELD_LENGTH, LAST_NAME_FIELD_LENGTH,)


class User(AbstractUser):
    """ Модель пользователя. """

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    username = models.CharField(
        unique=True,
        max_length=USERNAME_FIELD_LENGTH,
        validators=(
            RegexValidator(
                regex=r'^[\w.@+-]+\Z',
                message=REGEXVALIDATOR_USERNAME_MESSAGE,
                code=REGEXVALIDATOR_USERNAME_CODE,
            ),),
        verbose_name='Имя пользователя')
    email = models.EmailField(
        unique=True,
        max_length=EMAIL_FIELD_LENGTH,
        verbose_name='Электронная почта')
    first_name = models.CharField(
        max_length=FIRST_NAME_FIELD_LENGTH,
        verbose_name='Имя')
    last_name = models.CharField(
        max_length=LAST_NAME_FIELD_LENGTH,
        verbose_name='Фамилия')
    avatar = models.ImageField(
        upload_to='users/avatars/',
        blank=True,
        null=True,
        default=None,
        verbose_name='Аватар'
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Follow(models.Model):
    """ Модель подписки. """

    # кто подписан
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follows_as_follower',
        verbose_name='Подписчик'
    )
    # на кого подписан
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follows_as_author',
        verbose_name='Автор'
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='%(app_label)s_%(class)s_unique_following'),
            models.CheckConstraint(
                check=~models.Q(
                    user=models.F('author')),
                name='%(app_label)s_%(class)s_prevent_self_follow')
        )
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return (f'{self.user.username} '
                f'подписан на {self.author.username}')
