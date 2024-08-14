import base64
import uuid

from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import F
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.serializers import ModelSerializer, SerializerMethodField


from recipes.models import (
    Ingredient,
    Recipe,
    Recipe_Ingredients,
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
        fields = ('id', 'name', 'measurement_unit',)


class CustomUserSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(read_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    is_subscribed = serializers.SerializerMethodField(default=False)
    avatar = serializers.SerializerMethodField(default=None)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.subscribers.filter(id=request.user.id).exists()
        return False

    def get_avatar(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class AvatarBase64Field(serializers.ImageField):
    def to_internal_value(self, data):
        try:
            format, img_str = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(img_str), name=f'{uuid.uuid4()}.{ext}'
            )
        except ValueError:
            raise serializers.ValidationError('fgds')
        return super().to_internal_value(data)


class UserAvatarSerializer(ModelSerializer):
    avatar = AvatarBase64Field()

    class Meta:
        model = User
        fields = ('avatar',)

    def update(self, instance, validated_data):
        avatar = validated_data.get('avatar')
        instance.avatar = avatar
        instance.save()
        return instance


class RecipeSerializer(ModelSerializer):
    tags = TagSerializer(read_only=True, many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = SerializerMethodField()
    image = Base64ImageField()
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')
        read_only_fields = ('is_favorited', 'is_in_shopping_cart',)

    def get_ingredients(self, obj):
        recipe = obj
        ingredients = recipe.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('recipe__amount'),)
        return ingredients

    def get_is_favorited(self, obj):
        user = self.context.get('view').request.user
        if user.is_authenticated:
            return user.favorites.filter(recipe=obj).exists()
        else:
            return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('view').request.user
        if user.is_authenticated:
            return user.shopping_cart.filter(recipe=obj).exists()
        else:
            return False

    def validate(self, data):
        if not data.get('image'):
            raise ValidationError(
                {'image': 'Необходимо загрузить изображение.'}
            )

        tags_ids = self.initial_data.get('tags')
        if not tags_ids:
            raise ValidationError('Необходимо указать хотя бы один тег')
        for tag_id in tags_ids:
            try:
                tag_id = int(tag_id)
                Tag.objects.get(pk=tag_id)
            except (ObjectDoesNotExist, ValueError):
                raise ValidationError(
                    {'tags': f"Тег с ID {tag_id} не найден."}
                )

        unique_tag_ids = set(tags_ids)
        if len(unique_tag_ids) != len(tags_ids):
            raise ValidationError({'tags': 'Повторяющиеся теги в списке.'})

        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise ValidationError('Необходимо указать хотя бы один ингредиент')
        for ingredient in ingredients:
            try:
                ingredient['id'] = int(ingredient['id'])
                Ingredient.objects.get(pk=ingredient['id'])
            except (ObjectDoesNotExist, ValueError):
                raise ValidationError(
                    {
                        'ingredients':
                        f"Ингредиент с ID {ingredient['id']} не найден."
                    }
                )

        unique_ingredient_ids = set(
            [ingredient['id'] for ingredient in ingredients]
        )
        if len(unique_ingredient_ids) != len(ingredients):
            raise ValidationError(
                {'ingredients': 'Повторяющиеся ингредиенты в списке.'}
            )

        valid_ingredients = {}
        for ingredient in ingredients:
            valid_ingredients[ingredient['id']] = int(ingredient['amount'])
            if int(ingredient['amount']) <= 0:
                raise ValidationError(
                    'Количество ингредиента должно быть больше нуля')

        ingredient_objects = Ingredient.objects.filter(
            pk__in=valid_ingredients
        )

        for ingredient_object in ingredient_objects:
            valid_ingredients[ingredient_object.pk] = (
                ingredient_object, valid_ingredients[ingredient_object.pk])

        data.update(
            {'tags': Tag.objects.filter(id__in=tags_ids),
             'ingredients': valid_ingredients,
             'author': self.context.get('request').user}
        )
        return data

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        Recipe_Ingredients.objects.bulk_create(
            [Recipe_Ingredients(
                ingredient=ingredient_data,
                recipe=recipe,
                amount=amount
            ) for ingredient_data, amount in ingredients.values()])
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        if not self.context['request'].user.is_staff and \
                self.context['request'].user != instance.author:
            raise PermissionDenied(
                "Изменять рецепт может только автором или администратором."
            )
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)
        instance.tags.clear()
        instance.tags.set(tags)
        instance.ingredients.clear()
        Recipe_Ingredients.objects.bulk_create(
            [Recipe_Ingredients(
                ingredient=ingredient_data,
                recipe=instance,
                amount=amount
            ) for ingredient_data, amount in ingredients.values()])
        instance.save()
        return instance


class SpecialRecipeSerializer(ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionsSerializer(CustomUserSerializer):
    recipes = SpecialRecipeSerializer(many=True, read_only=True)
    recipes_count = SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')

    def validate(self, data):
        author = self.instance
        user = self.context.get('request').user
        if Subscriptions.objects.filter(user=user, author=author).exists():
            raise ValidationError(
                'Нельзя подписаться на автора дважды'
            )
        if user == author:
            raise ValidationError(
                'Нельзя подписаться на самого себя'
            )
        return data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        user = self.context.get('view').request.user
        value = self.context.get('recipes_limit')
        if user.is_authenticated:
            return obj.recipes.all()[:value] if value else obj.recipes.all()
        else:
            return obj.recipes.all()
