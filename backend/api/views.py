from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .filters import RecipeFilter, UserFilter
from .pagination import Pagination
from .permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly
from .serializers import (
    CustomUserSerializer,
    IngredientSerializer,
    RecipeSerializer,
    SpecialRecipeSerializer,
    SubscriptionsSerializer,
    TagSerializer,
    UserAvatarSerializer
)
from recipes.models import (
    Favorites,
    Ingredient,
    Recipe,
    ShoppingCart,
    Subscriptions,
    Tag,
    User
)


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = Pagination
    permission_classes = (IsAuthorOrReadOnly | IsAdminOrReadOnly,)
    serializer_class = RecipeSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def destroy(self, request, pk=None):
        recipe = self.get_object()
        if request.user != recipe.author and not request.user.is_staff:
            return Response(
                {"detail": "У вас нет прав на удаление этого рецепта."},
                status=status.HTTP_403_FORBIDDEN
            )

        recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            if Favorites.objects.filter(
                user=request.user, recipe=recipe
            ).exists():
                return Response(
                    {'detail': 'Recipe already in favorites'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorites.objects.create(user=request.user, recipe=recipe)
            serializer = SpecialRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        favorite = Favorites.objects.filter(user=request.user, recipe__id=pk)
        if favorite.exists():
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=request.user,
                                           recipe=recipe).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            serializer = SpecialRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        cart = ShoppingCart.objects.filter(user=request.user, recipe__id=pk)
        if cart.exists():
            cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False,
            methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        if not user.shopping_cart.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        ingredients = Ingredient.objects.filter(
            recipe__recipe__shopping_cart__user=user).values(
            'name',
            'measurement_unit').annotate(amount=Sum('recipe__amount'))
        shopping_list = ['Список покупок.']
        for ingredient in ingredients:
            shopping_list += [
                f'{ingredient["name"]}'
                f'({ingredient["measurement_unit"]}):'
                f'{ingredient["amount"]}']
        filename = f'{user.username}_shopping_list.txt'
        result_list = '\n'.join(shopping_list)
        response = HttpResponse(result_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def get_link(self, request, pk):
        recipe = self.get_object()
        link = f"http://127.0.0.1:8000/api/recipes/{recipe.id}/"
        return Response({'short-link': link})


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer

    def list(self, request):
        name = request.query_params.get('name')
        if name:
            queryset = self.get_queryset().filter(name__startswith=name)
        else:
            queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = Pagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = UserFilter

    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated()]
        elif self.action == 'list':
            return [AllowAny()]
        return super().get_permissions()

    @action(
            detail=False,
            methods=['get'],
            url_path='me',
            permission_classes=[IsAuthenticated]
        )
    def me(self, request):
        serializer = CustomUserSerializer(
            request.user,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, **kwargs):
        user = request.user
        author = get_object_or_404(User, id=self.kwargs.get('id'))
        if request.method == 'POST':
            serializer = SubscriptionsSerializer(author,
                                                 data=request.data,
                                                 context={'request': request})
            serializer.is_valid(raise_exception=True)
            Subscriptions.objects.create(user=user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if Subscriptions.objects.filter(user=user, author=author).exists():
            subscription = get_object_or_404(
                Subscriptions,
                user=user,
                author=author
            )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {'detail': 'Подписки не существует'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False,
            methods=['get'])
    def subscriptions(self, request):
        user = request.user
        subscribers = User.objects.filter(subscribers__user=user)
        pages = self.paginate_queryset(subscribers)
        serializer = SubscriptionsSerializer(
            pages,
            many=True,
            context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(methods=['put', 'delete'], detail=False, url_path='me/avatar',
            permission_classes=[IsAuthenticated])
    def manage_avatar(self, request):
        user = self.request.user
        if request.method == 'PUT':
            if 'avatar' not in request.data:
                return Response(
                    {'detail': 'Отсутствует поле "avatar"'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = UserAvatarSerializer(
                user,
                data=request.data,
                partial=True
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(
                    {'avatar': user.avatar.url},
                    status=status.HTTP_200_OK
                )
            return Response(
                serializer.error,
                status=status.HTTP_400_BAD_REQUEST
            )
        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete()
                user.avatar = None
                user.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_400_BAD_REQUEST)
