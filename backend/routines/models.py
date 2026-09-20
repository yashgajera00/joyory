from django.db import models
from django.contrib.auth.models import User
from datetime import date
from products.models import Product

class Routine(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='routines')
    session_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    name = models.CharField(max_length=200, default='My Joyory Routine')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    auto_reorder_enabled = models.BooleanField(default=True, help_text="Automatically schedule replenishment reorder upon routine completion")
    auto_reordered = models.BooleanField(default=False, help_text="True if automated reorder was dispatched")
    auto_reorder_date = models.DateTimeField(null=True, blank=True)
    auto_reorder_order_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (#{self.id})"

    @property
    def total_steps_count(self):
        return self.steps.count()

    @property
    def completed_steps_count(self):
        return self.steps.filter(completed=True).count()

    @property
    def progress_percentage(self):
        total = self.total_steps_count
        if total == 0:
            return 0.0
        return round((self.completed_steps_count / total) * 100, 1)

    @property
    def current_stage(self):
        # find the lowest stage number where steps are not all completed
        for stage_num in range(1, 10):
            stage_steps = self.steps.filter(stage_number=stage_num)
            if not stage_steps.exists():
                continue
            if stage_steps.filter(completed=False).exists():
                return stage_num
        # if all completed, return max stage or 1
        last = self.steps.order_by('-stage_number').first()
        return last.stage_number if last else 1

class RoutineStep(models.Model):
    routine = models.ForeignKey(Routine, on_delete=models.CASCADE, related_name='steps')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='routine_steps')
    stage_number = models.IntegerField(default=1)
    stage_name = models.CharField(max_length=100, default='Foundation Stage')
    week_start = models.IntegerField(default=1)
    week_end = models.IntegerField(default=2)
    frequency = models.CharField(max_length=50, default='daily')
    time_of_day = models.CharField(max_length=20, default='both')
    order = models.IntegerField(default=1)
    completed = models.BooleanField(default=False)
    morning_completed = models.BooleanField(default=False)
    evening_completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['stage_number', 'order']

    def __str__(self):
        return f"Stage {self.stage_number}: {self.product.name} ({self.frequency})"

class RoutineProgress(models.Model):
    routine_step = models.ForeignKey(RoutineStep, on_delete=models.CASCADE, related_name='progress_entries')
    date = models.DateField()
    session = models.CharField(max_length=20, default='all') # 'morning', 'evening', 'all'
    completed = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"Progress for Step #{self.routine_step_id} ({self.session}) on {self.date}"


class RoutineDeliveryItem(models.Model):
    routine = models.ForeignKey(Routine, on_delete=models.CASCADE, related_name='delivery_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='delivery_items')
    quantity = models.IntegerField(default=1)
    suggested_reorder_date = models.DateField()
    frequency_weeks = models.IntegerField(default=8)
    active = models.BooleanField(default=True)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=50, default='scheduled') # 'scheduled', 'auto_reordered', 'delivered'
    tracking_number = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Reorder {self.product.name} on {self.suggested_reorder_date} ({self.status})"

class DailySkinFeedback(models.Model):
    SKIN_FEEL_CHOICES = [
        ('comfortable', 'Comfortable'),
        ('dry', 'A little dry'),
        ('irritated', 'Irritated'),
    ]

    routine = models.ForeignKey(Routine, on_delete=models.CASCADE, related_name='skin_feedbacks')
    date = models.DateField(default=date.today)
    skin_feel = models.CharField(max_length=30, choices=SKIN_FEEL_CHOICES)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('routine', 'date')
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"Feedback for Routine #{self.routine_id} on {self.date}: {self.skin_feel}"

