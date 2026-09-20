from django.contrib import admin
from .models import Routine, RoutineStep, RoutineProgress, RoutineDeliveryItem

class RoutineStepInline(admin.TabularInline):
    model = RoutineStep
    extra = 0

class RoutineDeliveryItemInline(admin.TabularInline):
    model = RoutineDeliveryItem
    extra = 0

@admin.register(Routine)
class RoutineAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'status', 'current_stage', 'progress_percentage', 'created_at')
    list_filter = ('status',)
    search_fields = ('name', 'session_id', 'user__username')
    inlines = [RoutineStepInline, RoutineDeliveryItemInline]

@admin.register(RoutineStep)
class RoutineStepAdmin(admin.ModelAdmin):
    list_display = ('id', 'routine', 'product', 'stage_number', 'stage_name', 'frequency', 'time_of_day', 'completed')
    list_filter = ('stage_number', 'completed', 'time_of_day')
    search_fields = ('product__name', 'routine__name')

@admin.register(RoutineProgress)
class RoutineProgressAdmin(admin.ModelAdmin):
    list_display = ('id', 'routine_step', 'date', 'completed', 'created_at')
    list_filter = ('completed', 'date')
    search_fields = ('routine_step__product__name', 'notes')

@admin.register(RoutineDeliveryItem)
class RoutineDeliveryItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'routine', 'product', 'quantity', 'suggested_reorder_date', 'frequency_weeks', 'active')
    list_filter = ('active', 'frequency_weeks')
    search_fields = ('product__name', 'routine__name')
