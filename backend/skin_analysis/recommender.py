"""
Skin Analysis Product Recommender
===================================
Matches the Ivy AI skin profile against Joyory's existing product database
using ingredient signals, skin_types, and concerns fields.

No external products — only products already in the Joyory DB are returned.
"""

from products.models import Product, Ingredient


# ---------------------------------------------------------------------------
# Ingredient → Skin concern mappings
# ---------------------------------------------------------------------------

INGREDIENT_SIGNALS = {
    # Oily / acne-prone skin
    'oily': ['Niacinamide (Vitamin B3)', 'Salicylic Acid (BHA)', 'Green Tea EGCG Extract',
              'Glycolic Acid (AHA)', 'Azelaic Acid'],
    # Dry / low hydration
    'dry': ['Hyaluronic Acid', 'Polyglutamic Acid', 'Ceramide NP', 'Glycerin',
             'Panthenol (Vitamin B5)', 'Squalane', 'Colloidal Oatmeal'],
    # Pigmentation / dark spots
    'pigmentation': ['L-Ascorbic Acid (Vitamin C)', 'Ethyl Ascorbic Acid', 'Alpha Arbutin',
                     'Tranexamic Acid', 'Niacinamide (Vitamin B3)', 'Azelaic Acid'],
    # Redness / sensitivity
    'redness': ['Centella Asiatica', 'Madecassoside', 'Allantoin', 'Mugwort Extract',
                 'Azelaic Acid', 'Colloidal Oatmeal'],
    # Enlarged pores
    'pores': ['Niacinamide (Vitamin B3)', 'Salicylic Acid (BHA)', 'Glycolic Acid (AHA)'],
    # Fine lines / aging
    'fine_lines': ['Retinol', 'Granactive Retinoid', 'Bakuchiol', 'Matrixyl 3000',
                   'Argireline (Acetyl Hexapeptide-8)', 'Copper Tripeptide-1'],
    # Texture / rough texture
    'texture': ['Glycolic Acid (AHA)', 'Lactic Acid (AHA)', 'Salicylic Acid (BHA)',
                 'Gluconolactone (PHA)', 'Mandelic Acid (AHA)'],
    # Dark circles
    'dark_circles': ['Niacinamide (Vitamin B3)', 'Copper Tripeptide-1', 'Caffeine'],
    # Radiance / dull skin
    'radiance': ['L-Ascorbic Acid (Vitamin C)', 'Ethyl Ascorbic Acid', 'Alpha Arbutin',
                  'Tranexamic Acid', 'Glycolic Acid (AHA)'],
    # Combination skin
    'combination': ['Niacinamide (Vitamin B3)', 'Azelaic Acid', 'Hyaluronic Acid'],
}

# Human-readable reason templates
REASON_TEMPLATES = {
    'oily': 'Ideal for oily skin — helps regulate excess sebum.',
    'dry': 'Provides deep hydration to address low moisture levels.',
    'pigmentation': 'Targets pigmentation and uneven skin tone.',
    'redness': 'Calms redness and soothes reactive skin.',
    'pores': 'Helps refine enlarged pores and clear congestion.',
    'fine_lines': 'Supports skin renewal and smooths fine lines.',
    'texture': 'Gently resurfaces uneven or rough skin texture.',
    'dark_circles': 'Supports the under-eye area and improves radiance.',
    'radiance': 'Brightens dull skin for a luminous, healthy glow.',
    'combination': 'Balanced formula suited for combination skin concerns.',
}


def _normalise_level(value: str) -> str:
    """
    Map arbitrary API level strings to low / moderate / high buckets.
    Returns lowercase string.
    """
    if not value:
        return ''
    v = str(value).lower()
    if v in ('high', 'very high', 'elevated', 'severe', 'significant', 'excessive'):
        return 'high'
    if v in ('low', 'very low', 'minimal', 'none', 'absent'):
        return 'low'
    return 'moderate'


