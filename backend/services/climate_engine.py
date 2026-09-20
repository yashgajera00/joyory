"""
Climate Adaptation Engine.
Analyzes hyper-local climate conditions (temperature, humidity, UV index, AQI)
against products in the customer's cart or routine to offer smart shopping guidance.
Strictly non-diagnostic; focuses on texture, environmental protection, and hydration comfort.
"""

from typing import List, Dict, Any
from products.models import Product

def evaluate_climate_adaptation(
    climate_data: Dict[str, Any],
    product_ids: List[int]
) -> Dict[str, Any]:
    """
    Evaluates customer products against environmental parameters and produces shopping recommendations.
    """
    temp = climate_data.get("temperature", 25)
    humidity = climate_data.get("humidity", 50)
    uv_index = climate_data.get("uv_index", 5)
    aqi = climate_data.get("aqi", 50)

    products = list(Product.objects.filter(id__in=product_ids).prefetch_related('ingredients'))
    product_categories = {p.category for p in products}

    suggestions = []
    recommended_product_ids = set()

    # 1. UV Index Analysis
    has_sunscreen = 'sunscreen' in product_categories
    if uv_index >= 6:
        if not has_sunscreen:
            suggestions.append({
                "type": "uv_protection",
                "title": f"Elevated UV Index ({uv_index})",
                "message": (
                    f"Current local UV index is high ({uv_index}). Consider including a broad-spectrum "
                    "daily sunscreen to protect your skin barrier while using skincare routines."
                )
            })
            # Find recommended sunscreen
            sunscreen = Product.objects.filter(category='sunscreen').first()
            if sunscreen:
                recommended_product_ids.add(sunscreen.id)
        else:
            suggestions.append({
                "type": "uv_protection",
                "title": f"UV Defense Active ({uv_index})",
                "message": (
                    f"UV levels are high ({uv_index}), and your cart includes suitable sun protection. "
                    "Remember to reapply every 2 hours if outdoors."
                )
            })

    # 2. Humidity & Temperature Texture Optimization
    if humidity >= 65:
        # Check if cart contains heavy/rich creams
        heavy_creams = [p for p in products if p.texture == 'rich_cream']
        if heavy_creams:
            suggestions.append({
                "type": "texture_guidance",
                "title": f"High Humidity ({humidity}%) & Temperature ({temp}°C)",
                "message": (
                    f"Local humidity is {humidity}%. Rich, heavy creams may feel occlusive. "
                    "A lightweight water-gel or oil-free fluid moisturizer may feel significantly more breathable."
                )
            })
            # Suggest lightweight gel alternatives
            gels = Product.objects.filter(category='moisturizer', texture='gel').exclude(id__in=product_ids)[:2]
            for g in gels:
                recommended_product_ids.add(g.id)
    elif humidity <= 40:
        # Dry climate: check if hydrating products are present
        hydrators = [p for p in products if p.hydration_level in ['moderate', 'deep']]
        if not hydrators:
            suggestions.append({
                "type": "barrier_hydration",
                "title": f"Dry Environmental Conditions ({humidity}% Humidity)",
                "message": (
                    f"Current air moisture is low ({humidity}%). Low humidity can accelerate transepidermal water loss. "
                    "Consider pairing your routine with a hyaluronic acid or ceramide-rich barrier moisturizer."
                )
            })
            hydrating_prod = Product.objects.filter(
                category__in=['moisturizer', 'serum'], hydration_level='deep'
            ).first()
            if hydrating_prod:
                recommended_product_ids.add(hydrating_prod.id)
        else:
            suggestions.append({
                "type": "barrier_hydration",
                "title": f"Dry Climate Support ({humidity}%)",
                "message": (
                    f"Air humidity is low ({humidity}%). Your routine includes good hydrating elements "
                    "to maintain skin moisture balance."
                )
            })

    # 3. Air Quality / AQI Barrier Considerations
    if aqi >= 100:
        suggestions.append({
            "type": "pollution_defense",
            "title": f"Elevated Air Quality Index (AQI {aqi})",
            "message": (
                f"Local ambient particulate levels are elevated (AQI {aqi}). Using an antioxidant-rich formula "
                "(such as Vitamin C or Niacinamide) and a gentle evening double cleanser helps shield and purify your skin."
            )
        })
        antioxidant_prod = Product.objects.filter(
            category='serum', ingredients__category='antioxidant'
        ).exclude(id__in=product_ids).first()
        if antioxidant_prod:
            recommended_product_ids.add(antioxidant_prod.id)

    # Fetch alternative / suggested products
    alternative_products = []
    if recommended_product_ids:
        rec_objs = Product.objects.filter(id__in=recommended_product_ids)
        for obj in rec_objs:
            alternative_products.append({
                "product_id": obj.id,
                "name": obj.name,
                "category": obj.get_category_display(),
                "price": str(obj.price),
                "texture": obj.get_texture_display(),
                "reason": f"Recommended for current climate ({climate_data.get('condition', 'Local Weather')}, UV {uv_index}, Humidity {humidity}%)."
            })

    return {
        "location_available": True,
        "climate": climate_data,
        "suggestions": suggestions,
        "alternative_products": alternative_products
    }


