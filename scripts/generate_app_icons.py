from pathlib import Path
from PIL import Image

root = Path(r"C:\Users\andy_\Documents\Taller\APP_TALLER_PINTURA")
source = Path(r"C:\Users\andy_\AppData\Local\Temp\codex-clipboard-1648b34a-f413-4cac-b9f9-aae016759685.png")

img = Image.open(source).convert("RGBA")
base_size = 1024
safe_ratio = 0.82
safe_size = int(base_size * safe_ratio)
offset = (base_size - safe_size) // 2
canvas = Image.new("RGBA", (base_size, base_size), (0, 0, 0, 0))
resized = img.resize((safe_size, safe_size), Image.Resampling.LANCZOS)
canvas.paste(resized, (offset, offset), resized)

assets_dir = root / "static" / "assets"
assets_dir.mkdir(parents=True, exist_ok=True)
canvas.save(assets_dir / "app-icon-source.png")
canvas.resize((512, 512), Image.Resampling.LANCZOS).save(assets_dir / "icon-512.png")
canvas.resize((512, 512), Image.Resampling.LANCZOS).save(assets_dir / "icon-maskable-512.png")
canvas.resize((192, 192), Image.Resampling.LANCZOS).save(assets_dir / "icon-192.png")
canvas.resize((256, 256), Image.Resampling.LANCZOS).save(assets_dir / "app-icon.ico")

android_sizes = {
    "mipmap-mdpi": 48,
    "mipmap-hdpi": 72,
    "mipmap-xhdpi": 96,
    "mipmap-xxhdpi": 144,
    "mipmap-xxxhdpi": 192,
}

for folder, size in android_sizes.items():
    target_dir = root / "android" / "app" / "src" / "main" / "res" / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    rendered = canvas.resize((size, size), Image.Resampling.LANCZOS)
    rendered.save(target_dir / "ic_launcher.png")
    rendered.save(target_dir / "ic_launcher_round.png")
    rendered.save(target_dir / "ic_launcher_foreground.png")

print("OK")
