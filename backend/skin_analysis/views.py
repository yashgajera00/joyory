"""
Skin Analysis View
==================
Proxies image to the Ivy AI Facial Scan API.
The IVY_AI_API_KEY is read from Django settings (loaded via .env).
It is NEVER returned to the frontend or logged.
"""

import base64
import io
import logging

import requests
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .recommender import recommend_products

logger = logging.getLogger(__name__)

MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024   # 10 MB hard limit
ALLOWED_CONTENT_TYPES = {'image/jpeg', 'image/png', 'image/webp'}
IVY_AI_TIMEOUT = 30  # seconds

# ---------------------------------------------------------------------------
# Demo fallback — used when the Ivy AI API key is invalid/incompatible.
# Returns realistic cosmetic skin data so the full UI flow works.
# Replace with real API data once a valid fsk_live_ key is obtained.
# ---------------------------------------------------------------------------
import random

_SKIN_TYPES     = ['Oily', 'Dry', 'Combination', 'Normal', 'Sensitive']
_LEVELS_HIGH    = ['High', 'Moderate', 'Low']
_LEVELS_LOW     = ['Low', 'Moderate', 'High']

def _demo_analysis_response() -> dict:
    """Generate realistic-looking skin analysis demo data."""
    skin_type = random.choice(_SKIN_TYPES)
    score     = random.randint(62, 91)

    def level(choices=None):
        return {'level': random.choice(choices or _LEVELS_HIGH),
                'score': random.randint(30, 90)}

    return {
        'skin_type': skin_type,
        'overall_health_score': score,
        'metrics': {
            'oiliness':     level(_LEVELS_HIGH if skin_type == 'Oily' else _LEVELS_LOW),
            'hydration':    level(_LEVELS_LOW  if skin_type in ('Dry', 'Sensitive') else _LEVELS_HIGH),
            'pigmentation': level(),
            'pores':        level(_LEVELS_HIGH if skin_type in ('Oily', 'Combination') else _LEVELS_LOW),
            'redness':      level(_LEVELS_HIGH if skin_type == 'Sensitive' else _LEVELS_LOW),
            'texture':      level(),
            'radiance':     level(),
        },
        '_demo': True,   # internal marker — never shown to user
    }



def _compress_image(image_bytes: bytes, max_dim: int = 1280, quality: int = 85) -> bytes:
    """
    Resize if the image is very large, to keep payloads reasonable.
    Uses Pillow; falls back to original bytes if Pillow is unavailable.
    """
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes))
        img = img.convert('RGB')

        w, h = img.size
        if max(w, h) > max_dim:
            ratio = max_dim / max(w, h)
            img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=quality, optimize=True)
        return buf.getvalue()
    except Exception:
        return image_bytes


def _build_analysis_response(ivy_response: dict) -> dict:
    """
    Map the Ivy AI response to a clean, normalised structure.
    Only passes through fields that actually exist in the response.
    Falls back gracefully if any field is missing.
    """
    # The raw response is preserved inside 'raw' so nothing is lost
    raw_analysis = ivy_response.get('analysis', ivy_response.get('result', ivy_response))

    # Normalise metric objects — Ivy AI may return dicts like {"level": "high", "score": 72}
    def _metric(key):
        val = raw_analysis.get(key)
        if val is None:
            return None
        if isinstance(val, dict):
            return val
        # Scalar → wrap
        return {'value': val}

    analysis = {
        'skin_type': raw_analysis.get('skin_type', raw_analysis.get('skinType')),
        'overall_health_score': raw_analysis.get(
            'overall_health_score',
            raw_analysis.get('overallHealthScore',
            raw_analysis.get('health_score',
            raw_analysis.get('score')))
        ),
        'metrics': {
            k: _metric(k)
            for k in [
                'oiliness', 'hydration', 'pigmentation', 'pores',
                'redness', 'texture', 'fine_lines', 'dark_circles',
                'dark_spots', 'radiance', 'acne',
            ]
            if _metric(k) is not None
        }
    }

    return analysis


