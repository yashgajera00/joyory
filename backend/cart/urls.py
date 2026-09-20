from django.urls import path
from .views import (
    AddToCartView,
    UpdateCartItemView,
    ViewCartView,
    RemoveFromCartView,
    ClearCartView,
    CheckConflictsView,
    CartClimateAnalysisView
)

urlpatterns = [
    path('add/', AddToCartView.as_view(), name='cart_add'),
    path('update/', UpdateCartItemView.as_view(), name='cart_update'),
    path('', ViewCartView.as_view(), name='cart_view'),
    path('remove/', RemoveFromCartView.as_view(), name='cart_remove'),
    path('clear/', ClearCartView.as_view(), name='cart_clear'),
    path('check-conflicts/', CheckConflictsView.as_view(), name='cart_check_conflicts'),
    path('climate-analysis/', CartClimateAnalysisView.as_view(), name='cart_climate_analysis'),
]
