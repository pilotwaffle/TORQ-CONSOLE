"""
Create TORQ Console Icon with Tesla-style T design
Based on the image provided - red T with circuit board background
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_torq_icon():
    """Create a professional TORQ Console icon"""

    # Create 256x256 image (high resolution for icon)
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background - dark circle with circuit board pattern
    # Draw outer circle (dark background)
    center = size // 2
    radius = 120

    # Draw dark background circle
    draw.ellipse(
        [center - radius, center - radius, center + radius, center + radius],
        fill=(15, 20, 25, 255),  # Very dark blue-black
        outline=(60, 80, 100, 200),  # Subtle blue outline
        width=3
    )

    # Draw circuit board pattern (subtle lines)
    circuit_color = (40, 60, 80, 100)  # Subtle blue lines

    # Horizontal circuit lines
    for i in range(5, 12):
        y = center - radius + (i * 20)
        draw.line([(center - radius + 20, y), (center + radius - 20, y)],
                  fill=circuit_color, width=1)

    # Vertical circuit lines
    for i in range(5, 12):
        x = center - radius + (i * 20)
        draw.line([(x, center - radius + 20), (x, center + radius - 20)],
                  fill=circuit_color, width=1)

    # Draw circuit nodes (small circles)
    node_color = (60, 90, 120, 120)
    for i in range(6, 11):
        for j in range(6, 11):
            x = center - radius + (i * 20)
            y = center - radius + (j * 20)
            draw.ellipse([x-2, y-2, x+2, y+2], fill=node_color)

    # Draw the large red "T" (Tesla/TORQ style)
    # T shape using polygons for clean edges

    # Top horizontal bar of T
    t_color = (220, 30, 30, 255)  # Bright red
    t_top_left = center - 55
    t_top_right = center + 55
    t_top_y = center - 60
    t_bar_height = 20

    # Draw top bar
    draw.rectangle(
        [t_top_left, t_top_y, t_top_right, t_top_y + t_bar_height],
        fill=t_color
    )

    # Vertical stem of T
    t_stem_width = 30
    t_stem_left = center - t_stem_width // 2
    t_stem_right = center + t_stem_width // 2
    t_stem_top = t_top_y + t_bar_height - 5  # Slight overlap
    t_stem_bottom = center + 65

    # Draw stem (narrower at bottom for Tesla style)
    points = [
        (t_stem_left, t_stem_top),
        (t_stem_right, t_stem_top),
        (t_stem_right - 5, t_stem_bottom),
        (t_stem_left + 5, t_stem_bottom)
    ]
    draw.polygon(points, fill=t_color)

    # Add metallic highlight to T
    highlight_color = (255, 100, 100, 180)
    draw.rectangle(
        [t_top_left + 2, t_top_y + 2, t_top_right - 2, t_top_y + 6],
        fill=highlight_color
    )

    # Add text "CONSOLE" below the T
    try:
        # Try to use a bold font
        font = ImageFont.truetype("arial.ttf", 22)
        font_bold = ImageFont.truetype("arialbd.ttf", 24)
    except:
        font = ImageFont.load_default()
        font_bold = font

    # Draw "CONSOLE" text
    console_text = "CONSOLE"
    console_bbox = draw.textbbox((0, 0), console_text, font=font_bold)
    console_width = console_bbox[2] - console_bbox[0]
    console_x = center - console_width // 2
    console_y = t_stem_bottom + 15

    # Draw text with gradient effect (red to blue)
    # First part "CON" in red
    con_bbox = draw.textbbox((0, 0), "CON", font=font_bold)
    con_width = con_bbox[2] - con_bbox[0]
    draw.text((console_x, console_y), "CON", fill=(220, 60, 60, 255), font=font_bold)

    # Second part "SOLE" in light blue
    draw.text((console_x + con_width, console_y), "SOLE",
              fill=(120, 180, 220, 255), font=font_bold)

    # Add subtle glow effect around the circle
    glow_radius = radius + 5
    draw.ellipse(
        [center - glow_radius, center - glow_radius,
         center + glow_radius, center + glow_radius],
        outline=(80, 100, 140, 60),
        width=4
    )

    return img

def main():
    """Generate and save TORQ Console icon"""
    print("=" * 60)
    print("Creating TORQ Console Icon (Tesla-style T design)")
    print("=" * 60)
    print()

    # Create the icon
    print("Generating icon with red T design...")
    img = create_torq_icon()

    # Save as PNG first (high quality)
    png_path = "E:\\TORQ-CONSOLE\\torq_console_icon.png"
    img.save(png_path, "PNG")
    print(f"[OK] Saved PNG: {png_path}")

    # Convert to ICO with multiple sizes
    ico_path = "E:\\TORQ-CONSOLE\\torq_console_icon.ico"

    # Create multiple sizes for the ICO
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    images = []

    for size in sizes:
        resized = img.resize(size, Image.Resampling.LANCZOS)
        images.append(resized)

    # Save as ICO with all sizes
    images[0].save(
        ico_path,
        format='ICO',
        sizes=[(im.width, im.height) for im in images],
        append_images=images[1:]
    )

    print(f"[OK] Saved ICO: {ico_path}")
    print(f"[OK] Icon sizes: {', '.join([f'{s[0]}x{s[1]}' for s in sizes])}")
    print()
    print("=" * 60)
    print("[SUCCESS] TORQ Console icon created!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Run: E:\\TORQ-CONSOLE\\fix_icon.bat")
    print("  2. Press F5 on desktop to refresh")
    print("  3. Icon should now display the red T design!")
    print()

if __name__ == "__main__":
    main()
