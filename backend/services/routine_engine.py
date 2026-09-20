"""
Progressive Routine Generation and Automated Delivery Schedule Engine.
Determines safe multi-week routine staging to prevent skin barrier shock.
Calculates smart replenishment and delivery schedules based on bottle lifespan and application frequency.
"""

from typing import List, Dict, Any, Optional
from datetime import date, timedelta
from products.models import Product
from routines.models import Routine, RoutineStep, RoutineDeliveryItem

def generate_progressive_routine(
    product_ids: List[int],
    routine_name: str = "My Joyory Progressive Routine",
    user=None,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates a multi-stage progressive skincare routine.
    Stage 1: Foundation (Cleanser, Barrier Moisturizer, Sunscreen) - Weeks 1-2
    Stage 2: Gentle Hydration & Calming Actives - Week 3
    Stage 3: Targeted Treatments & Strong Actives (Retinoids, Acids) - Week 4+
    """
    products = list(Product.objects.filter(id__in=product_ids).prefetch_related('ingredients'))
    if not products:
        raise ValueError("At least one valid product is required to generate a routine.")

    routine = Routine.objects.create(
        name=routine_name,
        user=user if user and user.is_authenticated else None,
        session_id=session_id
    )

    stage1_products = []
    stage2_products = []
    stage3_products = []

    for prod in products:
        ing_categories = {i.category for i in prod.ingredients.all()}
        
        # High intensity active (Retinoids, Exfoliants/Acids) -> Stage 3
        if ('retinoid' in ing_categories or 'exfoliant' in ing_categories or prod.active_level == 'high' or prod.category == 'exfoliant'):
            stage3_products.append(prod)
        # Foundation essentials (Cleansers, Moisturizers, Sunscreens) -> Stage 1
        elif prod.category in ['cleanser', 'moisturizer', 'sunscreen'] and prod.active_level == 'low':
            stage1_products.append(prod)
        # Toners, gentle serums, moderate actives -> Stage 2
        else:
            stage2_products.append(prod)

    # If stage 1 is empty, assign the gentlest products to stage 1
    if not stage1_products:
        if stage2_products:
            stage1_products.append(stage2_products.pop(0))
        elif stage3_products:
            stage1_products.append(stage3_products.pop(0))

    order = 1
    created_steps = []

    # Stage 1: Weeks 1-2 (Foundation Barrier Building)
    for prod in stage1_products:
        step = RoutineStep.objects.create(
            routine=routine,
            product=prod,
            stage_number=1,
            stage_name="Stage 1: Barrier Foundation",
            week_start=1,
            week_end=2,
            frequency=prod.usage_frequency,
            time_of_day=prod.time_of_day,
            order=order
        )
        created_steps.append(step)
        order += 1

    # Stage 2: Week 3 (Hydration & Gentle Actives)
    for prod in stage2_products:
        step = RoutineStep.objects.create(
            routine=routine,
            product=prod,
            stage_number=2,
            stage_name="Stage 2: Targeted Prep & Hydration",
            week_start=3,
            week_end=3,
            frequency="daily" if prod.usage_frequency == "daily" else "every_other_day",
            time_of_day=prod.time_of_day,
            order=order
        )
        created_steps.append(step)
        order += 1

    # Stage 3: Week 4+ (Active Integration)
    for prod in stage3_products:
        step = RoutineStep.objects.create(
            routine=routine,
            product=prod,
            stage_number=3,
            stage_name="Stage 3: Concentrated Active Integration",
            week_start=4,
            week_end=6,
            frequency="2_3_times_per_week", # gentle introductory cadence for strong actives
            time_of_day="evening" if prod.category in ['exfoliant', 'treatment'] or any(i.category == 'retinoid' for i in prod.ingredients.all()) else prod.time_of_day,
            order=order
        )
        created_steps.append(step)
        order += 1

    # Generate Delivery / Reorder Items
    delivery_items = generate_delivery_schedule(routine)

    # Return structured roadmap response using the single source of truth
    roadmap = get_routine_staged_roadmap(routine)

    return {
        "routine_id": routine.id,
        "name": routine.name,
        "total_steps": len(created_steps),
        "journey_summary": roadmap["journey_summary"],
        "stages": roadmap["stages"],
        "adaptive_guidance": get_routine_adaptive_guidance(routine),
        "delivery_schedule": [
            {
                "product_name": item.product.name,
                "suggested_reorder_date": item.suggested_reorder_date.isoformat(),
                "frequency_weeks": item.frequency_weeks,
                "reason": item.reason
            }
            for item in delivery_items
        ]
    }


def get_routine_adaptive_guidance(routine: Routine) -> Dict[str, Any]:
    """
    Evaluates recent user-reported daily skin feedback to produce adaptive routine guidance.
    Strictly non-diagnostic skincare guidance for routine pacing and barrier tolerance.
    """
    recent_feedbacks = list(routine.skin_feedbacks.all()[:5])
    if not recent_feedbacks:
        return {
            "status": "baseline",
            "level": "info",
            "title": "Roadmap Adaptation Baseline",
            "message": "Log your daily skin feel after completing today's routine to receive personalized tolerance guidance.",
            "has_warning": False,
            "recent_count": 0,
            "irritation_count": 0
        }

    irritation_count = sum(1 for f in recent_feedbacks if f.skin_feel == 'irritated')
    dry_count = sum(1 for f in recent_feedbacks if f.skin_feel == 'dry')

    if irritation_count >= 2:
        return {
            "status": "irritation_caution",
            "level": "caution",
            "title": "⚠️ Tolerance Guidance: User-Reported Irritation",
            "message": (
                "Your recent feedback shows user-reported irritation. Skincare guidance suggests taking a rest night, "
                "reinforcing your barrier moisturizer, and holding back the introduction of stronger actives until comfort returns."
            ),
            "recommendation": "Review active application frequency and prioritize gentle barrier hydration.",
            "has_warning": True,
            "recent_count": len(recent_feedbacks),
            "irritation_count": irritation_count
        }
    elif irritation_count == 1:
        return {
            "status": "mild_caution",
            "level": "mild_caution",
            "title": "Skincare Guidance: Mild Sensitivity Noted",
            "message": "One recent log reported irritation. Ensure skin is fully dry before applying concentrated serums, and buffer with barrier moisturizer if needed.",
            "recommendation": "Monitor how your skin feels over the next 24–48 hours.",
            "has_warning": False,
            "recent_count": len(recent_feedbacks),
            "irritation_count": 1
        }
    elif dry_count >= 2:
        return {
            "status": "dryness_support",
            "level": "info",
            "title": "Hydration Guidance: Moisture Support Needed",
            "message": "Multiple recent logs noted skin feeling a little dry. Consider layering an extra pump of hydrating essence or sealing with your barrier cream.",
            "recommendation": "Maintain gentle cleansing without hot water stripping.",
            "has_warning": False,
            "recent_count": len(recent_feedbacks),
            "dry_count": dry_count
        }
    else:
        return {
            "status": "optimal",
            "level": "optimal",
            "title": "✓ Comfortable Routine Progression",
            "message": "Comfortable skin tolerance reported. Your progressive adaptation schedule is proceeding smoothly along your 6-week roadmap.",
            "recommendation": "Continue following your scheduled morning and evening cadence.",
            "has_warning": False,
            "recent_count": len(recent_feedbacks),
            "irritation_count": 0
        }


def get_routine_staged_roadmap(routine: Routine) -> Dict[str, Any]:
    """
    Computes the comprehensive 6-week multi-stage roadmap for a routine.
    Stage 1: Barrier Foundation (Weeks 1–2, 14 days)
    Stage 2: Targeted Prep & Hydration (Week 3, 7 days)
    Stage 3: Concentrated Active Integration (Weeks 4–6, 21 days)
    """
    today = date.today()
    routine_start = routine.created_at.date() if routine.created_at else today
    days_since_start = max(0, (today - routine_start).days)

    # Current week calculation (1 to 6)
    current_week = min(6, max(1, (days_since_start // 7) + 1))
    current_stage_num = routine.current_stage

    # Stage specifications
    stage_meta = {
        1: {
            "stage_number": 1,
            "stage_name": "Barrier Foundation",
            "duration": "Weeks 1–2",
            "week_start": 1,
            "week_end": 2,
            "days_total": 14,
            "start_offset": 0,
            "why_this_stage": "Build a stable skincare foundation before introducing stronger active ingredients.",
            "description": "Establishes a strong lipid matrix, optimizes epidermal hydration, and primes the acid mantle using gentle cleansers and barrier moisture."
        },
        2: {
            "stage_number": 2,
            "stage_name": "Targeted Prep & Hydration",
            "duration": "Week 3",
            "week_start": 3,
            "week_end": 3,
            "days_total": 7,
            "start_offset": 14,
            "why_this_stage": "Targeted cellular hydration and antioxidant protection to prep skin for deeper renewal.",
            "description": "Introduces gentle water-binding humectants and daytime antioxidant defenses while maintaining barrier stability."
        },
        3: {
            "stage_number": 3,
            "stage_name": "Concentrated Active Integration",
            "duration": "Weeks 4–6",
            "week_start": 4,
            "week_end": 6,
            "days_total": 21,
            "start_offset": 21,
            "why_this_stage": "Cautiously introduce concentrated active exfoliants and cell-turnover treatments with built-in rest days.",
            "description": "Accelerates epidermal renewal and targets persistent concerns using potent retinoids and chemical exfoliants on alternating evenings."
        }
    }

    # Fetch all steps for this routine
    steps = list(routine.steps.select_related('product').prefetch_related('progress_entries').order_by('stage_number', 'order'))

    stages_result = []

    for s_num in [1, 2, 3]:
        meta = stage_meta[s_num]
        s_start_date = routine_start + timedelta(days=meta["start_offset"])
        s_end_date = s_start_date + timedelta(days=meta["days_total"])

        # Determine stage status
        if s_num < current_stage_num:
            stage_status = "completed"
            days_progress = meta["days_total"]
            days_remaining = 0
            next_stage_text = "Completed"
        elif s_num == current_stage_num:
            stage_status = "current"
            # Calculate days elapsed in this stage
            elapsed_in_stage = max(1, min((today - s_start_date).days + 1, meta["days_total"])) if today >= s_start_date else 1
            days_progress = elapsed_in_stage
            days_remaining = max(0, meta["days_total"] - days_progress)
            next_stage_text = f"Next stage starts in {days_remaining} days" if days_remaining > 0 else "Transitioning to next stage"
        else:
            stage_status = "upcoming"
            days_progress = 0
            days_remaining = meta["days_total"]
            days_until_start = max(0, (s_start_date - today).days)
            next_stage_text = f"Starts in {days_until_start} days"

        # Products belonging to this stage
        stage_steps = [s for s in steps if s.stage_number == s_num]
        products_list = []
        for step in stage_steps:
            # Latest completion date if completed
            latest_progress = step.progress_entries.filter(completed=True).first()
            completed_at_str = None
            if latest_progress and latest_progress.created_at:
                completed_at_str = latest_progress.created_at.strftime("%I:%M %p")

            # Format AM/PM display
            time_display = "☀️ Morning" if step.time_of_day == "morning" else ("🌙 Evening" if step.time_of_day == "evening" else "☀️+🌙 AM + PM")

            products_list.append({
                "step_id": step.id,
                "product_id": step.product.id,
                "product_name": step.product.name,
                "category": step.product.get_category_display(),
                "image_url": step.product.effective_image_url,
                "stage": s_num,
                "week_range": meta["duration"],
                "frequency": step.frequency,
                "frequency_display": step.frequency.replace('_', ' ').capitalize(),
                "time_of_day": step.time_of_day,
                "time_display": time_display,
                "start_date": s_start_date.strftime("%b %d"),
                "start_date_iso": s_start_date.isoformat(),
                "expected_completion_date": s_end_date.strftime("%b %d"),
                "expected_completion_date_iso": s_end_date.isoformat(),
                "completed": step.completed,
                "status_label": "Completed" if step.completed else "Scheduled",
                "completed_at": completed_at_str
            })

        stages_result.append({
            "stage": s_num,
            "stage_number": s_num,
            "stage_name": meta["stage_name"],
            "duration": meta["duration"],
            "week_start": meta["week_start"],
            "week_end": meta["week_end"],
            "why_this_stage": meta["why_this_stage"],
            "description": meta["description"],
            "status": stage_status,
            "status_label": "CURRENT STAGE" if stage_status == "current" else ("COMPLETED" if stage_status == "completed" else "UPCOMING"),
            "start_date": s_start_date.strftime("%b %d, %Y"),
            "start_date_iso": s_start_date.isoformat(),
            "expected_completion_date": s_end_date.strftime("%b %d, %Y"),
            "expected_completion_date_iso": s_end_date.isoformat(),
            "days_total": meta["days_total"],
            "days_progress": days_progress,
            "days_remaining": days_remaining,
            "progress_ratio": f"{days_progress} / {meta['days_total']} days",
            "progress_percentage": round((days_progress / meta["days_total"]) * 100, 1),
            "next_stage_text": next_stage_text,
            "products": products_list
        })

    # Summary
    curr_stage_name = stage_meta.get(current_stage_num, {}).get("stage_name", "Barrier Foundation")
    next_stage_name = stage_meta.get(current_stage_num + 1, {}).get("stage_name", "Final Maintenance") if current_stage_num < 3 else "Routine Complete"

    current_stage_info = next((s for s in stages_result if s["stage_number"] == current_stage_num), stages_result[0])

    journey_summary = {
        "title": "Your Skincare Journey",
        "current_stage_number": current_stage_num,
        "current_stage_name": curr_stage_name,
        "current_stage_full": f"Stage {current_stage_num} — {curr_stage_name}",
        "current_week": current_week,
        "current_week_text": f"Week {current_week} of 6",
        "overall_progress": routine.progress_percentage,
        "total_stages": 3,
        "total_weeks": 6,
        "total_products": len(steps),
        "next_stage_name": next_stage_name,
        "days_remaining_in_stage": current_stage_info["days_remaining"],
        "days_remaining_text": f"{current_stage_info['days_remaining']} days remaining" if current_stage_info['days_remaining'] > 0 else "Stage Complete"
    }

    return {
        "journey_summary": journey_summary,
        "stages": stages_result
    }


def generate_delivery_schedule(routine: Routine) -> List[RoutineDeliveryItem]:
    """
    Computes suggested replenishment dates based on usage frequency and standard bottle size.
    """
    items = []
    today = date.today()

    for step in routine.steps.select_related('product').all():
        prod = step.product
        base_days = prod.typical_duration_days # e.g. 60 days standard daily

        # Adjust based on frequency
        if step.frequency == "twice_daily":
            lifespan_days = int(base_days * 0.6)
        elif step.frequency in ["2_3_times_per_week", "3_times_per_week"]:
            lifespan_days = int(base_days * 1.8)
        elif step.frequency == "weekly":
            lifespan_days = int(base_days * 3.5)
        else:
            lifespan_days = base_days

        reorder_date = today + timedelta(days=lifespan_days)
        freq_weeks = max(4, round(lifespan_days / 7))

        delivery_item, _ = RoutineDeliveryItem.objects.update_or_create(
            routine=routine,
            product=prod,
            defaults={
                "quantity": 1,
                "suggested_reorder_date": reorder_date,
                "frequency_weeks": freq_weeks,
                "active": True,
                "reason": (
                    f"Calculated from estimated bottle volume ({base_days} days daily usage) "
                    f"applied at '{step.frequency}' frequency."
                )
            }
        )
        items.append(delivery_item)

    return items


def get_active_stage_for_date(routine: Routine, target_date: date) -> int:
    """
    Determines which progressive routine stage is active for a target date.
    Stage 1: Barrier Foundation (Weeks 1-2, days 0-13)
    Stage 2: Targeted Prep & Hydration (Week 3, days 14-20)
    Stage 3: Concentrated Active Integration (Weeks 4-6, days 21+)
    """
    routine_start = routine.created_at.date() if routine.created_at else target_date
    days_since_start = max(0, (target_date - routine_start).days)
    current_week = min(6, max(1, (days_since_start // 7) + 1))

    if current_week <= 2:
        cal_stage = 1
    elif current_week == 3:
        cal_stage = 2
    else:
        cal_stage = 3

    return max(cal_stage, routine.current_stage)


def is_step_frequency_active_on_date(step: RoutineStep, routine_start: date, target_date: date) -> bool:
    """
    Evaluates whether a product is scheduled on the given date based on its frequency cadence.
    - 'daily', 'twice_daily', 'both': Every day
    - 'every_other_day': Alternating days (days_since_start % 2 == 0)
    - '2_3_times_per_week', '3_times_per_week': 3 spaced days per 7-day week (cycle_day in [0, 2, 4])
    - 'weekly', 'once_weekly': Once per week (cycle_day == 0)
    """
    freq = (step.frequency or "daily").lower().strip()
    if freq in ["daily", "twice_daily", "everyday", "both"]:
        return True

    days_since_start = max(0, (target_date - routine_start).days)
    cycle_day = days_since_start % 7

    if freq == "every_other_day":
        return (days_since_start % 2) == 0
    elif freq in ["2_3_times_per_week", "3_times_per_week", "2-3_times_per_week", "2_to_3_times_per_week"]:
        # 3 spaced application days per week (e.g. Day 0, Day 2, Day 4 of the 7-day cycle)
        return cycle_day in [0, 2, 4]
    elif freq in ["weekly", "once_weekly"]:
        return cycle_day == 0

    return True


def is_step_applicable_for_date(step: RoutineStep, routine: Routine, target_date: date) -> bool:
    """
    Filters routine steps for Daily Tracker based on:
    1. Current date
    2. RoutineStep scheduled start date / week window
    3. Current stage
    4. Frequency
    """
    routine_start = routine.created_at.date() if routine.created_at else target_date

    # 1. Scheduled start date check: product must not start before its scheduled week offset
    step_start_offset_days = max(0, (step.week_start - 1) * 7)
    step_start_date = routine_start + timedelta(days=step_start_offset_days)
    if target_date < step_start_date:
        return False

    # 2. Stage window check: product stage must be active or completed (not future)
    active_stage = get_active_stage_for_date(routine, target_date)
    if step.stage_number > active_stage:
        return False

    # 3. Frequency cadence check (rest days for actives like retinoids)
    if not is_step_frequency_active_on_date(step, routine_start, target_date):
        return False

    return True


