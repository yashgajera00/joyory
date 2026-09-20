"""
Authentication API Views for Joyory
===================================
Provides registration, login, logout, and current user profile endpoints
using Django REST Framework TokenAuthentication.
"""

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response


def _user_data(user):
    """Serialize user object for API responses."""
    full_name = f"{user.first_name} {user.last_name}".strip() or user.username
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": full_name,
    }


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    """
    Authenticate a user with username/email and password.
    Returns auth token and user profile.
    """
    identifier = (
        request.data.get("username", "").strip()
        or request.data.get("email", "").strip()
        or request.data.get("identifier", "").strip()
    )
    password = request.data.get("password", "")

    if not identifier or not password:
        return Response(
            {"success": False, "error": "Username/Email and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Allow login with either username or email
    username_to_try = identifier
    if "@" in identifier:
        user_by_email = User.objects.filter(email__iexact=identifier).first()
        if user_by_email:
            username_to_try = user_by_email.username

    user = authenticate(request, username=username_to_try, password=password)

    if not user:
        # Fallback: check if username was entered directly with email field
        user = authenticate(request, username=identifier, password=password)

    if not user:
        return Response(
            {"success": False, "error": "Invalid credentials. Please check your username and password."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        return Response(
            {"success": False, "error": "This account is inactive. Please contact support."},
            status=status.HTTP_403_FORBIDDEN,
        )

    token, _ = Token.objects.get_or_create(user=user)

    return Response(
        {
            "success": True,
            "token": token.key,
            "user": _user_data(user),
            "message": f"Welcome back, {user.first_name or user.username}!",
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    """
    Register a new user account with username, email, and password.
    Returns auth token and created user profile.
    """
    username = request.data.get("username", "").strip()
    email = request.data.get("email", "").strip()
    password = request.data.get("password", "").strip()
    first_name = request.data.get("first_name", "").strip()
    last_name = request.data.get("last_name", "").strip()

    if not username:
        return Response(
            {"success": False, "error": "Username is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not password or len(password) < 6:
        return Response(
            {"success": False, "error": "Password must be at least 6 characters long."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if User.objects.filter(username__iexact=username).exists():
        return Response(
            {"success": False, "error": f"Username '{username}' is already taken. Please choose another."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if email and User.objects.filter(email__iexact=email).exists():
        return Response(
            {"success": False, "error": f"An account with email '{email}' already exists. Please sign in."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "success": True,
                "token": token.key,
                "user": _user_data(user),
                "message": f"Account created successfully! Welcome to Joyory, {user.first_name or user.username}.",
            },
            status=status.HTTP_201_CREATED,
        )
    except Exception as exc:
        return Response(
            {"success": False, "error": f"Could not create account: {str(exc)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def logout_view(request):
    """
    Logout the authenticated user by deleting their auth token.
    """
    if request.user and request.user.is_authenticated:
        Token.objects.filter(user=request.user).delete()

    return Response(
        {"success": True, "message": "Logged out successfully."},
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
def me_view(request):
    """
    Get profile information of the currently authenticated user.
    """
    if not request.user or not request.user.is_authenticated:
        return Response(
            {"success": False, "authenticated": False, "user": None},
            status=status.HTTP_200_OK,
        )

    return Response(
        {
            "success": True,
            "authenticated": True,
            "user": _user_data(request.user),
        },
        status=status.HTTP_200_OK,
    )
