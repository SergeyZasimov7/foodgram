from django_filters import rest_framework as rest_framework_filter

from recipes.models import Recipe, User


class RecipeFilter(rest_framework_filter.FilterSet):
    author = rest_framework_filter.ModelChoiceFilter(
        queryset=User.objects.all()
    )
    tags = rest_framework_filter.AllValuesMultipleFilter(
        field_name='tags__slug'
    )
    is_favorited = rest_framework_filter.BooleanFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = rest_framework_filter.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )
    recipes_limit = rest_framework_filter.NumberFilter(
        method='filter_recipes_limit',
        label='Количество рецептов',
    )

    def filter_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(in_favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset

    def filter_recipes_limit(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(author_id__user=self.request.user)
        return queryset

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')


class UserFilter(rest_framework_filter.FilterSet):
    recipes_limit = rest_framework_filter.NumberFilter(
        method='filter_recipes_limit',
        label='Количество рецептов',
    )

    def filter_recipes_limit(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated:
            author_ids = user.subscriptions.values_list('author_id', flat=True)
            return queryset.filter(id__in=author_ids)[:value]
        return queryset

    class Meta:
        model = User
        fields = ('recipes_limit',)
