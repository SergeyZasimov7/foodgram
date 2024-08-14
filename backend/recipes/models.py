from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models

from .constans import (
    USER_LENGTH,
    EMAIL_LENGTH,
    TAG_LENGTH,
    INGREDIENT_NAME_LENGTH,
    INGREDIENT_MEASUREMENT_UNIT_LENGTH,
    VALUE_VALIDATOR,
    RECIPE_LENGTH
)
from .validators import validate_username


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')
    email = models.EmailField(
        max_length=EMAIL_LENGTH,
        unique=True,
        verbose_name='Электронная почта')
    username = models.CharField(
        max_length=USER_LENGTH,
        unique=True,
        verbose_name='Логин пользователя',
        validators=[validate_username])
    first_name = models.CharField(
        max_length=USER_LENGTH,
        verbose_name='Имя пользователя')
    last_name = models.CharField(
        max_length=USER_LENGTH,
        verbose_name='Фамилия пользователя')
    password = models.CharField(
        max_length=USER_LENGTH,
        verbose_name='Пароль пользователя')
    avatar = models.ImageField(
        verbose_name='Аватарка',
        blank=True,
        null=True,
        upload_to='avatars/'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscriptions(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='subscriptions_unique')]

    def __str__(self):
        return f'Подписка {self.user} на {self.author}'


class Tag(models.Model):
    name = models.CharField(
        max_length=TAG_LENGTH,
        unique=True,
        verbose_name='Название тега')
    color = models.CharField(
        max_length=TAG_LENGTH,
        unique=True,
        verbose_name='Цвет тега')
    slug = models.SlugField(
        max_length=TAG_LENGTH,
        unique=True,
        verbose_name='Слаг тега')

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=INGREDIENT_NAME_LENGTH,
        unique=True,
        verbose_name='Название ингредиента')
    measurement_unit = models.CharField(
        max_length=INGREDIENT_MEASUREMENT_UNIT_LENGTH,
        verbose_name='Единица измерения ингредиента')

    class Meta:
        unique_together = ('name', 'measurement_unit',)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',
        through='Recipe_Tags')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта',
        default=None,
        null=True)
    ingredients = models.ManyToManyField(
        Ingredient,
        related_name='recipes',
        verbose_name='Ингредиенты',
        through='Recipe_Ingredients')
    name = models.CharField(
        max_length=RECIPE_LENGTH,
        verbose_name='Название рецепта')
    image = models.ImageField(
        'Изображение',
        upload_to='recipes/')
    text = models.TextField(
        verbose_name='Описание рецепта')
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[MinValueValidator(VALUE_VALIDATOR)]
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации')

    class Meta:
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class Recipe_Tags(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE)
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['recipe', 'tag'], name='recipetag_unique')
        ]

    def __str__(self):
        return f'Рецепт {self.recipe} имеет тег {self.tag}'


class Recipe_Ingredients(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_list',
        verbose_name='Рецепт')
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe',
        verbose_name='Ингредиент')
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(VALUE_VALIDATOR)]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='recipeingredient_unique')]

    def __str__(self):
        return f'Рецепт {self.recipe} содержит {self.ingredient}'


class Favorites(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_favorites',
        verbose_name='Рецепт')
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'], name='userfavorites_unique')]

    def __str__(self):
        return f'Рецепт {self.recipe} в избранном {self.user}'


class ShoppingCart(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт')
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'], name='usershoppingcart_unique')]

    def __str__(self):
        return f'Рецепт {self.recipe} в корзине {self.user}'
