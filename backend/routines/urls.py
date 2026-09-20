from django.urls import path
from .views import (
    GenerateRoutineView,
    RoutineListView,
    RoutineDetailView,
    CompleteStepView,
    RoutineProgressView,
    RoutineDeliveryScheduleView,
    ToggleAutoReorderView,
    ToggleDeliveryItemAutoReorderView,
    CompleteAllStepsView,
    DailySkinFeedbackView,
    DeleteRoutineStepView
)

urlpatterns = [
    path('generate/', GenerateRoutineView.as_view(), name='routine_generate'),
    path('', RoutineListView.as_view(), name='routine_list'),
    path('<int:id>/', RoutineDetailView.as_view(), name='routine_detail'),
    path('<int:id>/steps/<int:step_id>/delete/', DeleteRoutineStepView.as_view(), name='routine_delete_step'),
    path('<int:id>/complete-step/', CompleteStepView.as_view(), name='routine_complete_step'),
    path('<int:id>/complete-all/', CompleteAllStepsView.as_view(), name='routine_complete_all_steps'),
    path('<int:id>/toggle-auto-reorder/', ToggleAutoReorderView.as_view(), name='routine_toggle_auto_reorder'),
    path('<int:id>/progress/', RoutineProgressView.as_view(), name='routine_progress'),
    path('<int:id>/feedback/', DailySkinFeedbackView.as_view(), name='routine_feedback'),
    path('<int:id>/delivery-schedule/', RoutineDeliveryScheduleView.as_view(), name='routine_delivery_schedule'),
    path('delivery-items/<int:item_id>/toggle/', ToggleDeliveryItemAutoReorderView.as_view(), name='routine_delivery_item_toggle'),
    path('<int:id>/delivery-items/<int:item_id>/toggle/', ToggleDeliveryItemAutoReorderView.as_view(), name='routine_delivery_item_toggle_with_routine'),
]

