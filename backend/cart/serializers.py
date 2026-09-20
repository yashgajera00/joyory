from rest_framework import serializers
from products.serializers import ProductSerializer
from .models import Cart, CartItem

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'line_total', 'added_at']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'session_key', 'items', 'total_items', 'total_price', 'created_at', 'updated_at']

class AddToCartInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(required=False, default=1, min_value=1)
    session_key = serializers.CharField(required=False, allow_blank=True, default='')
    set_quantity = serializers.BooleanField(required=False, default=False)

class UpdateCartItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=0)
    session_key = serializers.CharField(required=False, allow_blank=True, default='')

class RemoveFromCartInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    session_key = serializers.CharField(required=False, allow_blank=True, default='')

class CheckConflictsInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    cart_product_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list
    )
