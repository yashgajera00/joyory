from rest_framework import serializers
from products.serializers import ProductSerializer
from .models import Routine, RoutineStep, RoutineProgress, RoutineDeliveryItem, DailySkinFeedback
from services.routine_engine import get_routine_staged_roadmap, get_routine_adaptive_guidance

class RoutineProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoutineProgress
        fields = ['id', 'routine_step', 'date', 'session', 'completed', 'notes', 'created_at']

class DailySkinFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailySkinFeedback
        fields = ['id', 'routine', 'date', 'skin_feel', 'notes', 'created_at']

class RoutineStepSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    progress_entries = RoutineProgressSerializer(many=True, read_only=True)

    class Meta:
        model = RoutineStep
        fields = [
            'id', 'routine', 'product', 'stage_number', 'stage_name',
            'week_start', 'week_end', 'frequency', 'time_of_day',
            'order', 'completed', 'morning_completed', 'evening_completed', 'progress_entries'
        ]


class RoutineDeliveryItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=8, decimal_places=2, read_only=True)
    product_image_url = serializers.CharField(source='product.effective_image_url', read_only=True)

    class Meta:
        model = RoutineDeliveryItem
        fields = [
            'id', 'product', 'product_name', 'product_price', 'product_image_url', 'quantity',
            'suggested_reorder_date', 'frequency_weeks', 'active', 'reason',
            'status', 'tracking_number'
        ]

class RoutineSerializer(serializers.ModelSerializer):
    steps = RoutineStepSerializer(many=True, read_only=True)
    delivery_items = RoutineDeliveryItemSerializer(many=True, read_only=True)
    progress_percentage = serializers.FloatField(read_only=True)
    current_stage = serializers.IntegerField(read_only=True)
    total_steps_count = serializers.IntegerField(read_only=True)
    completed_steps_count = serializers.IntegerField(read_only=True)
    stages = serializers.SerializerMethodField()
    journey_summary = serializers.SerializerMethodField()
    adaptive_guidance = serializers.SerializerMethodField()

    class Meta:
        model = Routine
        fields = [
            'id', 'name', 'status', 'auto_reorder_enabled', 'auto_reordered',
            'auto_reorder_date', 'auto_reorder_order_id', 'created_at',
            'total_steps_count', 'completed_steps_count', 'progress_percentage', 'current_stage',
            'steps', 'delivery_items', 'stages', 'journey_summary', 'adaptive_guidance'
        ]

    def get_stages(self, obj):
        try:
            roadmap = get_routine_staged_roadmap(obj)
            return roadmap.get('stages', [])
        except Exception:
            return []

    def get_journey_summary(self, obj):
        try:
            roadmap = get_routine_staged_roadmap(obj)
            return roadmap.get('journey_summary', {})
        except Exception:
            return {}

    def get_adaptive_guidance(self, obj):
        try:
            return get_routine_adaptive_guidance(obj)
        except Exception:
            return {}

class GenerateRoutineInputSerializer(serializers.Serializer):
    product_ids = serializers.ListField(
        child=serializers.IntegerField(), min_length=1, required=True
    )
    name = serializers.CharField(required=False, default="My Joyory Routine")
    session_id = serializers.CharField(required=False, allow_blank=True, default='')

class CompleteStepInputSerializer(serializers.Serializer):
    step_id = serializers.IntegerField(required=True)
    date = serializers.DateField(required=False)
    session = serializers.CharField(required=False, default='all') # 'morning', 'evening', 'all'
    completed = serializers.BooleanField(required=False, default=True)
    notes = serializers.CharField(required=False, allow_blank=True, default='')


class DailySkinFeedbackInputSerializer(serializers.Serializer):
    skin_feel = serializers.ChoiceField(choices=['comfortable', 'dry', 'irritated'], required=True)
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    date = serializers.DateField(required=False)

