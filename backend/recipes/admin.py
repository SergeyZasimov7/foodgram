from django.contrib import admin

from .models import (
    Favorites,
    Ingredient,
    Recipe,
    Recipe_Ingredients,
    Recipe_Tags,
    ShoppingCart,
    Tag
)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author',)
    list_filter = ('author', 'name', 'tags__name',)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    list_filter = ('name',)


admin.site.register(Tag)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe_Ingredients)
admin.site.register(Recipe_Tags)
admin.site.register(Favorites)
admin.site.register(ShoppingCart)
