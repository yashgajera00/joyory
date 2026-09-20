from django.contrib import admin
from .models import Ingredient, IngredientInteraction, Product

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'slug')
    list_filter = ('category',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(IngredientInteraction)
class IngredientInteractionAdmin(admin.ModelAdmin):
    list_display = ('ingredient_a', 'ingredient_b', 'severity', 'interaction_type')
    list_filter = ('severity', 'interaction_type')
    search_fields = ('ingredient_a__name', 'ingredient_b__name', 'message', 'recommendation')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'category', 'price', 'active_level', 'texture',
        'suitable_climate', 'routine_stage', 'created_at'
    )
    list_filter = ('category', 'active_level', 'suitable_climate', 'texture', 'routine_stage')
    search_fields = ('name', 'description', 'skin_types', 'concerns')
    filter_horizontal = ('ingredients',)
