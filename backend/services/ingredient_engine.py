"""
Multi-Product Routine Conflict Detector & Ingredient Interaction Engine.
Analyzes ingredient interactions between newly selected products and existing routine/cart products.
Provides nuanced warnings and suggests compatible alternatives without forced blocking.
"""

from typing import List, Dict, Any, Optional
from products.models import Product, IngredientInteraction

def analyze_product_conflicts(
    target_product_id: int,
    existing_product_ids: List[int]
) -> Dict[str, Any]:
    """
    Analyzes potential ingredient interactions between a target product and existing products.
    """
    try:
        target_product = Product.objects.prefetch_related('ingredients').get(id=target_product_id)
    except Product.DoesNotExist:
        return {
            "has_conflicts": False,
            "has_warnings": False,
            "warnings": [],
            "alternatives": [],
            "error": f"Target product with ID {target_product_id} not found."
        }

    # Filter out target product itself if present in existing_product_ids
    compare_ids = [pid for pid in existing_product_ids if pid != target_product_id]
    if not compare_ids:
        return {
            "has_conflicts": False,
            "has_warnings": False,
            "warnings": [],
            "alternatives": []
        }

    existing_products = Product.objects.filter(id__in=compare_ids).prefetch_related('ingredients')
    target_ingredients = list(target_product.ingredients.all())

    warnings: List[Dict[str, Any]] = []
    conflicting_ingredient_ids = set()

    for existing_prod in existing_products:
        existing_ingredients = list(existing_prod.ingredients.all())
        for t_ing in target_ingredients:
            for e_ing in existing_ingredients:
                if t_ing.id == e_ing.id:
                    continue

                # Query symmetric interactions
                interaction = IngredientInteraction.objects.filter(
                    ingredient_a=t_ing, ingredient_b=e_ing
                ).first() or IngredientInteraction.objects.filter(
                    ingredient_a=e_ing, ingredient_b=t_ing
                ).first()

                if interaction:
                    conflicting_ingredient_ids.add(t_ing.id)
                    warnings.append({
                        "existing_product_id": existing_prod.id,
                        "existing_product_name": existing_prod.name,
                        "new_product_id": target_product.id,
                        "new_product_name": target_product.name,
                        "ingredient_a": interaction.ingredient_a.name,
                        "ingredient_b": interaction.ingredient_b.name,
                        "severity": interaction.severity,
                        "interaction_type": interaction.interaction_type,
                        "message": interaction.message,
                        "suggestion": interaction.recommendation,
                    })

    # Sort warnings by severity (warning > caution > info)
    severity_order = {"warning": 0, "caution": 1, "info": 2}
    warnings.sort(key=lambda w: severity_order.get(w["severity"], 3))

    has_conflicts = len(warnings) > 0
    has_warnings = any(w["severity"] == "warning" for w in warnings)

    alternatives = []
    if has_conflicts and conflicting_ingredient_ids:
        alternatives = find_alternative_products(target_product, conflicting_ingredient_ids)

    return {
        "has_conflicts": has_conflicts,
        "has_warnings": has_warnings,
        "warnings": warnings,
        "alternatives": alternatives,
    }


def find_alternative_products(
    target_product: Product,
    conflicting_ingredient_ids: set
) -> List[Dict[str, Any]]:
    """
    Suggests alternative products in the same category that avoid conflicting active ingredients.
    """
    candidates = (
        Product.objects.filter(category=target_product.category)
        .exclude(id=target_product.id)
        .prefetch_related('ingredients')
    )

    alternatives = []
    for cand in candidates:
        cand_ing_ids = set(cand.ingredients.values_list('id', flat=True))
        # If candidate has none of the conflicting active ingredients
        if not (cand_ing_ids & conflicting_ingredient_ids):
            alternatives.append({
                "product_id": cand.id,
                "name": cand.name,
                "category": cand.get_category_display(),
                "price": str(cand.price),
                "reason": (
                    f"Provides a gentler alternative in the {cand.get_category_display().lower()} category "
                    f"without overlapping active conflict ingredients."
                )
            })
            if len(alternatives) >= 3:
                break

    return alternatives
