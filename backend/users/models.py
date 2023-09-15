from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(
        max_length=254,
        unique=True,
        blank=False,
        null=False,
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        blank=False,
        null=False,
    )
    first_name = models.CharField(
        max_length=150,
        blank=False,
        null=False,
    )
    last_name = models.CharField(
        max_length=150,
        blank=False,
        null=False
    )
    password = models.CharField(
        max_length=150,
        blank=False,
        null=False,
    )

    class Meta:
        ordering = ['id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='подписчик',
        related_name='subscriber',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='subscribing',
    )

    class Meta:
        ordering = ('-id', )
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_subscription')
        ]

    def __str__(self):
        return f'{self.user.username} подписан на {self.author.username}'
