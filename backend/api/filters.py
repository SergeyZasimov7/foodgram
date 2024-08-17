from django_filters import rest_framework as rest_framework_filter

from recipes.models import Recipe, Ingredient


class RecipeFilter(rest_framework_filter.FilterSet):
    tags = rest_framework_filter.AllValuesMultipleFilter(
        field_name='tags__slug'
    )
    is_favorited = rest_framework_filter.BooleanFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = rest_framework_filter.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    def filter_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')


class IngredientFilter(rest_framework_filter.FilterSet):
    name = rest_framework_filter.CharFilter(
        field_name='name', lookup_expr='startswith'
    )

    class Meta:
        model = Ingredient
        fields = ['name']
