from pathlib import Path
import csv

kok_klasor = Path("webs")  # Kendi klasörünüzle değiştirin
cikti_dosyasi = "dosyalar.csv"

with open(cikti_dosyasi, "w", newline="", encoding="utf-8-sig") as f:
    yazici = csv.writer(f)
    yazici.writerow(["dosya_adi", "klasor_adi"])

    for dosya in kok_klasor.rglob("*"):
        if dosya.is_file() and dosya.suffix.lower() in {".jpg", ".jpeg"}:
            yazici.writerow([dosya.name, dosya.parent.name])

print(f"CSV dosyası oluşturuldu: {cikti_dosyasi}")