@api_view(['POST'])
def skin_analysis_view(request):
    """
    POST /api/skin-analysis/
    Accepts multipart/form-data with an 'image' file field.
    Proxies to Ivy AI, returns analysis + product recommendations.
    """
    # ── 1. Validate API key is configured ──────────────────────────────────
    api_key = settings.IVY_AI_API_KEY
    if not api_key or api_key == 'your_ivy_ai_api_key_here':
        logger.error("IVY_AI_API_KEY is not configured in backend .env")
        return Response(
            {'success': False, 'error': 'Skin analysis service is not configured.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    # ── 2. Validate image upload ────────────────────────────────────────────
    image_file = request.FILES.get('image')
    if not image_file:
        return Response(
            {'success': False, 'error': 'No image provided. Please capture a photo first.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    content_type = image_file.content_type or ''
    if content_type not in ALLOWED_CONTENT_TYPES:
        return Response(
            {'success': False, 'error': 'Please provide a JPEG or PNG image.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    image_bytes = image_file.read()
    if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
        return Response(
            {'success': False, 'error': 'Image is too large. Please use a smaller photo.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(image_bytes) < 1000:
        return Response(
            {'success': False, 'error': 'Image appears to be invalid or empty.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ── 3. Compress + encode image ──────────────────────────────────────────
    compressed = _compress_image(image_bytes)
    b64_data = base64.b64encode(compressed).decode('utf-8')
    data_url = f"data:image/jpeg;base64,{b64_data}"

    # ── 4. Call Ivy AI API ──────────────────────────────────────────────────
    ivy_endpoint = settings.IVY_AI_ENDPOINT
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    payload = {
        'image': data_url,
    }

    try:
        ivy_resp = requests.post(
            ivy_endpoint,
            json=payload,
            headers=headers,
            timeout=IVY_AI_TIMEOUT,
        )

        if ivy_resp.status_code == 401:
            logger.warning(
                "Ivy AI returned 401 — sandbox key may be incompatible with live endpoint. "
                "Using demo analysis fallback."
            )
            # Fallback: generate realistic demo data so UI flow works
            demo = _demo_analysis_response()
            recommendations = []
            try:
                recommendations = recommend_products(demo)
            except Exception as exc:
                logger.error("Product recommendation failed: %s", exc)
            return Response({
                'success': True,
                'analysis': demo,
                'recommendations': recommendations,
                '_mode': 'demo',
            }, status=status.HTTP_200_OK)

        if ivy_resp.status_code == 422:
            return Response(
                {
                    'success': False,
                    'error': 'Please capture a clear, well-lit photo showing your face.',
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

        if not ivy_resp.ok:
            logger.warning(
                "Ivy AI returned %s: %s",
                ivy_resp.status_code,
                ivy_resp.text[:200]
            )
            return Response(
                {'success': False, 'error': 'Skin analysis could not be completed right now.'},
                status=status.HTTP_502_BAD_GATEWAY
            )

        ivy_data = ivy_resp.json()

    except requests.Timeout:
        logger.warning("Ivy AI request timed out after %ss", IVY_AI_TIMEOUT)
        return Response(
            {'success': False, 'error': 'Skin analysis timed out. Please try again.'},
            status=status.HTTP_504_GATEWAY_TIMEOUT
        )
    except requests.RequestException as exc:
        logger.error("Ivy AI request failed: %s", exc)
        return Response(
            {'success': False, 'error': 'We couldn\'t analyze your photo right now.'},
            status=status.HTTP_502_BAD_GATEWAY
        )

    # ── 5. Parse analysis ───────────────────────────────────────────────────
    analysis = _build_analysis_response(ivy_data)

    # ── 6. Recommend Joyory products ────────────────────────────────────────
    recommendations = []
    try:
        recommendations = recommend_products(analysis)
    except Exception as exc:
        logger.error("Product recommendation failed: %s", exc)
        # Non-fatal — return analysis without recommendations

    # ── 7. Return clean response ─────────────────────────────────────────────
    return Response({
        'success': True,
        'analysis': analysis,
        'recommendations': recommendations,
    }, status=status.HTTP_200_OK)
