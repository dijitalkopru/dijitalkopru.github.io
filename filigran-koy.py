from pathlib import Path
from PIL import Image

# Ayarlar
input_dir = Path("cikis")
watermark_path = Path("damga.png")

scale = 0.205      # Filigranın genişliği / resim genişliği oranı
opacity = 0.5     # 0.0 (tam şeffaf) - 1.0 (tam opak)
margin = 10       # Kenar boşluğu (piksel)

wm_original = Image.open(watermark_path).convert("RGBA")

for img_path in input_dir.iterdir():
    if img_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
        continue

    img = Image.open(img_path).convert("RGBA")

    # Filigranı yeniden boyutlandır
    new_w = int(img.width * scale)
    new_h = int(wm_original.height * new_w / wm_original.width)
    wm = wm_original.resize((new_w, new_h), Image.LANCZOS)

    # Şeffaflığı ayarla
    alpha = wm.getchannel("A").point(lambda a: int(a * opacity))
    wm.putalpha(alpha)

    # Sol alt köşe konumu
    pos = (margin, img.height - wm.height - margin)

    img.paste(wm, pos, wm)

    # Orijinal dosyanın üzerine kaydet
    if img_path.suffix.lower() in {".jpg", ".jpeg"}:
        img.convert("RGB").save(img_path, quality=95)
    else:
        img.save(img_path)

print("Filigralama tamamlandı.")