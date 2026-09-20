from django.urls import path
from .views import skin_analysis_view

urlpatterns = [
    path('', skin_analysis_view, name='skin_analysis'),
]
