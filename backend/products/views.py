from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product
from .serializers import ProductSerializer

class ProductListView(generics.ListAPIView):
    """
    Catalog of Joyory products with search and filtering by category, climate, and active level.
    """
    queryset = Product.objects.all().prefetch_related('ingredients').order_by('id')
    serializer_class = ProductSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.query_params.get('category')
        climate = self.request.query_params.get('climate')
        active_level = self.request.query_params.get('active_level')
        search = self.request.query_params.get('search')

        if category:
            qs = qs.filter(category=category)
        if climate:
            qs = qs.filter(suitable_climate__in=[climate, 'all'])
        if active_level:
            qs = qs.filter(active_level=active_level)
        if search:
            qs = qs.filter(name__icontains=search)
        return qs

class ProductDetailView(generics.RetrieveAPIView):
    """
    Detailed product view including full ingredient list and metadata.
    """
    queryset = Product.objects.all().prefetch_related('ingredients')
    serializer_class = ProductSerializer
    lookup_field = 'id'
