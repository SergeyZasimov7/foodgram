import base64
import uuid

from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import F
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer, SerializerMethodField


from recipes.models import (
    Ingredient,
    Favorites,
    Recipe,
    RecipeIngredients,
    ShoppingCart,
    Subscriptions,
    Tag,
    User
)


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(default=False)

    class Meta:
        model = User
        fields = (
            'id',
            'username', 
            'first_name', 
            'last_name',
            'email',
            'is_subscribed',
            'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and obj:
            return obj.subscribers.filter(id=request.user.id).exists()
        return False


class AvatarBase64Field(serializers.ImageField):
    def to_internal_value(self, data):
        try:
            format, img_str = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(img_str), name=f'{uuid.uuid4()}.{ext}'
            )
        except ValueError:
            raise serializers.ValidationError('Неверный формат данных')
        return super().to_internal_value(data)


class UserAvatarSerializer(ModelSerializer):
    avatar = AvatarBase64Field()

    def validate(self, data):
        if 'avatar' not in data:
            raise serializers.ValidationError('Отсутствует поле "avatar"')
        return data

    class Meta:
        model = User
        fields = ('avatar',)


class RecipeSerializer(ModelSerializer):
    tags = TagSerializer(read_only=True, many=True)
    author = UserSerializer(read_only=True)
    ingredients = SerializerMethodField()
    image = Base64ImageField()
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')
        read_only_fields = ('is_favorited', 'is_in_shopping_cart')

    def get_ingredients(self, obj):
        recipe = obj
        ingredients = recipe.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('recipe__amount'),
        )
        return ingredients

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and obj:
            return obj.favorites.filter(id=request.user.id).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and obj:
            return obj.shopping_cart.filter(id=request.user.id).exists()
        return False


class RecipeCreateSerializer(ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    author = UserSerializer(read_only=True)
    ingredients = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        many=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'name', 'image', 'text',
            'cooking_time'
        )

    def validate(self, data):
        if not data.get('image'):
            raise ValidationError(
                {'image': 'Необходимо загрузить изображение.'}
            )
        tags_ids = self.initial_data.get('tags')
        if not tags_ids:
            raise ValidationError('Необходимо указать хотя бы один тег')
        unique_tag_ids = set(tags_ids)
        if len(unique_tag_ids) != len(tags_ids):
            raise ValidationError({'tags': 'Повторяющиеся теги в списке.'})
        return data

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        self._set_tags_and_ingredients(recipe, tags, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)
        self._set_tags_and_ingredients(instance, tags, ingredients)
        return instance

    def _set_tags_and_ingredients(self, recipe, tags, ingredients):
        recipe.tags.set(tags)
        recipe.ingredients.clear()
        RecipeIngredients.objects.bulk_create(
            [RecipeIngredients(
                ingredient=ingredient_data,
                recipe=recipe,
                amount=amount
            ) for ingredient_data, amount in ingredients.values()])

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data


class SpecialRecipeSerializer(ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscriptions
        fields = ('user', 'author')

    def validate(self, data):
        user = data['user']
        author = data['author']
        if Subscriptions.objects.filter(user=user, author=author).exists():
            raise ValidationError(
                'Нельзя подписаться на автора дважды'
            )
        if user == author:
            raise ValidationError(
                'Нельзя подписаться на самого себя'
            )
        return data

    def to_representation(self, instance):
        return UserSubscriptionSerializer(instance.author).data


class UserSubscriptionSerializer(serializers.ModelSerializer):
    recipes = SpecialRecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )
        read_only_fields = (
            'username',
            'first_name',
            'last_name',
            'email',
        )

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        user = self.context.get('request').user
        recipes_limit = self.context.get('recipes_limit')
        if user.is_authenticated:
            try:
                recipes_limit = int(recipes_limit)
            except ValueError:
                recipes_limit = None
            return (
                obj.recipes.all()[:recipes_limit]
                if recipes_limit
                else obj.recipes.all()
            )
        else:
            return obj.recipes.all()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and obj:
            return Subscriptions.objects.filter(user=request.user, author=obj).exists()
        return False


class FavoritesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorites
        fields = ('user', 'recipe')

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']
        if Favorites.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError('Рецепт уже в избранном')
        return data

    def to_representation(self, instance):
        return SpecialRecipeSerializer(instance.recipe).data

class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError('Рецепт уже в корзине покупок')
        return data

    def to_representation(self, instance):
        return SpecialRecipeSerializer(instance.recipe).data