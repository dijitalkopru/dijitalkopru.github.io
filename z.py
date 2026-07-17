import os
import random


import os
from PIL import Image

# Klasör yolu
klasor_yolu = "./"  # burayı değiştir

for dosya in os.listdir(klasor_yolu):
    if dosya.lower().endswith(".png"):
        png_yolu = os.path.join(klasor_yolu, dosya)
        
        # Yeni dosya adı (.jpg)
        jpg_dosya_adi = os.path.splitext(dosya)[0] + ".jpg"
        jpg_yolu = os.path.join(klasor_yolu, jpg_dosya_adi)

        # PNG'yi aç ve JPG olarak kaydet
        with Image.open(png_yolu) as img:
            rgb_img = img.convert("RGB")  # PNG transparan olabilir
            rgb_img.save(jpg_yolu, "JPEG", quality=95)

print("Tüm PNG dosyaları JPG'ye dönüştürüldü.")








# Dosyaların bulunduğu klasör
folder = "./"  # burayı kendi klasör yolunuzla değiştirin

# Sadece jpg dosyalarını al
files = [f for f in os.listdir(folder) if f.lower().endswith(".jpg")]

# Numara listesini hazırla ve karıştır
numbers = list(range(1, len(files)+1))
random.shuffle(numbers)

# Dosyaları geçici isimle değiştir (çakışmayı önlemek için)
temp_files = []
for i, f in enumerate(files):
    temp_name = f"temp_{i}.jpg"
    os.rename(os.path.join(folder, f), os.path.join(folder, temp_name))
    temp_files.append(temp_name)

# Şimdi karışık numaraları atayarak yeniden isimlendir
for temp_name, num in zip(temp_files, numbers):
    new_name = f"{num:03d}.jpg"  # 001, 002 ... 205
    os.rename(os.path.join(folder, temp_name), os.path.join(folder, new_name))

print("Dosyalar rastgele numaralandırıldı!")