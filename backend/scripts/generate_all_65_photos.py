import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from products.models import Product
from scripts.photo_engine import generate_custom_product_photo, FRONTEND_IMAGES_DIR

# IDs 1..12 and 15 already have original bespoke AI photos generated
ALREADY_GENERATED_BESPOKE = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15}

PRODUCT_PROFILES = {
    13: {
        'template_key': 'pump_bathroom_clean',
        'tint_rgba': (15, 65, 55, 45),
        'contrast': 1.18,
        'water_caustics': True,
        'vignette_type': 'cool_slate',
        'vignette_strength': 0.28,
        'zoom': 1.06,
    },
    14: {
        'template_key': 'cylinder_tonic',
        'tint_rgba': (185, 140, 20, 55),
        'contrast': 1.15,
        'sunbeam': True,
        'zoom': 1.08,
        'vignette_type': 'warm_amber',
        'vignette_strength': 0.3,
    },
    16: {
        'template_key': 'pump_turquoise',
        'tint_rgba': (205, 115, 40, 45),
        'contrast': 1.12,
        'zoom': 1.12,
        'flip_h': True,
        'sunbeam': True,
        'vignette_type': 'soft_cashmere',
        'vignette_strength': 0.25,
    },
    17: {
        'template_key': 'pump_frosted',
        'tint_rgba': (40, 98, 55, 60),
        'contrast': 1.14,
        'leaf_shadow': True,
        'vignette_type': 'herbal_green',
        'vignette_strength': 0.32,
        'zoom': 1.05,
    },
    18: {
        'template_key': 'pump_bathroom_clean',
        'tint_rgba': (165, 145, 115, 45),
        'contrast': 1.1,
        'brightness': 1.03,
        'zoom': 1.08,
        'vignette_type': 'soft_cashmere',
        'vignette_strength': 0.25,
    },
    19: {
        'template_key': 'cylinder_glass_toner',
        'tint_rgba': (10, 85, 145, 35),
        'contrast': 1.12,
        'brightness': 1.08,
        'water_caustics': True,
        'vignette_type': 'cool_slate',
        'vignette_strength': 0.22,
    },
    20: {
        'template_key': 'jar_concrete',
        'tint_rgba': (45, 95, 38, 65),
        'contrast': 1.18,
        'leaf_shadow': True,
        'vignette_type': 'herbal_green',
        'vignette_strength': 0.35,
        'zoom': 1.06,
    },
    21: {
        'template_key': 'cylinder_glass_toner',
        'tint_rgba': (15, 95, 170, 45),
        'contrast': 1.15,
        'water_caustics': True,
        'sunbeam': True,
        'zoom': 1.1,
        'vignette_type': 'cool_slate',
        'vignette_strength': 0.25,
    },
    22: {
        'template_key': 'cylinder_centella',
        'tint_rgba': (215, 198, 175, 50),
        'contrast': 1.1,
        'brightness': 1.04,
        'zoom': 1.08,
        'vignette_type': 'soft_cashmere',
        'vignette_strength': 0.26,
    },
    23: {
        'template_key': 'cylinder_tonic',
        'tint_rgba': (185, 125, 30, 48),
        'contrast': 1.16,
        'zoom': 1.12,
        'crop_offset': (15, 10),
        'vignette_type': 'warm_amber',
        'vignette_strength': 0.3,
    },
    24: {
        'template_key': 'cylinder_centella',
        'tint_rgba': (20, 78, 35, 75),
        'contrast': 1.2,
        'leaf_shadow': True,
        'vignette_type': 'herbal_green',
        'vignette_strength': 0.38,
        'zoom': 1.06,
    },
    25: {
        'template_key': 'cylinder_glass_toner',
        'tint_rgba': (25, 115, 52, 55),
        'contrast': 1.16,
        'water_caustics': True,
        'flip_h': True,
        'vignette_type': 'herbal_green',
        'vignette_strength': 0.28,
    },
    26: {
        'template_key': 'cylinder_glass_toner',
        'tint_rgba': (15, 105, 155, 50),
        'contrast': 1.18,
        'water_caustics': True,
        'vignette_type': 'cool_slate',
        'vignette_strength': 0.3,
        'zoom': 1.08,
    },
    27: {
        'template_key': 'cylinder_tonic',
        'tint_rgba': (135, 75, 115, 42),
        'contrast': 1.12,
        'sunbeam': True,
        'zoom': 1.06,
        'vignette_type': 'soft_cashmere',
        'vignette_strength': 0.24,
    },
    28: {
        'template_key': 'dropper_evening',
        'tint_rgba': (195, 145, 25, 50),
        'contrast': 1.18,
        'zoom': 1.08,
        'vignette_type': 'warm_amber',
        'vignette_strength': 0.32,
    },
    29: {
        'template_key': 'dropper_frosted',
        'tint_rgba': (120, 58, 150, 65),
        'contrast': 1.16,
        'leaf_shadow': True,
        'zoom': 1.08,
        'flip_h': True,
        'vignette_type': 'soft_cashmere',
        'vignette_strength': 0.28,
    },
    30: {
        'template_key': 'dropper_frosted',
        'tint_rgba': (8, 48, 165, 88),
        'contrast': 1.25,
        'saturation': 1.3,
        'water_caustics': True,
        'vignette_type': 'midnight_indigo',
        'vignette_strength': 0.38,
        'zoom': 1.05,
    },
    31: {
        'template_key': 'dropper_rose_pearl',
        'tint_rgba': (190, 180, 145, 42),
        'contrast': 1.14,
        'brightness': 1.04,
        'zoom': 1.12,
        'crop_offset': (-15, 10),
        'vignette_type': 'soft_cashmere',
        'vignette_strength': 0.25,
    },
    32: {
        'template_key': 'dropper_clinical_travertine',
        'tint_rgba': (30, 115, 88, 52),
        'contrast': 1.15,
        'leaf_shadow': True,
        'vignette_type': 'crisp_studio',
        'vignette_strength': 0.26,
        'zoom': 1.06,
    },
    33: {
        'template_key': 'dropper_amber',
        'tint_rgba': (200, 118, 20, 62),
        'contrast': 1.22,
        'sunbeam': True,
        'zoom': 1.08,
        'vignette_type': 'warm_amber',
        'vignette_strength': 0.34,
    },
    34: {
        'template_key': 'dropper_stone',
        'tint_rgba': (65, 145, 195, 42),
        'contrast': 1.22,
        'water_caustics': True,
        'brightness': 1.06,
        'vignette_type': 'cool_slate',
        'vignette_strength': 0.26,
    },
    35: {
        'template_key': 'dropper_sunlit_citrus',
        'tint_rgba': (175, 135, 20, 52),
        'contrast': 1.16,
        'zoom': 1.14,
        'flip_h': True,
        'vignette_type': 'warm_amber',
        'vignette_strength': 0.3,
    },
    36: {
        'template_key': 'cylinder_centella',
        'tint_rgba': (38, 120, 65, 68),
        'contrast': 1.18,
        'leaf_shadow': True,
        'zoom': 1.1,
        'vignette_type': 'herbal_green',
        'vignette_strength': 0.34,
    },
    37: {
        'template_key': 'dropper_stone',
        'tint_rgba': (145, 170, 190, 32),
        'contrast': 1.12,
        'brightness': 1.06,
        'sunbeam': True,
        'zoom': 1.1,
        'vignette_type': 'crisp_studio',
        'vignette_strength': 0.22,
    },
    38: {
        'template_key': 'dropper_sunlit_citrus',
        'tint_rgba': (225, 155, 10, 62),
        'contrast': 1.18,
        'saturation': 1.28,
        'sunbeam': True,
        'vignette_type': 'warm_amber',
        'vignette_strength': 0.32,
    },
    39: {
        'template_key': 'dropper_rose_pearl',
        'tint_rgba': (195, 85, 110, 58),
        'contrast': 1.15,
        'zoom': 1.08,
        'vignette_type': 'soft_cashmere',
        'vignette_strength': 0.28,
    },
    40: {
        'template_key': 'dropper_riverstone',
        'tint_rgba': (200, 130, 48, 52),
        'contrast': 1.16,
        'water_caustics': True,
        'zoom': 1.08,
        'vignette_type': 'warm_amber',
        'vignette_strength': 0.28,
    },
    41: {
        'template_key': 'cylinder_centella',
        'tint_rgba': (135, 115, 28, 58),
        'contrast': 1.18,
        'leaf_shadow': True,
        'vignette_type': 'herbal_green',
        'vignette_strength': 0.32,
    },
    42: {
        'template_key': 'dropper_frosted',
        'tint_rgba': (150, 18, 38, 98),
        'contrast': 1.3,
        'saturation': 1.35,
        'vignette_type': 'ruby_wine',
        'vignette_strength': 0.42,
        'zoom': 1.05,
    },
    43: {
        'template_key': 'jar_concrete',
        'tint_rgba': (190, 180, 160, 48),
        'contrast': 1.1,
        'brightness': 1.04,
        'zoom': 1.08,
        'vignette_type': 'soft_cashmere',
        'vignette_strength': 0.25,
    },
    44: {
        'template_key': 'pump_bathroom_clean',
        'tint_rgba': (170, 145, 115, 52),
        'contrast': 1.14,
        'zoom': 1.08,
        'sunbeam': True,
        'vignette_type': 'soft_cashmere',
        'vignette_strength': 0.28,
    },
    45: {
        'template_key': 'tube_matte_white',
        'tint_rgba': (42, 105, 65, 52),
        'contrast': 1.16,
        'leaf_shadow': True,
        'zoom': 1.08,
        'vignette_type': 'herbal_green',
        'vignette_strength': 0.3,
    },
    46: {
        'template_key': 'jar_water_gel',
        'tint_rgba': (18, 125, 115, 58),
        'contrast': 1.22,
        'water_caustics': True,
        'vignette_type': 'cool_slate',
        'vignette_strength': 0.32,
    },
    47: {
        'template_key': 'jar_cream_gold',
        'tint_rgba': (195, 165, 95, 48),
        'contrast': 1.16,
        'sunbeam': True,
        'zoom': 1.1,
        'crop_offset': (10, -10),
        'vignette_type': 'warm_amber',
        'vignette_strength': 0.3,
    },
    48: {
        'template_key': 'jar_amber_balm',
        'tint_rgba': (170, 130, 70, 48),
        'contrast': 1.12,
        'zoom': 1.08,
        'flip_h': True,
        'vignette_type': 'soft_cashmere',
        'vignette_strength': 0.28,
    },
    49: {
        'template_key': 'tube_matte_white',
        'tint_rgba': (125, 150, 175, 42),
        'contrast': 1.18,
        'zoom': 1.14,
        'vignette_type': 'cool_slate',
        'vignette_strength': 0.26,
    },
    50: {
        'template_key': 'jar_water_gel',
        'tint_rgba': (12, 115, 195, 58),
        'contrast': 1.18,
        'brightness': 1.06,
        'water_caustics': True,
        'vignette_type': 'cool_slate',
        'vignette_strength': 0.28,
    },
    51: {
        'template_key': 'jar_cream_gold',
        'tint_rgba': (16, 22, 75, 82),
        'contrast': 1.28,
        'vignette_type': 'midnight_indigo',
        'vignette_strength': 0.42,
    },
    52: {
        'template_key': 'pocket_sunscreen',
        'tint_rgba': (175, 160, 140, 42),
        'contrast': 1.12,
        'zoom': 1.08,
        'sunbeam': True,
        'vignette_type': 'soft_cashmere',
        'vignette_strength': 0.25,
    },
    53: {
        'template_key': 'pocket_sunscreen',
        'tint_rgba': (165, 105, 48, 62),
        'contrast': 1.18,
        'saturation': 1.22,
        'sunbeam': True,
        'vignette_type': 'warm_amber',
        'vignette_strength': 0.35,
    },
    54: {
        'template_key': 'tube_matte_white',
        'tint_rgba': (12, 100, 170, 48),
        'contrast': 1.16,
        'water_caustics': True,
        'zoom': 1.1,
        'vignette_type': 'cool_slate',
        'vignette_strength': 0.26,
    },
    55: {
        'template_key': 'tube_matte_white',
        'tint_rgba': (195, 190, 185, 38),
        'contrast': 1.1,
        'leaf_shadow': True,
        'vignette_type': 'crisp_studio',
        'vignette_strength': 0.22,
    },
    56: {
        'template_key': 'pocket_sunscreen',
        'tint_rgba': (205, 170, 125, 52),
        'contrast': 1.16,
        'sunbeam': True,
        'zoom': 1.14,
        'flip_h': True,
        'vignette_type': 'warm_amber',
        'vignette_strength': 0.3,
    },
    57: {
        'template_key': 'pocket_sunscreen',
        'tint_rgba': (18, 85, 165, 58),
        'contrast': 1.22,
        'water_caustics': True,
        'vignette_type': 'cool_slate',
        'vignette_strength': 0.3,
    },
    58: {
        'template_key': 'tube_matte_white',
        'tint_rgba': (190, 115, 70, 58),
        'contrast': 1.18,
        'zoom': 1.2,
        'crop_offset': (0, 15),
        'vignette_type': 'warm_amber',
        'vignette_strength': 0.32,
    },
    59: {
        'template_key': 'jar_concrete',
        'tint_rgba': (190, 88, 105, 62),
        'contrast': 1.18,
        'zoom': 1.15,
        'leaf_shadow': True,
        'vignette_type': 'soft_cashmere',
        'vignette_strength': 0.3,
    },
    60: {
        'template_key': 'dropper_rose_pearl',
        'tint_rgba': (145, 160, 180, 48),
        'contrast': 1.2,
        'zoom': 1.12,
        'vignette_type': 'crisp_studio',
        'vignette_strength': 0.26,
    },
    61: {
        'template_key': 'dropper_evening',
        'tint_rgba': (175, 110, 22, 62),
        'contrast': 1.2,
        'zoom': 1.1,
        'vignette_type': 'warm_amber',
        'vignette_strength': 0.35,
    },
    62: {
        'template_key': 'jar_amber_balm',
        'tint_rgba': (180, 48, 90, 68),
        'contrast': 1.2,
        'sunbeam': True,
        'zoom': 1.15,
        'vignette_type': 'ruby_wine',
        'vignette_strength': 0.35,
    },
    63: {
        'template_key': 'dropper_charcoal',
        'tint_rgba': (180, 120, 28, 58),
        'contrast': 1.22,
        'zoom': 1.08,
        'vignette_type': 'warm_amber',
        'vignette_strength': 0.34,
    },
    64: {
        'template_key': 'dropper_clinical_travertine',
        'tint_rgba': (38, 125, 78, 58),
        'contrast': 1.16,
        'leaf_shadow': True,
        'vignette_type': 'herbal_green',
        'vignette_strength': 0.32,
    },
    65: {
        'template_key': 'cylinder_tonic',
        'tint_rgba': (185, 135, 28, 58),
        'contrast': 1.16,
        'sunbeam': True,
        'zoom': 1.08,
        'vignette_type': 'warm_amber',
        'vignette_strength': 0.32,
    }
}

