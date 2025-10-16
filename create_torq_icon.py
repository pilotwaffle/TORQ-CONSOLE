"""
Convert TORQ Console logo PNG to ICO format and update desktop shortcut
"""
from PIL import Image
import os

# Paths
logo_png = r"C:\Users\asdasd\Downloads\TORQ CRYPTO BOT Logo Design.png"
output_ico = r"E:\TORQ-CONSOLE\torq_console_icon.ico"

print("=" * 60)
print("TORQ Console Icon Creator")
print("=" * 60)
print()

try:
    # Check if PIL is available
    print("[1/4] Checking dependencies...")
    print("[OK] PIL/Pillow is available")
    print()

    # Load the PNG image
    print("[2/4] Loading TORQ logo...")
    print(f"Source: {logo_png}")

    if not os.path.exists(logo_png):
        print(f"[ERROR] Logo file not found at {logo_png}")
        print()
        print("Please ensure the TORQ logo PNG is in the Downloads folder.")
        exit(1)

    img = Image.open(logo_png)
    print(f"[OK] Logo loaded: {img.size[0]}x{img.size[1]} pixels")
    print()

    # Convert to RGBA if needed
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # Create icon with multiple sizes (Windows standard)
    print("[3/4] Creating ICO file with multiple sizes...")
    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]

    # Resize and save as ICO
    img.save(
        output_ico,
        format='ICO',
        sizes=icon_sizes
    )

    print(f"[OK] Icon created: {output_ico}")
    print(f"[OK] Sizes: {', '.join([f'{s[0]}x{s[1]}' for s in icon_sizes])}")
    print()

    # Verify the icon was created
    print("[4/4] Verifying icon file...")
    if os.path.exists(output_ico):
        file_size = os.path.getsize(output_ico)
        print(f"[OK] Icon file verified: {file_size:,} bytes")
        print()
        print("=" * 60)
        print("[SUCCESS] TORQ Console icon created!")
        print("=" * 60)
        print()
        print(f"Icon location: {output_ico}")
        print()
        print("Next step: Run the desktop shortcut creator to use this icon.")
    else:
        print("[ERROR] Icon file was not created")
        exit(1)

except ImportError as e:
    print("[ERROR] PIL/Pillow is not installed")
    print()
    print("Install it with: pip install Pillow")
    exit(1)

except Exception as e:
    print(f"[ERROR] {str(e)}")
    exit(1)
