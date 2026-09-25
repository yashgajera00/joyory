from django.db import models
from django.utils.text import slugify

class Ingredient(models.Model):
    CATEGORY_CHOICES = [
        ('exfoliant', 'Exfoliant'),
        ('retinoid', 'Retinoid'),
        ('antioxidant', 'Antioxidant'),
        ('humectant', 'Humectant'),
        ('lipid', 'Lipid / Barrier Support'),
        ('peptide', 'Peptide'),
        ('sunscreen_filter', 'Sunscreen Filter'),
        ('soothing', 'Soothing / Calming'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    description = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class IngredientInteraction(models.Model):
    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('caution', 'Caution'),
        ('warning', 'Warning'),
    ]

    INTERACTION_TYPE_CHOICES = [
        ('irritation_risk', 'Irritation Risk'),
        ('barrier_stress', 'Barrier Stress'),
        ('ph_dependency', 'pH Sensitivity / Dependency'),
        ('reduced_efficacy', 'Reduced Efficacy'),
        ('compatible_synergy', 'Compatible Synergy'),
        ('sun_sensitivity', 'Sun Sensitivity'),
    ]

    ingredient_a = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, related_name='interactions_as_a'
    )
    ingredient_b = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, related_name='interactions_as_b'
    )
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='caution')
    interaction_type = models.CharField(
        max_length=50, choices=INTERACTION_TYPE_CHOICES, default='irritation_risk'
    )
    message = models.TextField()
    recommendation = models.TextField(help_text="Suggested shopping/usage guidance")

    class Meta:
        unique_together = ('ingredient_a', 'ingredient_b')

    def __str__(self):
        return f"{self.ingredient_a.name} + {self.ingredient_b.name} [{self.severity}]"

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('cleanser', 'Cleanser'),
        ('toner', 'Toner'),
        ('serum', 'Serum'),
        ('moisturizer', 'Moisturizer'),
        ('exfoliant', 'Exfoliant'),
        ('sunscreen', 'Sunscreen'),
        ('treatment', 'Treatment'),
    ]

    TEXTURE_CHOICES = [
        ('gel', 'Gel / Water Gel'),
        ('lightweight_lotion', 'Lightweight Lotion / Fluid'),
        ('rich_cream', 'Rich Cream / Balm'),
        ('oil', 'Oil'),
        ('foam', 'Foam'),
        ('liquid', 'Liquid'),
    ]

    CLIMATE_CHOICES = [
        ('all', 'All Climates'),
        ('hot_humid', 'Hot & Humid'),
        ('hot_dry', 'Hot & Dry'),
        ('cold_dry', 'Cold & Dry'),
    ]

    HYDRATION_CHOICES = [
        ('light', 'Light Hydration'),
        ('moderate', 'Moderate Hydration'),
        ('deep', 'Deep Barrier Repair'),
    ]

    ACTIVE_LEVEL_CHOICES = [
        ('low', 'Low / Gentle'),
        ('medium', 'Medium'),
        ('high', 'High / Concentrated Active'),
    ]

    TIME_OF_DAY_CHOICES = [
        ('morning', 'Morning'),
        ('evening', 'Evening'),
        ('both', 'Both Morning & Evening'),
    ]

    name = models.CharField(max_length=255)
    brand = models.CharField(max_length=150, default='Joyory')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    texture = models.CharField(max_length=50, choices=TEXTURE_CHOICES, default='lightweight_lotion')
    suitable_climate = models.CharField(max_length=50, choices=CLIMATE_CHOICES, default='all')
    hydration_level = models.CharField(max_length=50, choices=HYDRATION_CHOICES, default='moderate')
    active_level = models.CharField(max_length=20, choices=ACTIVE_LEVEL_CHOICES, default='medium')
    usage_frequency = models.CharField(max_length=50, default='daily')
    time_of_day = models.CharField(max_length=20, choices=TIME_OF_DAY_CHOICES, default='both')
    typical_duration_days = models.IntegerField(default=60, help_text="Average lifespan of bottle in days")
    skin_types = models.CharField(max_length=255, default='All Skin Types', help_text="e.g. Sensitive, Oily, Dry, Combination")
    concerns = models.CharField(max_length=255, default='Barrier Support, Daily Health', help_text="e.g. Fine Lines, Dark Spots, Acne, Redness")
    routine_stage = models.IntegerField(default=1, choices=[(1, 'Stage 1: Barrier Foundation'), (2, 'Stage 2: Targeted Prep & Hydration'), (3, 'Stage 3: Concentrated Active Integration')])
    image_url = models.CharField(max_length=500, blank=True, default='', help_text="Product image path or URL")
    ingredients = models.ManyToManyField(Ingredient, related_name='products', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def effective_image_url(self):
        if self.image_url:
            return self.image_url
        if self.id:
            return f'/images/products/product_{self.id}.jpg'
        return f'/images/products/{self.category}.jpg'

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
