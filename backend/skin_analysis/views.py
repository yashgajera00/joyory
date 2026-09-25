"""
Skin Analysis View
==================
Proxies image to the Gemini Vision API.
The GEMINI_API_KEY is read from Django settings (loaded via .env).
It is NEVER returned to the frontend or logged.
"""

import base64
import io
import json
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
GEMINI_TIMEOUT = 30  # seconds


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


def _normalise_metric_value(raw_value, fallback_level='moderate', fallback_score=60):
    if raw_value is None:
        return {'level': fallback_level, 'score': fallback_score}
    if isinstance(raw_value, dict):
        level = raw_value.get('level') or raw_value.get('value') or raw_value.get('status') or fallback_level
        score = raw_value.get('score')
        if score is None:
            try:
                score = int(raw_value.get('value', fallback_score))
            except (TypeError, ValueError):
                score = fallback_score
        return {'level': str(level), 'score': int(score)}
    if isinstance(raw_value, (int, float)):
        return {'level': fallback_level, 'score': int(raw_value)}
    if isinstance(raw_value, str):
        lower = raw_value.lower()
        if lower in {'low', 'moderate', 'high'}:
            level = lower
        else:
            level = fallback_level
        return {'level': level, 'score': fallback_score}
    return {'level': fallback_level, 'score': fallback_score}


def _build_analysis_response(gemini_response: dict) -> dict:
    """Normalize Gemini JSON into the same structure the app already expects."""
    raw = gemini_response.get('analysis') or gemini_response.get('result') or gemini_response

    metrics_source = raw.get('metrics') or {}
    metrics = {
        'oiliness': _normalise_metric_value(metrics_source.get('oiliness')),
        'hydration': _normalise_metric_value(metrics_source.get('hydration')),
        'pigmentation': _normalise_metric_value(metrics_source.get('pigmentation')),
        'pores': _normalise_metric_value(metrics_source.get('pores')),
        'redness': _normalise_metric_value(metrics_source.get('redness')),
        'texture': _normalise_metric_value(metrics_source.get('texture')),
        'fine_lines': _normalise_metric_value(metrics_source.get('fine_lines') or metrics_source.get('fineLines')),
        'dark_circles': _normalise_metric_value(metrics_source.get('dark_circles') or metrics_source.get('darkCircles')),
        'radiance': _normalise_metric_value(metrics_source.get('radiance')),
    }

    score = raw.get('overall_health_score')
    if score is None:
        try:
            score = int(raw.get('overallHealthScore') or raw.get('score') or 75)
        except (TypeError, ValueError):
            score = 75

    return {
        'skin_type': raw.get('skin_type') or raw.get('skinType') or 'Balanced',
        'overall_health_score': int(score),
        'metrics': metrics,
    }


def _extract_gemini_json(text: str):
    if not text:
        return {}
    cleaned = text.strip()
    if cleaned.startswith('```'):
        cleaned = cleaned.strip('`')
        if cleaned.lower().startswith('json'):
            cleaned = cleaned[4:].strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find('{')
        end = cleaned.rfind('}')
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(cleaned[start:end + 1])
            except json.JSONDecodeError:
                return {}
        return {}


@api_view(['POST'])
def skin_analysis_view(request):
    """
    POST /api/skin-analysis/
    Accepts multipart/form-data with an 'image' file field.
    Proxies to the Gemini Vision API and returns analysis + product recommendations.
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if not api_key:
        logger.error("GEMINI_API_KEY is not configured in backend .env")
        return Response(
            {'success': False, 'error': 'Skin analysis service is not configured.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

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

    compressed = _compress_image(image_bytes)
    encoded = base64.b64encode(compressed).decode('utf-8')
    endpoint = f"{settings.GEMINI_ENDPOINT}/{settings.GEMINI_MODEL_NAME}:generateContent?key={api_key}"
    prompt = (
        "Analyze this face skin image for skincare and return JSON only. "
        "Output this exact structure: {\n"
        "  \"skin_type\": \"string\",\n"
        "  \"overall_health_score\": 0-100,\n"
        "  \"metrics\": {\n"
        "    \"oiliness\": {\"level\": \"low|moderate|high\", \"score\": 0-100},\n"
        "    \"hydration\": {\"level\": \"low|moderate|high\", \"score\": 0-100},\n"
        "    \"pigmentation\": {\"level\": \"low|moderate|high\", \"score\": 0-100},\n"
        "    \"pores\": {\"level\": \"low|moderate|high\", \"score\": 0-100},\n"
        "    \"redness\": {\"level\": \"low|moderate|high\", \"score\": 0-100},\n"
        "    \"texture\": {\"level\": \"low|moderate|high\", \"score\": 0-100},\n"
        "    \"fine_lines\": {\"level\": \"low|moderate|high\", \"score\": 0-100},\n"
        "    \"dark_circles\": {\"level\": \"low|moderate|high\", \"score\": 0-100},\n"
        "    \"radiance\": {\"level\": \"low|moderate|high\", \"score\": 0-100}\n"
        "  }\n"
        "}. Do not include Markdown fences or explanations."
    )
    payload = {
        'contents': [{
            'parts': [
                {'text': prompt},
                {'inline_data': {'mime_type': 'image/jpeg', 'data': encoded}}
            ]
        }]
    }

    try:
        gemini_resp = requests.post(
            endpoint,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=GEMINI_TIMEOUT,
        )
    except requests.Timeout:
        logger.warning("Gemini request timed out after %ss", GEMINI_TIMEOUT)
        return Response(
            {'success': False, 'error': 'Skin analysis timed out. Please try again.'},
            status=status.HTTP_504_GATEWAY_TIMEOUT
        )
    except requests.RequestException as exc:
        logger.error("Gemini request failed: %s", exc)
        return Response(
            {'success': False, 'error': 'We couldn\'t analyze your photo right now.'},
            status=status.HTTP_502_BAD_GATEWAY
        )

    if gemini_resp.status_code == 401:
        return Response(
            {'success': False, 'error': 'Gemini API authentication failed. Please check the API key.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if gemini_resp.status_code == 400:
        return Response(
            {'success': False, 'error': 'Gemini rejected the uploaded image or request format.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not gemini_resp.ok:
        logger.warning("Gemini API returned %s: %s", gemini_resp.status_code, gemini_resp.text[:300])
        return Response(
            {'success': False, 'error': 'Skin analysis could not be completed right now.'},
            status=status.HTTP_502_BAD_GATEWAY
        )

    try:
        gemini_data = gemini_resp.json()
    except ValueError:
        return Response(
            {'success': False, 'error': 'Gemini returned an invalid response.'},
            status=status.HTTP_502_BAD_GATEWAY
        )

    try:
        candidate = gemini_data['candidates'][0]
        text = ''.join(part.get('text', '') for part in candidate.get('content', {}).get('parts', []) if isinstance(part, dict))
        parsed = _extract_gemini_json(text)
        if not parsed:
            raise ValueError('No JSON found in Gemini output')
    except (KeyError, IndexError, ValueError):
        logger.error('Gemini response did not contain usable JSON: %s', gemini_data)
        return Response(
            {'success': False, 'error': 'Gemini returned an unusable analysis payload.'},
            status=status.HTTP_502_BAD_GATEWAY
        )

    analysis = _build_analysis_response(parsed)

    recommendations = []
    try:
        recommendations = recommend_products(analysis)
    except Exception as exc:
        logger.error("Product recommendation failed: %s", exc)

    return Response({
        'success': True,
        'analysis': analysis,
        'recommendations': recommendations,
    }, status=status.HTTP_200_OK)
