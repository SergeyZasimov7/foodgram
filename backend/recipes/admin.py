from django.contrib import admin

from .models import (Favorites, Ingredient, Recipe, RecipeIngredients,
                     RecipeTags, ShoppingCart, Tag)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredients
    extra = 1
    min_num = 1
    autocomplete_fields = ['ingredient']


class RecipeTagInline(admin.TabularInline):
    model = RecipeTags
    extra = 1
    min_num = 1
    autocomplete_fields = ['tag']


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author',)
    list_filter = ('author', 'name', 'tags__name',)
    inlines = [RecipeIngredientInline, RecipeTagInline]


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    list_filter = ('name',)
    search_fields = ['name']


class TagAdmin(admin.ModelAdmin):
    search_fields = ['name']


admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(RecipeIngredients)
admin.site.register(RecipeTags)
admin.site.register(Favorites)
admin.site.register(ShoppingCart)
