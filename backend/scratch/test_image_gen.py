import os
from PIL import Image, ImageEnhance, ImageChops, ImageDraw, ImageFont, ImageFilter

def create_product_image(
    base_image_path,
    output_path,
    product_name,
    category_name,
    spec_text,
    tint_rgba=(0, 0, 0, 0),
    contrast=1.1,
    brightness=1.0,
    color_boost=1.1,
    zoom=1.05,
    crop_offset=(0, 0),
    flip=False,
    dark_badge=False
):
    # Load base image
    base = Image.open(base_image_path).convert('RGB')
    w, h = base.size
    
    if flip:
        base = base.transpose(Image.FLIP_LEFT_RIGHT)
        
    # Zoom and crop
    if zoom > 1.0:
        crop_w = int(w / zoom)
        crop_h = int(h / zoom)
        left = (w - crop_w) // 2 + crop_offset[0]
        top = (h - crop_h) // 2 + crop_offset[1]
        left = max(0, min(w - crop_w, left))
        top = max(0, min(h - crop_h, top))
        base = base.crop((left, top, left + crop_w, top + crop_h)).resize((w, h), Image.LANCZOS)
        
    # Tint overlay
    if tint_rgba[3] > 0:
        tint_layer = Image.new('RGBA', (w, h), tint_rgba)
        base_rgba = base.convert('RGBA')
        base = Image.alpha_composite(base_rgba, tint_layer).convert('RGB')
        
    # Enhancements
    if contrast != 1.0:
        base = ImageEnhance.Contrast(base).enhance(contrast)
    if brightness != 1.0:
        base = ImageEnhance.Brightness(base).enhance(brightness)
    if color_boost != 1.0:
        base = ImageEnhance.Color(base).enhance(color_boost)
        
    # Vignette
    vignette = Image.new('L', (w, h), 255)
    draw_v = ImageDraw.Draw(vignette)
    for i in range(100):
        alpha = int(255 - (i * 0.9))
        draw_v.rectangle([i*3, i*3, w - i*3, h - i*3], outline=alpha)
    vignette = vignette.filter(ImageFilter.GaussianBlur(40))
    
    # Render Luxury Editorial Badge at the bottom
    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    
    # Badge dimensions
    badge_w = int(w * 0.78)
    badge_h = 100
    badge_x = (w - badge_w) // 2
    badge_y = h - badge_h - 32
    
    # Frosted glass background
    if dark_badge:
        bg_color = (18, 22, 28, 215)
        border_color = (255, 255, 255, 50)
        title_color = (255, 255, 255, 245)
        subtitle_color = (190, 205, 220, 230)
        brand_color = (212, 175, 55, 240) # soft gold
    else:
        bg_color = (255, 255, 255, 220)
        border_color = (210, 200, 190, 140)
        title_color = (26, 26, 26, 245)
        subtitle_color = (95, 90, 85, 225)
        brand_color = (160, 110, 60, 235) # warm amber bronze
        
    # Draw rounded rectangle for badge
    draw_ov.rounded_rectangle(
        [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h],
        radius=14,
        fill=bg_color,
        outline=border_color,
        width=1
    )
    
    # Fonts
    font_brand = ImageFont.truetype('C:/Windows/Fonts/georgiab.ttf', 16)
    font_title = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 18)
    font_spec = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 13)
    
    # Text rendering
    brand_text = "J O Y O R Y"
    draw_ov.text((badge_x + 22, badge_y + 16), brand_text, fill=brand_color, font=font_brand)
    
    # Category tag on the right
    cat_text = category_name.upper()
    draw_ov.text((badge_x + badge_w - 90, badge_y + 18), cat_text, fill=subtitle_color, font=font_spec)
    
    # Product title (truncate if overly long)
    disp_title = product_name.replace("Joyory ", "")
    if len(disp_title) > 42:
        disp_title = disp_title[:40] + "..."
    draw_ov.text((badge_x + 22, badge_y + 42), disp_title, fill=title_color, font=font_title)
    
    # Spec text
    draw_ov.text((badge_x + 22, badge_y + 70), spec_text, fill=subtitle_color, font=font_spec)
    
    # Composite overlay
    final_img = Image.alpha_composite(base.convert('RGBA'), overlay).convert('RGB')
    final_img.save(output_path, quality=94)
    print(f"Successfully generated: {output_path}")

if __name__ == '__main__':
    # Test on product 30
    create_product_image(
        base_image_path='c:/Users/Yash/OneDrive/Desktop/joyory/frontend/public/images/products/product_4.jpg',
        output_path='c:/Users/Yash/OneDrive/Desktop/joyory/frontend/public/images/products/test_badge_30.jpg',
        product_name='Joyory Copper Tripeptide-1 Firming Booster',
        category_name='Serum',
        spec_text='Copper Tripeptide-1 • Hyaluronic Acid | 30ml / 1.0 fl oz',
        tint_rgba=(12, 45, 140, 85),
        contrast=1.18,
        color_boost=1.3,
        zoom=1.08,
        flip=True,
        dark_badge=True
    )
