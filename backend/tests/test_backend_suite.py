from django.test import TestCase
from django.core.management import call_command
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from io import BytesIO
import json
from datetime import date, timedelta

from products.models import Product, Ingredient, IngredientInteraction
from cart.models import Cart, CartItem
from routines.models import Routine, RoutineStep, RoutineProgress, RoutineDeliveryItem
from services.climate_service import ClimateService
from services.climate_engine import evaluate_climate_adaptation
from services.routine_engine import generate_progressive_routine, generate_delivery_schedule

class JoyoryBackendTestSuite(TestCase):
    """
    Comprehensive test suite validating all 15 required backend test scenarios.
    """

    def setUp(self):
        self.client = APIClient()
        # Seed standard demo data
        call_command('seed_demo_data')

        self.cleanser = Product.objects.get(name="Joyory Barrier Calm Gentle Cleanser")
        self.retinol_serum = Product.objects.get(name="Joyory Midnight Renewal 0.5% Retinol Treatment")
        self.aha_exfoliant = Product.objects.get(name="Joyory Resurfacing 7% Glycolic AHA Exfoliator")
        self.moisturizer = Product.objects.get(name="Joyory Deep Barrier Restoring Cream")
        self.sunscreen = Product.objects.get(name="Joyory Invisible Shield Mineral SPF 50+")
        self.gentle_serum = Product.objects.get(name="Joyory Gentle Hydrating Recovery Serum")

    # 1. Product Listing
    def test_01_product_listing(self):
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 10)
        # Test category filter
        resp_cleanser = self.client.get('/api/products/?category=cleanser')
        self.assertEqual(resp_cleanser.status_code, status.HTTP_200_OK)
        for item in resp_cleanser.data:
            self.assertEqual(item['category'], 'cleanser')

    # 2. Product Detail
    def test_02_product_detail(self):
        response = self.client.get(f'/api/products/{self.retinol_serum.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.retinol_serum.id)
        self.assertEqual(response.data['name'], self.retinol_serum.name)
        self.assertIn('ingredients', response.data)
        ing_names = [i['name'] for i in response.data['ingredients']]
        self.assertIn('Retinol', ing_names)

    # 3. Add to Cart
    def test_03_add_to_cart(self):
        payload = {
            "product_id": self.cleanser.id,
            "quantity": 2,
            "session_key": "test-session-123"
        }
        response = self.client.post('/api/cart/add/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('cart', response.data)
        self.assertEqual(response.data['cart']['total_items'], 2)
        expected_total = float(self.cleanser.price * 2)
        self.assertEqual(float(response.data['cart']['total_price']), expected_total)
        # Verify cart view
        get_cart = self.client.get('/api/cart/?session_key=test-session-123')
        self.assertEqual(get_cart.status_code, status.HTTP_200_OK)
        self.assertEqual(len(get_cart.data['items']), 1)

    # 4. Conflict Detection
    def test_04_conflict_detection(self):
        payload = {
            "product_id": self.retinol_serum.id,
            "cart_product_ids": [self.aha_exfoliant.id]
        }
        response = self.client.post('/api/cart/check-conflicts/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['has_conflicts'])
        self.assertTrue(response.data['has_warnings'])
        self.assertGreaterEqual(len(response.data['warnings']), 1)
        warning = response.data['warnings'][0]
        self.assertEqual(warning['severity'], 'warning')
        self.assertEqual(warning['interaction_type'], 'irritation_risk')

    # 5. Compatible Ingredient Combination
    def test_05_compatible_ingredient_combination(self):
        # Cleanser + Gentle Hydrating Serum (Hyaluronic Acid & Ceramides)
        payload = {
            "product_id": self.cleanser.id,
            "cart_product_ids": [self.gentle_serum.id]
        }
        response = self.client.post('/api/cart/check-conflicts/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['has_warnings'])

    # 6. Warning Interaction Formatting
    def test_06_warning_interaction(self):
        payload = {
            "product_id": self.aha_exfoliant.id,
            "cart_product_ids": [self.retinol_serum.id]
        }
        response = self.client.post('/api/cart/check-conflicts/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        warning = response.data['warnings'][0]
        self.assertIn("message", warning)
        self.assertIn("suggestion", warning)
        self.assertIn("ingredient_a", warning)
        self.assertIn("ingredient_b", warning)
        self.assertEqual(warning['severity'], 'warning')

    # 7. Alternative Product Suggestion
    def test_07_alternative_product_suggestion(self):
        # Adding Retinol to cart that already has AHA suggests gentle alternative serums
        payload = {
            "product_id": self.retinol_serum.id,
            "cart_product_ids": [self.aha_exfoliant.id]
        }
        response = self.client.post('/api/cart/check-conflicts/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        alternatives = response.data['alternatives']
        self.assertIsInstance(alternatives, list)
        self.assertGreater(len(alternatives), 0)
        # Alternative should be in the same category (serum)
        for alt in alternatives:
            self.assertEqual(alt['category'], 'Serum')
            self.assertIn('reason', alt)

    # 8. Climate API Success
    @patch('urllib.request.urlopen')
    def test_08_climate_api_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_payload = {
            "name": "Ahmedabad",
            "main": {"temp": 34.5, "humidity": 45},
            "weather": [{"main": "Clear"}]
        }
        mock_response.read.return_value = json.dumps(mock_payload).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        service = ClimateService(api_key="mock_test_key")
        result = service.get_climate_data(latitude=23.0225, longitude=72.5714)

        self.assertEqual(result['temperature'], 34.5)
        self.assertEqual(result['humidity'], 45)
        self.assertEqual(result['source'], 'live')
        self.assertFalse(result['is_fallback'])

    # 9. Climate API Failure & Fallback
    @patch('urllib.request.urlopen')
    def test_09_climate_api_failure_fallback(self, mock_urlopen):
        # Force network failure
        mock_urlopen.side_effect = Exception("Connection timeout")

        service = ClimateService(api_key="mock_test_key")
        result = service.get_climate_data(latitude=23.0225, longitude=72.5714)

        self.assertIsNotNone(result)
        self.assertEqual(result['source'], 'fallback')
        self.assertTrue(result['is_fallback'])
        self.assertIn('temperature', result)
        self.assertIn('humidity', result)
        self.assertIn('uv_index', result)

    # 10. Climate-based Suggestion
    def test_10_climate_based_suggestion(self):
        # High UV scenario without sunscreen in product list
        high_uv_climate = {
            "temperature": 35.0,
            "humidity": 30, # dry
            "uv_index": 9,  # high UV
            "aqi": 140,
            "condition": "Sunny"
        }
        # Products without sunscreen
        product_ids = [self.cleanser.id, self.gentle_serum.id]
        analysis = evaluate_climate_adaptation(high_uv_climate, product_ids)

        self.assertTrue(analysis['location_available'])
        suggestion_types = [s['type'] for s in analysis['suggestions']]
        self.assertIn('uv_protection', suggestion_types)
        self.assertIn('barrier_hydration', suggestion_types)
        # Should recommend sunscreen in alternatives
        rec_categories = [p['category'] for p in analysis['alternative_products']]
        self.assertIn('Sunscreen', rec_categories)

    # 11. Routine Generation
    def test_11_routine_generation(self):
        payload = {
            "product_ids": [
                self.cleanser.id,
                self.gentle_serum.id,
                self.retinol_serum.id,
                self.sunscreen.id
            ],
            "name": "My Custom Test Routine"
        }
        response = self.client.post('/api/routines/generate/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('routine_id', response.data)
        self.assertIn('stages', response.data)
        self.assertGreaterEqual(len(response.data['stages']), 2)

    # 12. Progressive Routine Stages (Staged active introduction)
    def test_12_progressive_routine_stages(self):
        routine_data = generate_progressive_routine(
            product_ids=[
                self.cleanser.id,
                self.gentle_serum.id,
                self.retinol_serum.id,
                self.aha_exfoliant.id,
                self.sunscreen.id
            ]
        )
        stages = {s['stage']: s for s in routine_data['stages']}
        # Stage 1 must contain barrier foundation (cleanser and/or sunscreen)
        stage1_prod_names = [p['product_name'] for p in stages[1]['products']]
        self.assertIn(self.cleanser.name, stage1_prod_names)
        self.assertIn(self.sunscreen.name, stage1_prod_names)

        # Stage 3 must contain high intensity actives (Retinol, AHA)
        self.assertIn(3, stages)
        stage3_prod_names = [p['product_name'] for p in stages[3]['products']]
        self.assertIn(self.retinol_serum.name, stage3_prod_names)
        self.assertIn(self.aha_exfoliant.name, stage3_prod_names)
        # Verify frequency in stage 3 is non-daily / spaced (e.g. 2_3_times_per_week)
        for p in stages[3]['products']:
            self.assertEqual(p['frequency'], '2_3_times_per_week')

    # 13. Routine Completion Tracking
    def test_13_routine_completion_tracking(self):
        routine_data = generate_progressive_routine(
            product_ids=[self.cleanser.id, self.sunscreen.id]
        )
        routine_id = routine_data['routine_id']
        routine = Routine.objects.get(id=routine_id)
        first_step = routine.steps.first()

        payload = {
            "step_id": first_step.id,
            "completed": True,
            "notes": "Skin feels clean and calm."
        }
        response = self.client.post(f'/api/routines/{routine_id}/complete-step/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['completed'])

        # Verify in database
        first_step.refresh_from_db()
        self.assertTrue(first_step.completed)
        self.assertEqual(first_step.progress_entries.count(), 1)
        self.assertEqual(first_step.progress_entries.first().notes, "Skin feels clean and calm.")

    # 14. Progress Calculation
    def test_14_progress_calculation(self):
        routine_data = generate_progressive_routine(
            product_ids=[self.cleanser.id, self.sunscreen.id]
        )
        routine_id = routine_data['routine_id']
        routine = Routine.objects.get(id=routine_id)

        # Initially 0% completed
        resp_initial = self.client.get(f'/api/routines/{routine_id}/progress/')
        self.assertEqual(resp_initial.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_initial.data['completed_steps'], 0)
        self.assertEqual(resp_initial.data['progress_percentage'], 0.0)

        # Complete 1 out of 2 steps -> 50%
        step1 = routine.steps.first()
        step1.completed = True
        step1.save()

        resp_after = self.client.get(f'/api/routines/{routine_id}/progress/')
        self.assertEqual(resp_after.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_after.data['completed_steps'], 1)
        self.assertEqual(resp_after.data['total_steps'], 2)
        self.assertEqual(resp_after.data['progress_percentage'], 50.0)

    # 15. Delivery / Reorder Date Calculation
    def test_15_delivery_reorder_date_calculation(self):
        routine_data = generate_progressive_routine(
            product_ids=[self.cleanser.id, self.sunscreen.id]
        )
        routine_id = routine_data['routine_id']

        response = self.client.get(f'/api/routines/{routine_id}/delivery-schedule/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('items', response.data)
        self.assertEqual(len(response.data['items']), 2)

        for item in response.data['items']:
            self.assertIn('suggested_reorder_date', item)
            self.assertIn('frequency_weeks', item)
            self.assertIn('reason', item)
            # Reorder date must be strictly in the future
            reorder_dt = date.fromisoformat(item['suggested_reorder_date'])
            self.assertGreater(reorder_dt, date.today())
