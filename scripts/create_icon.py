#!/usr/bin/env python3
"""
Create ICO file for Prompt Manager

This script creates a simple ICO file with the project's color scheme.
"""

import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError as e:
    print("❌ Pillow not installed.")
    print("Please install it using:")
    print("  pip install Pillow")
    print(f"\nError: {e}")
    sys.exit(1)


def create_icon(ico_path: str, sizes: list = None):
    """
    Create ICO with multiple resolutions
    
    Args:
        ico_path: Path to output ICO file
        sizes: List of sizes to include (default: [16, 32, 48, 256])
    """
    if sizes is None:
        sizes = [16, 32, 48, 256]
    
    images = []
    
    for size in sizes:
        print(f"🎨 Creating {size}x{size} icon...")
        
        # Create new image with transparent background
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw background circle with project color (#0073FF)
        margin = size // 10
        draw.ellipse(
            [margin, margin, size - margin, size - margin],
            fill='#0073FF',
            outline=None
        )
        
        # Draw simple list icon representation
        bar_height = size // 8
        bar_margin = size // 4
        bar_spacing = size // 10
        
        for i in range(3):
            y = bar_margin + i * (bar_height + bar_spacing)
            opacity = int(255 * (1.0 - i * 0.3))  # Decreasing opacity
            
            # Draw white bar
            draw.rectangle(
                [bar_margin, y, size - bar_margin, y + bar_height],
                fill=(255, 255, 255, opacity)
            )
            
            # Draw small circle bullet
            circle_size = bar_height // 2
            circle_y = y + bar_height // 2 - circle_size // 2
            draw.ellipse(
                [bar_margin - circle_size - 5, circle_y, 
                 bar_margin - 5, circle_y + circle_size],
                fill=(255, 255, 255, opacity)
            )
        
        images.append(img)
    
    # Save as ICO with all sizes
    print(f"💾 Saving ICO: {ico_path}")
    images[0].save(
        ico_path,
        format='ICO',
        sizes=[(img.width, img.height) for img in images],
        append_images=images[1:]
    )
    
    print("✅ ICO file created successfully!")
    print(f"📁 Location: {ico_path}")
    print(f"📏 Sizes included: {', '.join(f'{s}x{s}' for s in sizes)}")


def main():
    """Main function"""
    # Get project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Define path
    ico_path = project_root / "public" / "logo.ico"
    
    # Create ICO
    print("🚀 Creating ICO file...")
    print("=" * 50)
    
    try:
        create_icon(str(ico_path))
        
        # Show file size
        file_size = ico_path.stat().st_size
        print(f"📦 File size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")
        
    except Exception as e:
        print(f"❌ Error during creation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("=" * 50)
    print("🎉 Done!")


if __name__ == "__main__":
    main()
