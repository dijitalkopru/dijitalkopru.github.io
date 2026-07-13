import json
import csv

json_dosyasi = "veriler.json"
csv_dosyasi = "tasarlayanlar.csv"

# CSV'den eşleştirme sözlüğü oluştur
tasarlayan_map = {}
with open(csv_dosyasi, encoding="utf-8-sig", newline="") as f:
    okuyucu = csv.DictReader(f)
    for satir in okuyucu:
        tasarlayan_map[satir["dosya_adi"]] = satir["tasarlayan"]

# JSON'u oku
with open(json_dosyasi, encoding="utf-8") as f:
    veriler = json.load(f)

# Eşleşen kayıtları güncelle
for kayit in veriler:
    dosya = kayit.get("resim_adi")
    if dosya in tasarlayan_map:
        kayit["tasarlayan"] = tasarlayan_map[dosya]

# Güncellenmiş JSON'u kaydet
with open("veriler_guncel.json", "w", encoding="utf-8") as f:
    json.dump(veriler, f, ensure_ascii=False, indent=4)

print("Güncellenmiş JSON dosyası oluşturuldu.")