import os
import math
from PIL import Image, ImageEnhance, ImageChops, ImageDraw, ImageFilter, ImageOps

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_IMAGES_DIR = os.path.join(BASE_DIR, '..', 'frontend', 'public', 'images', 'products')

# High quality studio base templates available in products dir
TEMPLATE_MAP = {
    'pump_frosted': os.path.join(FRONTEND_IMAGES_DIR, 'product_1.jpg'),
    'pump_turquoise': os.path.join(FRONTEND_IMAGES_DIR, 'product_2.jpg'),
    'dropper_amber': os.path.join(FRONTEND_IMAGES_DIR, 'product_3.jpg'),
    'dropper_frosted': os.path.join(FRONTEND_IMAGES_DIR, 'product_4.jpg'),
    'dropper_cobalt': os.path.join(FRONTEND_IMAGES_DIR, 'product_5.jpg'),
    'cylinder_tonic': os.path.join(FRONTEND_IMAGES_DIR, 'product_6.jpg'),
    'dropper_charcoal': os.path.join(FRONTEND_IMAGES_DIR, 'product_7.jpg'),
    'jar_cream_gold': os.path.join(FRONTEND_IMAGES_DIR, 'product_8.jpg'),
    'jar_water_gel': os.path.join(FRONTEND_IMAGES_DIR, 'product_9.jpg'),
    'tube_matte_white': os.path.join(FRONTEND_IMAGES_DIR, 'product_10.jpg'),
    'cylinder_centella': os.path.join(FRONTEND_IMAGES_DIR, 'product_11.jpg'),
    'dropper_rose_pearl': os.path.join(FRONTEND_IMAGES_DIR, 'product_12.jpg'),
    'jar_amber_balm': os.path.join(FRONTEND_IMAGES_DIR, 'product_15.jpg'),
    'pump_bathroom_clean': os.path.join(FRONTEND_IMAGES_DIR, 'cleanser.jpg'),
    'dropper_stone': os.path.join(FRONTEND_IMAGES_DIR, 'serum.jpg'),
    'jar_concrete': os.path.join(FRONTEND_IMAGES_DIR, 'moisturizer.jpg'),
    'cylinder_glass_toner': os.path.join(FRONTEND_IMAGES_DIR, 'toner.jpg'),
    'dropper_riverstone': os.path.join(FRONTEND_IMAGES_DIR, 'exfoliant.jpg'),
    'pocket_sunscreen': os.path.join(FRONTEND_IMAGES_DIR, 'sunscreen.jpg'),
    'dropper_evening': os.path.join(FRONTEND_IMAGES_DIR, 'retinol.jpg'),
    'dropper_sunlit_citrus': os.path.join(FRONTEND_IMAGES_DIR, 'vitamin_c.jpg'),
    'dropper_clinical_travertine': os.path.join(FRONTEND_IMAGES_DIR, 'treatment.jpg'),
}

def apply_sunbeam(img, angle=45, intensity=50, warm_color=(255, 235, 190)):
    w, h = img.size
    beam = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(beam)
    # Draw soft angled rays
    for offset in range(-w, w * 2, 90):
        alpha = int(intensity * (0.6 + 0.4 * math.sin(offset)))
        poly = [
            (offset, 0),
            (offset + 70, 0),
            (offset - int(h * 0.5) + 70, h),
            (offset - int(h * 0.5), h)
        ]
        draw.polygon(poly, fill=(warm_color[0], warm_color[1], warm_color[2], max(10, alpha)))
    beam = beam.filter(ImageFilter.GaussianBlur(55))
    return Image.alpha_composite(img.convert('RGBA'), beam).convert('RGB')

def apply_leaf_shadow(img, seed=1):
    w, h = img.size
    shadow = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    # Organic branch curves & leaves
    leaf_color = (20, 25, 20, 48)
    for i in range(5):
        cx = int(w * (0.15 + 0.15 * i * ((seed % 3) + 1)))
        cy = int(h * (0.1 + 0.12 * i))
        draw.ellipse([cx - 50, cy - 25, cx + 50, cy + 25], fill=leaf_color)
        draw.ellipse([cx - 20, cy - 40, cx + 20, cy + 40], fill=leaf_color)
    shadow = shadow.filter(ImageFilter.GaussianBlur(35))
    return Image.alpha_composite(img.convert('RGBA'), shadow).convert('RGB')