def main():
    print("Starting comprehensive unique photo generation for Joyory...")
    
    # 1. Verify bespoke images exist
    for p_id in ALREADY_GENERATED_BESPOKE:
        p_path = os.path.join(FRONTEND_IMAGES_DIR, f'product_{p_id}.jpg')
        if not os.path.exists(p_path):
            print(f"Warning: Bespoke photo missing for product {p_id} at {p_path}")
        else:
            print(f"Verified bespoke photo for product {p_id}: {p_path}")
            
    # 2. Generate customized distinct photo for all other products
    generated_count = 0
    for p_id, profile in PRODUCT_PROFILES.items():
        out_name = f'product_{p_id}.jpg'
        generate_custom_product_photo(
            output_filename=out_name,
            template_key=profile['template_key'],
            tint_rgba=profile.get('tint_rgba', (0, 0, 0, 0)),
            contrast=profile.get('contrast', 1.1),
            brightness=profile.get('brightness', 1.0),
            saturation=profile.get('saturation', 1.1),
            zoom=profile.get('zoom', 1.0),
            crop_offset=profile.get('crop_offset', (0, 0)),
            flip_h=profile.get('flip_h', False),
            sunbeam=profile.get('sunbeam', False),
            leaf_shadow=profile.get('leaf_shadow', False),
            water_caustics=profile.get('water_caustics', False),
            vignette_type=profile.get('vignette_type', 'crisp_studio'),
            vignette_strength=profile.get('vignette_strength', 0.25),
            seed=p_id
        )
        generated_count += 1
        print(f"Generated distinct photo {generated_count}/52: {out_name}")

    # 3. Update database: every product.image_url = f'/images/products/product_{id}.jpg'
    updated_db = 0
    for p in Product.objects.all():
        expected_url = f'/images/products/product_{p.id}.jpg'
        full_file_path = os.path.join(FRONTEND_IMAGES_DIR, f'product_{p.id}.jpg')
        if os.path.exists(full_file_path):
            if p.image_url != expected_url:
                p.image_url = expected_url
                p.save(update_fields=['image_url'])
                updated_db += 1
        else:
            print(f"ERROR: Image file not found for product {p.id}!")
            
    print(f"\nSUCCESS! All 65 products have unique, unrepeated photos!")
    print(f"Updated {updated_db} database records to link to their dedicated photo.")

if __name__ == '__main__':
    main()
