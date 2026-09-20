import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from products.models import Product
from services.ingredient_engine import analyze_product_conflicts
from services.climate_service import default_climate_service
from services.climate_engine import evaluate_climate_adaptation
from .models import Cart, CartItem
from .serializers import (
    CartSerializer,
    AddToCartInputSerializer,
    UpdateCartItemInputSerializer,
    RemoveFromCartInputSerializer,
    CheckConflictsInputSerializer
)

def get_or_create_cart(request, session_key: str = None) -> Cart:
    """
    Resolves or creates a Cart based on user authentication or session_key.
    Ensures strict separation between authenticated users and guest carts.
    """
    user = request.user if (request.user and request.user.is_authenticated) else None
    if user:
        cart = Cart.objects.filter(user=user).order_by('-updated_at').first()
        if not cart:
            cart = Cart.objects.create(user=user)
        return cart

    s_key = session_key or request.headers.get('X-Session-ID') or request.query_params.get('session_key')
    if not s_key:
        s_key = str(uuid.uuid4())

    cart = Cart.objects.filter(session_key=s_key, user=None).order_by('-updated_at').first()
    if not cart:
        cart = Cart.objects.create(session_key=s_key, user=None)
    return cart


class AddToCartView(APIView):
    """
    Add a product to the customer's cart.
    Automatically performs multi-product ingredient conflict analysis without blocking the purchase.
    Supports set_quantity / mode='set' to directly update quantity.
    """
    def post(self, request):
        serializer = AddToCartInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data.get('quantity', 1)
        session_key = serializer.validated_data.get('session_key')
        set_quantity = serializer.validated_data.get('set_quantity', False) or request.data.get('mode') == 'set'

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        cart = get_or_create_cart(request, session_key)

        # Existing products currently in cart before adding/updating this one
        existing_product_ids = list(
            cart.items.exclude(product_id=product_id).values_list('product_id', flat=True)
        )

        # Analyze conflicts against existing cart contents
        conflict_analysis = analyze_product_conflicts(product_id, existing_product_ids)

        # Update or create cart item
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            if set_quantity:
                cart_item.quantity = quantity
            else:
                cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()

        cart_data = CartSerializer(cart).data

        return Response({
            "message": f"Added '{product.name}' to cart.",
            "cart": cart_data,
            "conflict_analysis": conflict_analysis
        }, status=status.HTTP_200_OK)


class UpdateCartItemView(APIView):
    """
    Directly set the exact quantity of a product in the customer's cart.
    If quantity is 0 or less, the product is removed from the cart.
    """
    def post(self, request):
        serializer = UpdateCartItemInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']
        session_key = serializer.validated_data.get('session_key')

        cart = get_or_create_cart(request, session_key)

        try:
            cart_item = cart.items.get(product_id=product_id)
            if quantity <= 0:
                cart_item.delete()
                message = "Product removed from cart."
            else:
                cart_item.quantity = quantity
                cart_item.save()
                message = f"Updated quantity to {quantity}."
        except CartItem.DoesNotExist:
            if quantity > 0:
                try:
                    product = Product.objects.get(id=product_id)
                    CartItem.objects.create(cart=cart, product=product, quantity=quantity)
                    message = f"Added '{product.name}' with quantity {quantity}."
                except Product.DoesNotExist:
                    return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
            else:
                message = "Item was not in cart."

        # Re-check conflicts across cart
        cart_product_ids = list(cart.items.values_list('product_id', flat=True))
        conflict_analysis = None
        if cart_product_ids:
            conflict_analysis = analyze_product_conflicts(cart_product_ids[0], cart_product_ids[1:])

        cart_data = CartSerializer(cart).data
        return Response({
            "message": message,
            "cart": cart_data,
            "conflict_analysis": conflict_analysis
        }, status=status.HTTP_200_OK)


class ViewCartView(APIView):
    """
    Retrieve cart details, items, line totals, and overall total.
    """
    def get(self, request):
        session_key = request.query_params.get('session_key')
        cart = get_or_create_cart(request, session_key)
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


class RemoveFromCartView(APIView):
    """
    Remove or decrement a product from the customer's cart.
    """
    def delete(self, request):
        serializer = RemoveFromCartInputSerializer(data=request.data or request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        product_id = serializer.validated_data['product_id']
        session_key = serializer.validated_data.get('session_key')
        cart = get_or_create_cart(request, session_key)

        try:
            item = cart.items.get(product_id=product_id)
            item.delete()
        except CartItem.DoesNotExist:
            return Response({"error": "Product not found in cart."}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "message": "Product removed from cart.",
            "cart": CartSerializer(cart).data
        }, status=status.HTTP_200_OK)


class ClearCartView(APIView):
    """
    Clears all items from customer's cart upon checkout completion.
    """
    def post(self, request):
        session_key = request.data.get('session_key') or request.query_params.get('session_key')
        cart = get_or_create_cart(request, session_key)
        cart.items.all().delete()
        return Response({
            "message": "Cart cleared successfully.",
            "cart": CartSerializer(cart).data
        }, status=status.HTTP_200_OK)


class CheckConflictsView(APIView):
    """
    Ad-hoc ingredient interaction check endpoint for a given product vs cart/routine product IDs.
    """
    def post(self, request):
        serializer = CheckConflictsInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        product_id = serializer.validated_data['product_id']
        cart_product_ids = serializer.validated_data.get('cart_product_ids', [])

        result = analyze_product_conflicts(product_id, cart_product_ids)
        return Response(result, status=status.HTTP_200_OK)


class CartClimateAnalysisView(APIView):
    """
    Analyzes current cart products against hyper-local environmental data (UV, humidity, temp, AQI).
    """
    def post(self, request):
        lat = request.data.get('latitude')
        lon = request.data.get('longitude')
        city = request.data.get('city')
        session_key = request.data.get('session_key')

        cart = get_or_create_cart(request, session_key)
        cart_product_ids = list(cart.items.values_list('product_id', flat=True))

        climate_data = default_climate_service.get_climate_data(
            latitude=float(lat) if lat is not None else None,
            longitude=float(lon) if lon is not None else None,
            city=city
        )

        analysis = evaluate_climate_adaptation(climate_data, cart_product_ids)
        return Response(analysis, status=status.HTTP_200_OK)