def _extract_concerns(analysis: dict) -> list:
    """
    Convert the Ivy AI analysis dict into a prioritised list of skin concerns
    that will drive ingredient matching.
    """
    concerns = []
    metrics = analysis.get('metrics', {})

    skin_type = str(analysis.get('skin_type', '')).lower()
    if 'oily' in skin_type:
        concerns.append('oily')
    elif 'dry' in skin_type:
        concerns.append('dry')
    elif 'combination' in skin_type:
        concerns.append('combination')

    # Metric → concern mapping
    _map = {
        'oiliness': ('oily', 'high'),
        'hydration': ('dry', 'low'),       # low hydration → dry concern
        'pigmentation': ('pigmentation', 'moderate'),
        'redness': ('redness', 'moderate'),
        'pores': ('pores', 'moderate'),
        'texture': ('texture', 'moderate'),
        'fine_lines': ('fine_lines', 'moderate'),
        'dark_circles': ('dark_circles', 'moderate'),
        'radiance': ('radiance', 'low'),   # low radiance → dull skin
    }

    for key, (concern, trigger_level) in _map.items():
        metric = metrics.get(key, {})
        if isinstance(metric, dict):
            raw_level = metric.get('level', metric.get('value', metric.get('score', '')))
        else:
            raw_level = str(metric)

        norm = _normalise_level(str(raw_level))

        if trigger_level == 'high' and norm == 'high':
            concerns.append(concern)
        elif trigger_level == 'low' and norm == 'low':
            concerns.append(concern)
        elif trigger_level == 'moderate' and norm in ('moderate', 'high'):
            concerns.append(concern)

    return list(dict.fromkeys(concerns))  # deduplicate, preserve order


def recommend_products(analysis: dict, max_results: int = 5) -> list:
    """
    Given the Ivy AI analysis dict, query the Joyory product database
    and return the top `max_results` most relevant products with reasons.

    Returns list of dicts:
    {
        "product_id": int,
        "name": str,
        "category": str,
        "price": str,
        "image_url": str,
        "brand": str,
        "reason": str,
        "match_score": int,
    }
    """
    concerns = _extract_concerns(analysis)

    if not concerns:
        # Fallback: return bestseller-style safe picks (low active level, broad skin types)
        concerns = ['dry', 'radiance']

    # Build ingredient name sets for each concern
    concern_ingredient_sets = {}
    for concern in concerns:
        ing_names = INGREDIENT_SIGNALS.get(concern, [])
        concern_ingredient_sets[concern] = set(ing_names)

    # Fetch all products with their ingredients
    all_products = list(
        Product.objects.prefetch_related('ingredients').all()
    )

    scored = []
    for product in all_products:
        score = 0
        matched_concerns = []
        product_ingredient_names = {ing.name for ing in product.ingredients.all()}
        product_skin_types = product.skin_types.lower()
        product_concerns_field = product.concerns.lower()

        for concern in concerns:
            ing_set = concern_ingredient_sets.get(concern, set())
            # Match by ingredients
            ingredient_overlap = len(ing_set & product_ingredient_names)
            if ingredient_overlap > 0:
                score += ingredient_overlap * 2
                matched_concerns.append(concern)
                continue

            # Match by skin_types or concerns field
            concern_keywords = {
                'oily': ['oily'],
                'dry': ['dry', 'hydrat'],
                'pigmentation': ['pigment', 'dark spot', 'tone', 'brighten'],
                'redness': ['redness', 'rosacea', 'calm', 'sensitiv', 'sooth'],
                'pores': ['pore', 'congestion'],
                'fine_lines': ['fine line', 'wrinkle', 'anti-aging', 'aging'],
                'texture': ['texture', 'roughness', 'exfoliat'],
                'dark_circles': ['dark circle', 'eye'],
                'radiance': ['radianc', 'glow', 'brighten', 'luminous'],
                'combination': ['combination'],
            }.get(concern, [])

            for kw in concern_keywords:
                if kw in product_skin_types or kw in product_concerns_field:
                    score += 1
                    matched_concerns.append(concern)
                    break

        if score > 0:
            # Build readable reason from matched concerns
            reasons = []
            for c in dict.fromkeys(matched_concerns):
                if c in REASON_TEMPLATES:
                    reasons.append(REASON_TEMPLATES[c])
            reason_text = ' '.join(reasons[:2]) if reasons else 'Matches your current skin profile.'

            scored.append({
                'product_id': product.id,
                'name': product.name,
                'category': product.get_category_display(),
                'category_slug': product.category,
                'price': str(product.price),
                'image_url': product.effective_image_url,
                'brand': product.brand,
                'reason': reason_text,
                'match_score': score,
            })

    # Sort by match score descending, take top N
    scored.sort(key=lambda x: x['match_score'], reverse=True)
    results = scored[:max_results]

    # Remove internal scoring field from output
    for r in results:
        r.pop('match_score', None)

    return results
