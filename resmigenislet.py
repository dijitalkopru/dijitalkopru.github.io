from PIL import Image
import os

INPUT_DIR = "giris"
OUTPUT_DIR = "cikis"
TARGET_RATIO = 4 / 5  # Instagram dikey gönderi oranı

os.makedirs(OUTPUT_DIR, exist_ok=True)

for fname in os.listdir(INPUT_DIR):
    if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
        continue

    img = Image.open(os.path.join(INPUT_DIR, fname)).convert("RGB")
    w, h = img.size

    if w / h < TARGET_RATIO:
        new_w = int(h * TARGET_RATIO)
        new_h = h
    else:
        new_w = w
        new_h = int(w / TARGET_RATIO)

    # Kenar piksellerinin ortalamasını arka plan rengi olarak kullan
    border = []
    border.extend(list(img.crop((0, 0, w, 1)).getdata()))
    border.extend(list(img.crop((0, h - 1, w, h)).getdata()))
    border.extend(list(img.crop((0, 0, 1, h)).getdata()))
    border.extend(list(img.crop((w - 1, 0, w, h)).getdata()))

    avg_color = tuple(
        int(sum(p[i] for p in border) / len(border))
        for i in range(3)
    )

    canvas = Image.new("RGB", (new_w, new_h), avg_color)
    x = (new_w - w) // 2
    y = (new_h - h) // 2
    canvas.paste(img, (x, y))

    canvas.save(os.path.join(OUTPUT_DIR, fname))

print("Tamamlandı.")