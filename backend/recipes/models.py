import random
import string

from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .constans import (
    USER_LENGTH,
    TAG_LENGTH,
    INGREDIENT_NAME_LENGTH,
    INGREDIENT_MEASUREMENT_UNIT_LENGTH,
    MAX_VALUE_VALIDATOR,
    MIN_VALUE_VALIDATOR,
    RECIPE_LENGTH,
    SHORT_LINK_LENGTH
)
from .validators import validate_username


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')
    email = models.EmailField(
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
        return f'Пользователь {self.username} ({self.email})'


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
        verbose_name='Название тега')
    slug = models.SlugField(
        max_length=TAG_LENGTH,
        unique=True,
        verbose_name='Слаг тега')

    def __str__(self):
        return f'Тег: {self.name} (slug: {self.slug})'


class Ingredient(models.Model):
    name = models.CharField(
        max_length=INGREDIENT_NAME_LENGTH,
        verbose_name='Название ингредиента')
    measurement_unit = models.CharField(
        max_length=INGREDIENT_MEASUREMENT_UNIT_LENGTH,
        verbose_name='Единица измерения ингредиента')

    class Meta:
        models.UniqueConstraint(
            fields=['name', 'measurement_unit'], name='unique_ingredient'
        )

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',
        through='RecipeTags')
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
        through='RecipeIngredients')
    name = models.CharField(
        max_length=RECIPE_LENGTH,
        verbose_name='Название рецепта')
    image = models.ImageField(
        'Изображение',
        upload_to='recipes/')
    text = models.TextField(
        verbose_name='Описание рецепта')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[
            MinValueValidator(
                MIN_VALUE_VALIDATOR,
                message='Время приготовления должно быть не менее 1 минуты.'
            ),
            MaxValueValidator(
                MAX_VALUE_VALIDATOR,
                message='Время приготовления должно быть не более 32000 минут.'
            )
        ],
        help_text='Укажите время приготовления 1 до 32000 минут.'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'),
    short_link = models.CharField(
        max_length=SHORT_LINK_LENGTH,
        blank=True,
        null=True
    )

    def generate_short_link(self):
        while True:
            short_code = ''.join(
                random.choice(
                    string.ascii_letters + string.digits
                ) for _ in range(6)
            )
            if not Recipe.objects.filter(short_link=short_code).exists():
                return short_code

    def save(self, *args, **kwargs):
        if not self.short_link:
            self.short_link = self.generate_short_link()
        super(Recipe, self).save(*args, **kwargs)

    def __str__(self):
        return (
            f'{self.name} '
            f'(Автор: {self.author}, '
            f'Время: {self.cooking_time} мин.)'
        )


class RecipeTags(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE)
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'tag'], name='recipetag_unique'
            )
        ]

    def __str__(self):
        return f'Рецепт {self.recipe} имеет тег {self.tag}'


class RecipeIngredients(models.Model):
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
        validators=[
            MinValueValidator(
                MIN_VALUE_VALIDATOR,
                message='Количество ингредиентов должно быть не меньше 1'
            ),
            MaxValueValidator(
                MAX_VALUE_VALIDATOR,
                message='Количество ингредиентов должно быть не больше 32000'
            ),
        ],
        help_text='Количество ингредиентов должно быть от 1 до 32000'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='recipeingredient_unique')]

    def __str__(self):
        return f'Рецепт {self.recipe} содержит {self.ingredient}'


class RecipeRelation(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )

    class Meta:
        abstract = True


class Favorites(RecipeRelation):

    class Meta(RecipeRelation.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'], name='userfavorites_unique')]
        default_related_name = 'favorites'

    def __str__(self):
        return f'Рецепт {self.recipe} в избранном {self.user}'


class ShoppingCart(RecipeRelation):

    class Meta(RecipeRelation.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'], name='usershoppingcart_unique')]
        default_related_name = 'shopping_cart'

    def __str__(self):
        return f'Рецепт {self.recipe} в корзине {self.user}'
