"""
Generate simple icon files for the TORQ Chrome Extension.
Run this with Pillow (PIL) installed, or use your own icons.
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    has_pil = True
except ImportError:
    has_pil = False
    print("PIL not available. Install with: pip install Pillow")

def create_icon(size, output_path):
    """Create a simple TORQ icon."""
    if not has_pil:
        # Create a minimal SVG that can be converted
        svg = f'''<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">
  <rect width="{size}" height="{size}" fill="#4cc9f0"/>
  <text x="50%" y="55%" text-anchor="middle" dominant-baseline="middle" font-size="{size//2}" fill="#000">T</text>
</svg>'''
        with open(output_path.replace('.png', '.svg'), 'w') as f:
            f.write(svg)
        print(f"Created {output_path.replace('.png', '.svg')}")
        return

    # Create image with PIL
    img = Image.new("RGB", (size, size), "#4cc9f0")
    draw = ImageDraw.Draw(img)

    # Draw a "T" for TORQ
    font_size = size // 2
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    # Draw border
    draw.rectangle([4, 4, size-5, size-5], outline="#000", width=2)

    # Draw T
    text = "T"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) // 2
    y = (size - text_height) // 2
    draw.text((x, y), text, fill="#000", font=font)

    img.save(output_path)
    print(f"Created {output_path}")

if __name__ == "__main__":
    import os
    icons_dir = os.path.join(os.path.dirname(__file__), "icons")

    for size in [16, 48, 128]:
        path = os.path.join(icons_dir, f"icon{size}.png")
        create_icon(size, path)

    print("\nIcons generated!")
    print("\nIf PIL is not available, SVG files were created.")
    print("Convert them to PNG using:")
    print("  - Online: https://cloudconvert.com/svg-to-png")
    print("  - CLI: magick icon.svg icon16.png")
