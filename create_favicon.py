"""
Create favicon.ico from TORQ logo for web server
"""
from PIL import Image
import os

# Paths
logo_png = r"C:\Users\asdasd\Downloads\TORQ CRYPTO BOT Logo Design.png"
output_favicon = r"E:\TORQ-CONSOLE\torq_console\ui\static\favicon.ico"

print("=" * 60)
print("TORQ Console Favicon Creator")
print("=" * 60)
print()

try:
    # Ensure static directory exists
    static_dir = os.path.dirname(output_favicon)
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
        print(f"[OK] Created directory: {static_dir}")

    # Load the PNG image
    print("[1/3] Loading TORQ logo...")
    img = Image.open(logo_png)
    print(f"[OK] Logo loaded: {img.size[0]}x{img.size[1]} pixels")
    print()

    # Convert to RGBA if needed
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # Create favicon with standard sizes
    print("[2/3] Creating favicon with multiple sizes...")
    favicon_sizes = [(32, 32), (16, 16)]

    # Save as ICO
    img.save(
        output_favicon,
        format='ICO',
        sizes=favicon_sizes
    )

    print(f"[OK] Favicon created: {output_favicon}")
    print(f"[OK] Sizes: {', '.join([f'{s[0]}x{s[1]}' for s in favicon_sizes])}")
    print()

    # Verify
    print("[3/3] Verifying favicon...")
    if os.path.exists(output_favicon):
        file_size = os.path.getsize(output_favicon)
        print(f"[OK] Favicon verified: {file_size:,} bytes")
        print()
        print("=" * 60)
        print("[SUCCESS] Favicon created for web server!")
        print("=" * 60)
        print()
        print(f"Location: {output_favicon}")
        print("The favicon will show in browser tabs automatically.")
    else:
        print("[ERROR] Favicon file was not created")
        exit(1)

except Exception as e:
    print(f"[ERROR] {str(e)}")
    exit(1)
