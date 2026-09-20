from django.urls import path, include
from .views import health_check, ClimateAnalyzeView
from .auth_views import login_view, register_view, logout_view, me_view

urlpatterns = [
    path("health/", health_check, name="health_check"),
    path("climate/analyze/", ClimateAnalyzeView.as_view(), name="climate_analyze"),
    path("products/", include("products.urls")),
    path("cart/", include("cart.urls")),
    path("routines/", include("routines.urls")),
    # Auth endpoints
    path("auth/login/", login_view, name="auth_login"),
    path("auth/register/", register_view, name="auth_register"),
    path("auth/logout/", logout_view, name="auth_logout"),
    path("auth/me/", me_view, name="auth_me"),
]
