from rest_framework import serializers
from django.db import models
from .models import Ingredient, IngredientInteraction, Product

class IngredientSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'slug', 'category', 'category_display', 'description']

class IngredientInteractionSerializer(serializers.ModelSerializer):
    ingredient_a_name = serializers.CharField(source='ingredient_a.name', read_only=True)
    ingredient_b_name = serializers.CharField(source='ingredient_b.name', read_only=True)

    class Meta:
        model = IngredientInteraction
        fields = [
            'id', 'ingredient_a', 'ingredient_a_name', 'ingredient_b', 'ingredient_b_name',
            'severity', 'interaction_type', 'message', 'recommendation'
        ]

class ProductSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    texture_display = serializers.CharField(source='get_texture_display', read_only=True)
    climate_display = serializers.CharField(source='get_suitable_climate_display', read_only=True)
    hydration_display = serializers.CharField(source='get_hydration_level_display', read_only=True)
    active_display = serializers.CharField(source='get_active_level_display', read_only=True)
    routine_stage_display = serializers.CharField(source='get_routine_stage_display', read_only=True)
    image_url = serializers.CharField(source='effective_image_url', read_only=True)
    ingredients = IngredientSerializer(many=True, read_only=True)
    known_interactions = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'brand', 'category', 'category_display', 'price', 'description',
            'image_url',
            'texture', 'texture_display', 'suitable_climate', 'climate_display',
            'hydration_level', 'hydration_display', 'active_level', 'active_display',
            'skin_types', 'concerns', 'routine_stage', 'routine_stage_display',
            'usage_frequency', 'time_of_day', 'typical_duration_days', 'ingredients',
            'known_interactions', 'created_at'
        ]

    def get_known_interactions(self, obj):
        ing_ids = obj.ingredients.values_list('id', flat=True)
        if not ing_ids:
            return []
        interactions = IngredientInteraction.objects.filter(
            models.Q(ingredient_a_id__in=ing_ids) | models.Q(ingredient_b_id__in=ing_ids)
        ).select_related('ingredient_a', 'ingredient_b')
        return IngredientInteractionSerializer(interactions, many=True).data