def apply_water_caustics(img, intensity=35):
    w, h = img.size
    caustic = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(caustic)
    # Water ripple concentric arcs
    center = (int(w * 0.5), int(h * 0.75))
    for r in range(40, 480, 45):
        alpha = max(10, int(intensity * (1.0 - r / 500.0)))
        draw.ellipse(
            [center[0] - r*1.3, center[1] - r*0.5, center[0] + r*1.3, center[1] + r*0.5],
            outline=(200, 240, 255, alpha),
            width=6
        )
    caustic = caustic.filter(ImageFilter.GaussianBlur(22))
    return Image.alpha_composite(img.convert('RGBA'), caustic).convert('RGB')

def apply_vignette(img, vignette_type='warm_amber', strength=0.3):
    w, h = img.size
    vig = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(vig)
    color_dict = {
        'warm_amber': (70, 40, 15),
        'cool_slate': (20, 30, 45),
        'midnight_indigo': (10, 12, 35),
        'crisp_studio': (30, 30, 30),
        'soft_cashmere': (60, 50, 45),
        'herbal_green': (25, 45, 30),
        'ruby_wine': (55, 15, 25),
    }
    base_col = color_dict.get(vignette_type, (30, 30, 30))
    max_r = int(math.hypot(w, h) / 2)
    center_x, center_y = w // 2, h // 2
    
    # Outer dark border with smooth falloff
    for step in range(12):
        frac = step / 12.0
        alpha = int(255 * strength * (frac ** 2.2))
        pad = int(min(w, h) * (1.0 - frac) * 0.48)
        draw.rectangle(
            [pad, pad, w - pad, h - pad],
            outline=(base_col[0], base_col[1], base_col[2], alpha),
            width=int(min(w, h) * 0.04)
        )
    vig = vig.filter(ImageFilter.GaussianBlur(60))
    return Image.alpha_composite(img.convert('RGBA'), vig).convert('RGB')

def generate_custom_product_photo(
    output_filename,
    template_key,
    tint_rgba=(0, 0, 0, 0),
    contrast=1.1,
    brightness=1.0,
    saturation=1.1,
    zoom=1.0,
    crop_offset=(0, 0),
    flip_h=False,
    sunbeam=False,
    leaf_shadow=False,
    water_caustics=False,
    vignette_type='crisp_studio',
    vignette_strength=0.25,
    seed=1
):
    template_path = TEMPLATE_MAP[template_key]
    img = Image.open(template_path).convert('RGB')
    w, h = img.size
    
    # Horizontal flip if requested
    if flip_h:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
        
    # Zoom and pan
    if zoom > 1.0:
        crop_w = int(w / zoom)
        crop_h = int(h / zoom)
        left = (w - crop_w) // 2 + crop_offset[0]
        top = (h - crop_h) // 2 + crop_offset[1]
        left = max(0, min(w - crop_w, left))
        top = max(0, min(h - crop_h, top))
        img = img.crop((left, top, left + crop_w, top + crop_h)).resize((w, h), Image.LANCZOS)
        
    # Formula color tint
    if tint_rgba[3] > 0:
        tint_layer = Image.new('RGBA', (w, h), tint_rgba)
        img = Image.alpha_composite(img.convert('RGBA'), tint_layer).convert('RGB')
        
    # Lighting and environmental effects
    if sunbeam:
        img = apply_sunbeam(img, warm_color=(255, 230, 180) if 'warm' in vignette_type else (230, 245, 255))
    if leaf_shadow:
        img = apply_leaf_shadow(img, seed=seed)
    if water_caustics:
        img = apply_water_caustics(img)
        
    # Contrast, Brightness, Saturation
    if contrast != 1.0:
        img = ImageEnhance.Contrast(img).enhance(contrast)
    if brightness != 1.0:
        img = ImageEnhance.Brightness(img).enhance(brightness)
    if saturation != 1.0:
        img = ImageEnhance.Color(img).enhance(saturation)
        
    # Custom Vignette
    if vignette_strength > 0:
        img = apply_vignette(img, vignette_type=vignette_type, strength=vignette_strength)
        
    # Final unsharp mask for razor sharp cosmetics advertising finish
    img = img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=110, threshold=3))
    
    out_path = os.path.join(FRONTEND_IMAGES_DIR, output_filename)
    img.save(out_path, format='JPEG', quality=95, optimize=True)
    return out_path

print("Photo generation engine ready!")
