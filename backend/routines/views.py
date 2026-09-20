from datetime import date, datetime, timedelta
import uuid
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Routine, RoutineStep, RoutineProgress, RoutineDeliveryItem, DailySkinFeedback
from .serializers import (
    RoutineSerializer,
    RoutineStepSerializer,
    RoutineDeliveryItemSerializer,
    GenerateRoutineInputSerializer,
    CompleteStepInputSerializer,
    DailySkinFeedbackSerializer,
    DailySkinFeedbackInputSerializer
)
from services.routine_engine import (
    generate_progressive_routine,
    get_routine_adaptive_guidance,
    get_routine_staged_roadmap,
    get_active_stage_for_date,
    is_step_applicable_for_date
)
from services.climate_service import default_climate_service
from services.climate_engine import evaluate_daily_tracker_weather_timing


class GenerateRoutineView(APIView):
    """
    Generates a staged, multi-week progressive routine based on product active levels and categories.
    Avoids introducing conflicting active ingredients simultaneously.
    """
    def post(self, request):
        serializer = GenerateRoutineInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        product_ids = serializer.validated_data['product_ids']
        name = serializer.validated_data.get('name', 'My Joyory Routine')
        session_id = serializer.validated_data.get('session_id') or request.headers.get('X-Session-ID')

        try:
            routine_data = generate_progressive_routine(
                product_ids=product_ids,
                routine_name=name,
                user=request.user if request.user.is_authenticated else None,
                session_id=session_id
            )
            return Response(routine_data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


def get_user_routine(request, routine_id, prefetch=None):
    """
    Retrieves a routine ensuring strict user ownership isolation.
    Authenticated users can only access their own routines.
    Unauthenticated guests can only access unowned routines matching their session_id.
    """
    qs = Routine.objects.all()
    if prefetch:
        qs = qs.prefetch_related(*prefetch)
    try:
        routine = qs.get(id=routine_id)
    except Routine.DoesNotExist:
        return None

    if request.user and request.user.is_authenticated:
        if routine.user and routine.user != request.user:
            return None
    else:
        # Unauthenticated request cannot access any authenticated user's routine
        if routine.user is not None:
            return None
        session_id = request.headers.get('X-Session-ID') or request.query_params.get('session_id')
        if routine.session_id and session_id and routine.session_id != session_id:
            return None

    return routine


class RoutineListView(APIView):
    """
    Lists routines for the current user or guest session.
    """
    def get(self, request):
        session_id = request.query_params.get('session_id') or request.headers.get('X-Session-ID')
        
        if request.user and request.user.is_authenticated:
            routines = Routine.objects.filter(user=request.user).order_by('-created_at')
        elif session_id:
            routines = Routine.objects.filter(session_id=session_id, user=None).order_by('-created_at')
        else:
            routines = Routine.objects.none()

        serializer = RoutineSerializer(routines, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RoutineDetailView(APIView):
    """
    Full routine details including stages, weekly timing, and progress.
    """
    def get(self, request, id):
        routine = get_user_routine(request, id, prefetch=['steps__product', 'delivery_items'])
        if not routine:
            return Response({"error": "Routine not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = RoutineSerializer(routine)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CompleteStepView(APIView):
    """
    Logs micro-tracking completion of a daily routine step.
    If all steps are completed and auto_reorder_enabled is True, automatically triggers replenishment reorder!
    """
    def post(self, request, id):
        serializer = CompleteStepInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        routine = get_user_routine(request, id, prefetch=['steps', 'delivery_items'])
        if not routine:
            return Response({"error": "Routine not found."}, status=status.HTTP_404_NOT_FOUND)

        step_id = serializer.validated_data['step_id']
        try:
            step = routine.steps.get(id=step_id)
        except RoutineStep.DoesNotExist:
            return Response({"error": f"Step #{step_id} not found in Routine #{id}."}, status=status.HTTP_404_NOT_FOUND)

        session = serializer.validated_data.get('session', 'all')
        completed = serializer.validated_data.get('completed', True)
        entry_date = serializer.validated_data.get('date') or date.today()
        notes = serializer.validated_data.get('notes', '')

        # Create or update progress entry for this specific session
        progress_entry, _ = RoutineProgress.objects.update_or_create(
            routine_step=step,
            date=entry_date,
            session=session,
            defaults={"completed": completed, "notes": notes}
        )

        # Update step's session completion flags independently
        if session == 'morning':
            step.morning_completed = completed
        elif session == 'evening':
            step.evening_completed = completed
        else:
            step.morning_completed = completed
            step.evening_completed = completed

        # Evaluate overall step completion based on frequency/time_of_day
        if step.time_of_day == 'both':
            step.completed = (step.morning_completed and step.evening_completed)
        elif step.time_of_day == 'morning':
            step.completed = step.morning_completed
        elif step.time_of_day == 'evening':
            step.completed = step.evening_completed
        else:
            step.completed = completed

        step.save()


        # Check if entire routine is now completed
        all_steps = routine.steps.all()
        total_steps = all_steps.count()
        completed_steps = all_steps.filter(completed=True).count()
        is_routine_completed = (total_steps > 0 and completed_steps == total_steps)

        auto_reordered_now = False
        reorder_info = None

        if is_routine_completed:
            routine.status = 'completed'
            if routine.auto_reorder_enabled and not routine.auto_reordered:
                routine.auto_reordered = True
                routine.auto_reorder_date = timezone.now()
                order_code = f"JOY-REORDER-{routine.id}-{uuid.uuid4().hex[:6].upper()}"
                routine.auto_reorder_order_id = order_code

                # Mark delivery items as auto_reordered
                for item in routine.delivery_items.all():
                    item.status = 'auto_reordered'
                    item.tracking_number = f"EXP-IN-{uuid.uuid4().hex[:8].upper()}"
                    item.save()

                auto_reordered_now = True
                reorder_info = {
                    "order_id": order_code,
                    "reorder_date": routine.auto_reorder_date.isoformat(),
                    "items_count": routine.delivery_items.count(),
                    "status": "confirmed_and_dispatched"
                }
            routine.save()
        else:
            if routine.status == 'completed':
                routine.status = 'active'
            routine.save()

        return Response({
            "message": f"Step marked as {'completed' if completed else 'pending'}.",
            "step_id": step.id,
            "completed": step.completed,
            "progress_entry_id": progress_entry.id,
            "current_routine_progress": routine.progress_percentage,
            "is_routine_completed": is_routine_completed,
            "auto_reorder_enabled": routine.auto_reorder_enabled,
            "auto_reordered": routine.auto_reordered,
            "auto_reorder_order_id": routine.auto_reorder_order_id,
            "auto_reordered_now": auto_reordered_now,
            "reorder_info": reorder_info
        }, status=status.HTTP_200_OK)


class ToggleAutoReorderView(APIView):
    """
    Toggles the automatic replenishment setting on routine completion.
    """
    def post(self, request, id):
        routine = get_user_routine(request, id)
        if not routine:
            return Response({"error": "Routine not found."}, status=status.HTTP_404_NOT_FOUND)

        enabled = request.data.get('enabled')
        if enabled is not None:
            routine.auto_reorder_enabled = bool(enabled)
        else:
            routine.auto_reorder_enabled = not routine.auto_reorder_enabled
        routine.save()

        return Response({
            "routine_id": routine.id,
            "auto_reorder_enabled": routine.auto_reorder_enabled,
            "message": f"Automatic replenishment {'enabled' if routine.auto_reorder_enabled else 'disabled'}."
        }, status=status.HTTP_200_OK)


class ToggleDeliveryItemAutoReorderView(APIView):
    """
    Toggles or sets the active auto-reorder status for a specific routine delivery item.
    """
    def post(self, request, item_id, id=None):
        try:
            if id:
                item = RoutineDeliveryItem.objects.select_related('product', 'routine').get(id=item_id, routine_id=id)
            else:
                item = RoutineDeliveryItem.objects.select_related('product', 'routine').get(id=item_id)
        except RoutineDeliveryItem.DoesNotExist:
            return Response({"error": "Delivery item not found."}, status=status.HTTP_404_NOT_FOUND)

        if request.user and request.user.is_authenticated:
            if item.routine.user and item.routine.user != request.user:
                return Response({"error": "Delivery item not found."}, status=status.HTTP_404_NOT_FOUND)
        elif item.routine.user is not None:
            return Response({"error": "Delivery item not found."}, status=status.HTTP_404_NOT_FOUND)

        active = request.data.get('active')
        if active is not None:
            item.active = bool(active)
        else:
            item.active = not item.active
        item.save()

        return Response({
            "item_id": item.id,
            "routine_id": item.routine_id,
            "product_id": item.product_id,
            "product_name": item.product.name,
            "active": item.active,
            "message": f"Auto-reorder for '{item.product.name}' is now {'enabled' if item.active else 'paused'}."
        }, status=status.HTTP_200_OK)


class CompleteAllStepsView(APIView):
    """
    Marks all steps in a routine as completed at once (ideal for quick testing & verifying auto-reorder).
    """
    def post(self, request, id):
        routine = get_user_routine(request, id, prefetch=['steps__product', 'delivery_items'])
        if not routine:
            return Response({"error": "Routine not found."}, status=status.HTTP_404_NOT_FOUND)

        for step in routine.steps.all():
            step.completed = True
            step.morning_completed = True
            step.evening_completed = True
            step.save()
            RoutineProgress.objects.update_or_create(
                routine_step=step,
                date=date.today(),
                session='all',
                defaults={"completed": True, "notes": "Completed during full routine review"}
            )


        routine.status = 'completed'
        auto_reordered_now = False
        reorder_info = None

        if routine.auto_reorder_enabled and not routine.auto_reordered:
            routine.auto_reordered = True
            routine.auto_reorder_date = timezone.now()
            order_code = f"JOY-REORDER-{routine.id}-{uuid.uuid4().hex[:6].upper()}"
            routine.auto_reorder_order_id = order_code

            for item in routine.delivery_items.all():
                item.status = 'auto_reordered'
                item.tracking_number = f"EXP-IN-{uuid.uuid4().hex[:8].upper()}"
                item.save()

            auto_reordered_now = True
            reorder_info = {
                "order_id": order_code,
                "reorder_date": routine.auto_reorder_date.isoformat(),
                "items_count": routine.delivery_items.count(),
                "status": "confirmed_and_dispatched"
            }

        routine.save()

        return Response({
            "routine_id": routine.id,
            "message": "All steps completed successfully!",
            "progress_percentage": 100.0,
            "is_routine_completed": True,
            "auto_reorder_enabled": routine.auto_reorder_enabled,
            "auto_reordered": routine.auto_reordered,
            "auto_reorder_order_id": routine.auto_reorder_order_id,
            "auto_reordered_now": auto_reordered_now,
            "reorder_info": reorder_info
        }, status=status.HTTP_200_OK)


class RoutineProgressView(APIView):
    """
    Calculates detailed metrics for routine progress tracking, enriched with
    morning and evening routine separation, environmental guidance, and adaptive tolerance feedback.
    Filters steps based on scheduled start date, current stage, and frequency cadence.
    """
    def get(self, request, id):
        routine = get_user_routine(request, id, prefetch=['steps__product__ingredients', 'steps__progress_entries'])
        if not routine:
            return Response({"error": "Routine not found."}, status=status.HTTP_404_NOT_FOUND)

        steps_qs = routine.steps.select_related('product').prefetch_related('product__ingredients', 'progress_entries')
        total = steps_qs.count()
        completed = sum(1 for s in steps_qs if s.completed)
        pct = round((completed / total * 100), 1) if total > 0 else 0.0

        lat = request.query_params.get('latitude')
        lon = request.query_params.get('longitude')
        city = request.query_params.get('city')
        time_of_day = request.query_params.get('time_of_day') # 'morning' | 'evening'
        week_param = request.query_params.get('week')
        date_param = request.query_params.get('date')

        # Compute evaluated date and active week/stage
        routine_start = routine.created_at.date() if routine.created_at else date.today()
        if week_param:
            try:
                target_week = int(week_param)
                eval_date = routine_start + timedelta(days=(target_week - 1) * 7)
            except ValueError:
                eval_date = date.today()
        elif date_param:
            try:
                eval_date = date.fromisoformat(date_param)
            except ValueError:
                eval_date = date.today()
        else:
            eval_date = date.today()

        days_since_start = max(0, (eval_date - routine_start).days)
        current_week = min(6, max(1, (days_since_start // 7) + 1))
        active_stage = get_active_stage_for_date(routine, eval_date)

        # Filter steps applicable to the user's CURRENT stage, CURRENT date, and frequency cadence
        today_steps = [
            s for s in steps_qs
            if is_step_applicable_for_date(s, routine, eval_date)
        ]

        # Fetch environmental conditions
        weather_data = default_climate_service.get_climate_data(
            latitude=float(lat) if lat is not None else None,
            longitude=float(lon) if lon is not None else None,
            city=city
        )

        timing_analysis = evaluate_daily_tracker_weather_timing(
            routine_steps=today_steps,
            weather_data=weather_data,
            selected_time_of_day=time_of_day
        )

        # Build progress timestamp lookups for morning and evening strictly for eval_date
        step_progress_morning_map = {}
        step_progress_evening_map = {}
        for s in today_steps:
            if s.time_of_day == 'morning':
                p_morning = s.progress_entries.filter(date=eval_date, completed=True).first()
            else:
                p_morning = s.progress_entries.filter(date=eval_date, session='morning', completed=True).first()

            if p_morning and p_morning.created_at:
                step_progress_morning_map[s.id] = p_morning.created_at.strftime("%I:%M %p")

            if s.time_of_day == 'evening':
                p_evening = s.progress_entries.filter(date=eval_date, completed=True).first()
            else:
                p_evening = s.progress_entries.filter(date=eval_date, session='evening', completed=True).first()

            if p_evening and p_evening.created_at:
                step_progress_evening_map[s.id] = p_evening.created_at.strftime("%I:%M %p")

        step_obj_map = {s.id: s for s in today_steps}

        # Build morning and evening tasks separately with independent completion states
        morning_tasks = []
        evening_tasks = []
        all_evaluated_steps = []

        for s_data in timing_analysis["steps"]:
            s_id = s_data.get("step_id")
            s_obj = step_obj_map.get(s_id)
            time_spec = s_data.get("time_of_day")

            m_is_done = bool(step_progress_morning_map.get(s_id))
            e_is_done = bool(step_progress_evening_map.get(s_id))


            if time_spec in ["morning", "both"]:
                m_task = dict(s_data)
                m_task["session"] = "morning"
                m_task["completed"] = m_is_done
                m_task["completed_at"] = step_progress_morning_map.get(s_id)
                morning_tasks.append(m_task)

            if time_spec in ["evening", "both"]:
                e_task = dict(s_data)
                e_task["session"] = "evening"
                e_task["completed"] = e_is_done
                e_task["completed_at"] = step_progress_evening_map.get(s_id)
                evening_tasks.append(e_task)

            step_eval = dict(s_data)
            step_eval["completed"] = s_obj.completed if s_obj else s_data.get("completed", False)
            step_eval["morning_completed"] = m_is_done
            step_eval["evening_completed"] = e_is_done
            step_eval["completed_at"] = step_progress_morning_map.get(s_id) or step_progress_evening_map.get(s_id)
            all_evaluated_steps.append(step_eval)


        # Calculate time-based wishing/greeting
        client_hour_param = request.query_params.get('client_hour')
        if client_hour_param is not None:
            try:
                current_hour = int(client_hour_param)
            except ValueError:
                current_hour = datetime.now().hour
        else:
            current_hour = datetime.now().hour

        user_name = routine.user.first_name if (routine.user and routine.user.first_name) else None

        if 5 <= current_hour < 12:
            base_greeting = "Good Morning"
        elif 12 <= current_hour < 17:
            base_greeting = "Good Afternoon"
        elif 17 <= current_hour < 22:
            base_greeting = "Good Evening"
        else:
            base_greeting = "Good Night"

        greeting = f"{base_greeting}, {user_name}" if user_name else base_greeting
        today_date_str = eval_date.strftime("%A, %b %d, %Y")


        # Compact Environment Card Info
        uv_val = weather_data.get("uv_index", 6)
        if uv_val >= 8:
            uv_sev = "Very High"
            reminder = "UV is very high today. Don't forget your broad-spectrum sunscreen."
        elif uv_val >= 6:
            uv_sev = "High"
            reminder = "UV is high today. Don't forget your sunscreen."
        elif uv_val >= 3:
            uv_sev = "Moderate"
            reminder = "Moderate daylight UV. Apply standard daytime sun protection."
        else:
            uv_sev = "Low"
            reminder = "UV exposure is low right now. Ideal conditions for barrier recovery."

        humidity_val = weather_data.get("humidity", 55)
        temp_val = weather_data.get("temperature", 28.0)
        environment = {
            "uv_index": uv_val,
            "uv_severity": uv_sev,
            "humidity": humidity_val,
            "temperature": temp_val,
            "condition": weather_data.get("condition", "Clear"),
            "city": weather_data.get("city", city or "Mumbai"),
            "reminder": reminder
        }

        # Check today's skin feedback
        today_feedback = routine.skin_feedbacks.filter(date=eval_date).first()
        today_skin_feel = today_feedback.skin_feel if today_feedback else None

        # Adaptive Routine Guidance from engine
        adaptive_guidance = get_routine_adaptive_guidance(routine)

        # Today's Progress metric (based on today's actionable session tasks)
        today_session_total = len(morning_tasks) + len(evening_tasks)
        today_session_completed = sum(1 for s in morning_tasks if s.get("completed")) + sum(1 for s in evening_tasks if s.get("completed"))
        today_progress_pct = round((today_session_completed / today_session_total * 100), 1) if today_session_total > 0 else 0.0

        return Response({
            "routine_id": routine.id,
            "routine_name": routine.name,
            "greeting": greeting,
            "today_date": today_date_str,
            "eval_date": eval_date.isoformat(),
            "current_week": current_week,
            "current_week_text": f"Week {current_week} of 6",
            "current_stage": active_stage,
            "today_progress": {
                "completed": today_session_completed,
                "total": today_session_total,
                "percentage": today_progress_pct,
                "ratio_text": f"{today_session_completed} / {today_session_total} completed"
            },
            "environment": environment,
            "morning_routine": morning_tasks,
            "evening_routine": evening_tasks,
            "today_skin_feel": today_skin_feel,
            "adaptive_guidance": adaptive_guidance,
            "completed_steps": completed,
            "total_steps": total,
            "progress_percentage": pct,
            "is_completed": routine.status == 'completed' or (total > 0 and completed == total),
            "auto_reorder_enabled": routine.auto_reorder_enabled,
            "auto_reordered": routine.auto_reordered,
            "auto_reorder_date": routine.auto_reorder_date.isoformat() if routine.auto_reorder_date else None,
            "auto_reorder_order_id": routine.auto_reorder_order_id,
            "weather_intelligence": timing_analysis["weather"],
            "useful_count": timing_analysis["useful_count"],
            "not_recommended_count": timing_analysis["not_recommended_count"],
            "caution_count": timing_analysis["caution_count"],
            "steps": all_evaluated_steps
        }, status=status.HTTP_200_OK)



class DailySkinFeedbackView(APIView):
    """
    Records or retrieves daily user-reported skin feedback (comfortable, dry, irritated).
    Powers adaptive tolerance guidance without making medical diagnoses.
    """
    def get(self, request, id):
        routine = get_user_routine(request, id)
        if not routine:
            return Response({"error": "Routine not found."}, status=status.HTTP_404_NOT_FOUND)

        today = date.today()
        today_feedback = routine.skin_feedbacks.filter(date=today).first()
        recent = routine.skin_feedbacks.all()[:10]

        return Response({
            "routine_id": routine.id,
            "today_feedback": DailySkinFeedbackSerializer(today_feedback).data if today_feedback else None,
            "today_skin_feel": today_feedback.skin_feel if today_feedback else None,
            "adaptive_guidance": get_routine_adaptive_guidance(routine),
            "recent_feedbacks": DailySkinFeedbackSerializer(recent, many=True).data
        }, status=status.HTTP_200_OK)

    def post(self, request, id):
        routine = get_user_routine(request, id)
        if not routine:
            return Response({"error": "Routine not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = DailySkinFeedbackInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        skin_feel = serializer.validated_data["skin_feel"]
        notes = serializer.validated_data.get("notes", "")
        entry_date = serializer.validated_data.get("date") or date.today()

        feedback, _ = DailySkinFeedback.objects.update_or_create(
            routine=routine,
            date=entry_date,
            defaults={"skin_feel": skin_feel, "notes": notes}
        )

        guidance = get_routine_adaptive_guidance(routine)

        return Response({
            "message": "Daily skin feedback recorded successfully.",
            "feedback": DailySkinFeedbackSerializer(feedback).data,
            "today_skin_feel": feedback.skin_feel,
            "adaptive_guidance": guidance
        }, status=status.HTTP_200_OK)


class RoutineDeliveryScheduleView(APIView):
    """
    Retrieves the suggested reorder and delivery replenishment schedule.
    """
    def get(self, request, id):
        routine = get_user_routine(request, id, prefetch=['delivery_items__product'])
        if not routine:
            return Response({"error": "Routine not found."}, status=status.HTTP_404_NOT_FOUND)

        items = routine.delivery_items.all()
        serializer = RoutineDeliveryItemSerializer(items, many=True)

        return Response({
            "routine_id": routine.id,
            "routine_name": routine.name,
            "auto_reorder_enabled": routine.auto_reorder_enabled,
            "auto_reordered": routine.auto_reordered,
            "auto_reorder_date": routine.auto_reorder_date.isoformat() if routine.auto_reorder_date else None,
            "auto_reorder_order_id": routine.auto_reorder_order_id,
            "items": serializer.data
        }, status=status.HTTP_200_OK)


class DeleteRoutineStepView(APIView):
    """
    Deletes a specific product step from the user's progressive routine.
    Removes step progress entries and associated delivery items.
    """
    def delete(self, request, id, step_id):
        routine = get_user_routine(request, id)
        if not routine:
            return Response({"error": "Routine not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            step = routine.steps.select_related('product').get(id=step_id)
        except RoutineStep.DoesNotExist:
            return Response({"error": f"Step #{step_id} not found in Routine #{id}."}, status=status.HTTP_404_NOT_FOUND)

        prod_id = step.product_id
        prod_name = step.product.name

        step.delete()

        # Remove replenishment delivery item if no other step in this routine uses this product
        if not routine.steps.filter(product_id=prod_id).exists():
            routine.delivery_items.filter(product_id=prod_id).delete()

        total = routine.steps.count()
        if total == 0:
            routine.status = 'archived'
        routine.save()

        return Response({
            "message": f"'{prod_name}' successfully removed from your routine.",
            "deleted_step_id": step_id,
            "deleted_product_id": prod_id,
            "remaining_steps": total,
            "progress_percentage": routine.progress_percentage
        }, status=status.HTTP_200_OK)


