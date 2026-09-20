from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from services.climate_service import default_climate_service
from services.climate_engine import evaluate_climate_adaptation

@api_view(["GET"])
def health_check(request):
    """
    API Health Check endpoint to verify backend status and CORS configuration.
    """
    return Response({
        "status": "online",
        "service": "Joyory Backend API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })

class ClimateAnalyzeView(APIView):
    """
    Analyzes hyper-local climate conditions for a given coordinate or city,
    and returns smart shopping suggestions for the provided products.
    """
    def post(self, request):
        lat = request.data.get('latitude')
        lon = request.data.get('longitude')
        city = request.data.get('city')
        product_ids = request.data.get('product_ids', [])

        try:
            latitude = float(lat) if lat is not None else None
            longitude = float(lon) if lon is not None else None
        except (ValueError, TypeError):
            latitude, longitude = None, None

        climate_data = default_climate_service.get_climate_data(
            latitude=latitude,
            longitude=longitude,
            city=city
        )

        analysis = evaluate_climate_adaptation(climate_data, product_ids)
        return Response(analysis, status=status.HTTP_200_OK)