def evaluate_daily_tracker_weather_timing(
    routine_steps,
    weather_data: Dict[str, Any],
    selected_time_of_day: str = None
) -> Dict[str, Any]:
    """
    Evaluates each product in a routine against current hyper-local weather conditions
    (temperature, humidity, UV index, AQI) and time of day (morning vs evening).
    Determines:
    - Which products are USEFUL and recommended right now.
    - Which products should NOT be used right now (e.g. Retinol/AHA in daytime sun, Sunscreen at night).
    - Which products require caution based on humidity/temperature texture clash.
    """
    from datetime import datetime

    temp = weather_data.get("temperature", 28.0)
    humidity = weather_data.get("humidity", 55)
    uv_index = weather_data.get("uv_index", 6)
    aqi = weather_data.get("aqi", 70)
    condition = weather_data.get("condition", "Partly Cloudy")
    city = weather_data.get("city", "Local Area")

    # Determine time of day (if not provided, check current hour)
    if not selected_time_of_day:
        current_hour = datetime.now().hour
        if 5 <= current_hour < 17:
            time_of_day = "morning"
        else:
            time_of_day = "evening"
    else:
        time_of_day = selected_time_of_day.lower()

    is_daytime = time_of_day in ["morning", "day", "afternoon"]
    evaluated_steps = []

    useful_count = 0
    not_recommended_count = 0
    caution_count = 0

    for step in routine_steps:
        prod = step.product
        ing_categories = {i.category for i in prod.ingredients.all()}
        ing_names = [i.name for i in prod.ingredients.all()]

        suitability = "optimal" # "optimal", "caution", "not_recommended"
        badge = "USEFUL RIGHT NOW"
        is_useful = True
        reasons = []
        action_advice = ""

        has_photosensitizer = (
            'retinoid' in ing_categories 
            or 'exfoliant' in ing_categories 
            or prod.category == 'exfoliant' 
            or prod.time_of_day == 'evening'
            or any(any(k in name.lower() for k in ['glycolic', 'salicylic', 'lactic', 'mandelic', 'retinol', 'retinal', 'tretinoin', 'adapalene', 'aha', 'bha']) for name in ing_names)
        )

        # Check 1: Sunscreen / Daytime UV Protection
        if prod.category == 'sunscreen':
            if is_daytime:
                suitability = "optimal"
                badge = "USEFUL RIGHT NOW"
                is_useful = True
                reasons.append(f"Crucial daytime shield. Current UV Index is {uv_index}. Apply 15 mins before stepping out.")
                action_advice = "Apply as the final step of your daytime routine."
            else:
                suitability = "not_recommended"
                badge = "DO NOT USE RIGHT NOW"
                is_useful = False
                reasons.append("Do NOT use at night. Sunscreen filters are formulated for UV deflection and should not sit on skin overnight while sleeping.")
                action_advice = "Skip this formula tonight. Use in morning routines only."

        # Check 2: Strong Photosensitizing Actives (Retinoids, Exfoliating Acids)
        elif has_photosensitizer:
            if is_daytime:
                suitability = "not_recommended"
                badge = "DO NOT USE RIGHT NOW"
                is_useful = False
                actives_str = ", ".join([name for name in ing_names if any(k in name.lower() for k in ['retinol', 'acid', 'aha', 'bha', 'peel', 'glycolic', 'salicylic', 'lactic'])] or ['Potent Active'])
                reasons.append(f"Do NOT use right now in daytime. {actives_str} degrades in sunlight and significantly increases UV sunburn risk & hyperpigmentation under current UV index ({uv_index}).")
                action_advice = "Hold back for your Evening Routine when UV index is 0."
            else:
                suitability = "optimal"
                badge = "USEFUL RIGHT NOW"
                is_useful = True
                reasons.append("Optimal for evening application. Cellular turnover and active skin renewal peak overnight without UV light degradation.")
                action_advice = "Apply tonight after cleansing and before your night moisturizer."

        # Check 3: Antioxidants & Vitamin C
        elif 'antioxidant' in ing_categories:
            if is_daytime:
                suitability = "optimal"
                badge = "USEFUL RIGHT NOW"
                is_useful = True
                reasons.append(f"Highly beneficial morning formula. Antioxidants neutralize daytime UV free radicals and air pollutants (AQI {aqi}).")
                action_advice = "Apply in AM before moisturizer and sunscreen."
            else:
                suitability = "optimal"
                badge = "USEFUL RIGHT NOW"
                is_useful = True
                reasons.append("Safe for evening use to assist nighttime cellular repair.")
                action_advice = "Safe to use tonight."

        # Check 4: Climate Texture Considerations (High Humidity & Heat vs Cold & Dry)
        elif humidity >= 65 and temp >= 28 and prod.texture == 'rich_cream':
            suitability = "caution"
            badge = "USE WITH CAUTION"
            is_useful = True
            reasons.append(f"Current weather is Hot & Humid ({temp}°C, {humidity}% humidity). Heavy rich creams can feel occlusive and trap sweat.")
            action_advice = "Apply a thin layer only, or consider switching to a lightweight water-gel during humid daytime hours."

        elif humidity <= 40 and prod.hydration_level in ['moderate', 'deep']:
            suitability = "optimal"
            badge = "USEFUL RIGHT NOW"
            is_useful = True
            reasons.append(f"Low ambient humidity ({humidity}%). Essential right now to counteract rapid transepidermal moisture loss.")
            action_advice = "Generously apply to seal in skin hydration."

        # Check 5: Cleansers & Hydrating Toners
        elif prod.category in ['cleanser', 'toner']:
            suitability = "optimal"
            badge = "USEFUL RIGHT NOW"
            is_useful = True
            if is_daytime:
                reasons.append("Removes overnight excess sebum and preps skin for daytime hydration.")
                action_advice = "Use to start your day fresh."
            else:
                reasons.append(f"Essential evening step to wash off daytime sunscreen, grime, and particulate matter (AQI {aqi}).")
                action_advice = "Cleanse thoroughly tonight."

        else:
            suitability = "optimal"
            badge = "USEFUL RIGHT NOW"
            is_useful = True
            reasons.append("Safe and compatible with current environmental conditions.")
            action_advice = "Follow standard application frequency."

        if suitability == "optimal":
            useful_count += 1
        elif suitability == "not_recommended":
            not_recommended_count += 1
        else:
            caution_count += 1

        evaluated_steps.append({
            "step_id": step.id,
            "product_id": prod.id,
            "product_name": prod.name,
            "image_url": prod.effective_image_url,
            "category": prod.get_category_display(),
            "texture": prod.get_texture_display(),
            "time_of_day": step.time_of_day or prod.time_of_day,
            "time_of_day_spec": prod.time_of_day,
            "stage_number": step.stage_number,
            "stage_name": step.stage_name,
            "frequency": step.frequency,
            "completed": step.completed,
            "is_useful_now": is_useful,
            "suitability": suitability, # 'optimal', 'caution', 'not_recommended'
            "suitability_badge": badge,
            "suitability_reason": " ".join(reasons),
            "action_advice": action_advice
        })

    # Summary text
    summary_parts = []
    if is_daytime:
        summary_parts.append(f"☀️ Current Daytime Conditions ({city}): {temp}°C, {humidity}% Humidity, UV Index {uv_index} ({condition}).")
        if not_recommended_count > 0:
            summary_parts.append(f"{useful_count} product(s) are recommended right now, while {not_recommended_count} product(s) should NOT be used in daytime sun (photosensitizing).")
        else:
            summary_parts.append(f"All {useful_count} formulas are suitable for daytime application.")
    else:
        summary_parts.append(f"🌙 Evening / Night Conditions ({city}): {temp}°C, {humidity}% Humidity (UV 0).")
        if not_recommended_count > 0:
            summary_parts.append(f"{useful_count} product(s) are optimal for nighttime renewal; {not_recommended_count} daytime formula (e.g. Sunscreen) should be skipped tonight.")
        else:
            summary_parts.append(f"All {useful_count} formulas are optimal for your evening skincare routine.")

    return {
        "weather": {
            "temperature": temp,
            "humidity": humidity,
            "uv_index": uv_index,
            "aqi": aqi,
            "condition": condition,
            "city": city,
            "time_of_day": time_of_day,
            "is_daytime": is_daytime,
            "summary": " ".join(summary_parts)
        },
        "useful_count": useful_count,
        "not_recommended_count": not_recommended_count,
        "caution_count": caution_count,
        "steps": evaluated_steps
    }
