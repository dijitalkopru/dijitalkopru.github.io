"""


📝 Bu Kod Ne İşe Yarar?
Bu kod, yerel bilgisayarında çalışan bir yapay zeka modelini (gemma-4-e2b) kullanarak bir klasör dolusu resmi otomatik olarak analiz eden bir toplu görsel işleyicidir.

Otomatik Tarama: jpgs klasöründeki yüzlerce .jpg veya .jpeg uzantılı resmi tek tek bulur.

Yapay Zeka Analizi: Her resmi arka planda base64 formatına çevirerek LM Studio'ya gönderir. Modelden resmi "Türkçe ve Türk Kültürü dersi materyali" gözüyle incelemesini ister.

Garantili Çıktı (JSON Schema): Yapay zekanın kafasına göre takılmasını engeller; kesinlikle belirlediğin şemada (resim_adi, icerik_ozeti, etiketler) veri üretmesini zorunlu kılar.

Güvenli Kayıt (Çift Katmanlı): 1. İşlem sırasında elektrik kesilse bile o ana kadar taranan her resim için anında resim_adi_analiz.json adında tekil bir dosya kaydeder (veri kaybını önler).
2. Tüm süreç bittiğinde, başarılı olan tüm analizleri tek bir büyük havuzda birleştirerek toplu_sonuc.json dosyasını oluşturur.

Metrik Takibi: Her resmin kaç saniyede analiz edildiğini ve kaç token harcandığını konsolda canlı olarak gösterir.

🛠️ Gereksinimler
Kodun sorunsuz çalışması için bilgisayarında şunların hazır olması gerekir:

Python 3.x: Bilgisayarında Python kurulu olmalı.

Gerekli Kütüphane: Terminal veya komut satırından şu kütüphaneyi kurmalısın:

Bash
pip install requests
LM Studio Ayarları:

Sunucu (Local Server) açık ve http://127.0.0.1:1234 adresinde dinlemede olmalı.

google/gemma-4-e2b modeli yüklü (Load Model) olmalı.

Modelin Vision Settings (Görsel İşleme) özelliği aktif olmalı.

Klasör Yapısı: Kodun çalıştırıldığı dizinde jpgs adında bir klasör bulunmalı ve analiz edilecek resimler bu klasörün içinde olmalı.
"""






import base64
import json
import os
import time
from glob import glob
import requests


class ImageBatchProcessor:

    def __init__(
        self,
        api_base_url="http://127.0.0.1:1234",
        model_name="google/gemma-4-e2b",
        images_folder="jpgs",
    ):
        self.api_base_url = api_base_url.rstrip("/")
        self.chat_url = f"{self.api_base_url}/v1/chat/completions"
        self.models_url = f"{self.api_base_url}/v1/models"
        self.model_name = model_name
        self.images_folder = images_folder
        self.timeout = 300  # Büyük görseller veya ilk yükleme için 5 dakika zaman aşımı

    def check_api_connection(self):
        """LM Studio API'sine erişilip erişilemediğini kontrol eder."""
        try:
            requests.get(self.models_url, timeout=5)
            return True
        except requests.RequestException:
            print(
                f"HATA: LM Studio API'ye ({self.api_base_url}) bağlanılamadı. Server açık mı?"
            )
            return False

    def encode_image_to_base64(self, image_path):
        """Görseli okuyup base64 string'e dönüştürür."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def get_image_files(self):
        """Klasördeki .jpg ve .jpeg uzantılı dosyaları listeler."""
        if not os.path.exists(self.images_folder):
            print(f"HATA: '{self.images_folder}' klasörü bulunamadı.")
            return []

        # Büyük/küçük harf duyarlılığı için glob pattern
        jpg_files = glob(os.path.join(self.images_folder, "*.[jJ][pP][gG]"))
        jpeg_files = glob(os.path.join(self.images_folder, "*.[jJ][pP][eE][gG]"))
        return sorted(jpg_files + jpeg_files)

    def analyze_image(self, image_path):
        """Tek bir görseli LM Studio'ya göndererek analiz eder."""
        file_name = os.path.basename(image_path)

        try:
            base64_image = self.encode_image_to_base64(image_path)
        except Exception as e:
            return {"success": False, "error": f"Görsel okunurken hata: {str(e)}"}

        system_instruction = (
            "Sen Türk dili, edebiyatı ve kültürü alanında uzman bir yapay zeka asistanısın. "
            "Sana gönderilen görseli 'Türkçe ve Türk Kültürü' dersi bağlamında incele. "
            "Çıktıyı her zaman belirtilen JSON şemasına uygun olarak ver. Başka hiçbir açıklama yazma."
        )

        # API Gövdesi (Payload) - LM Studio JSON Schema Yapısı Entegre Edildi
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_instruction},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Lütfen '{file_name}' isimli bu resmi Türkçe ve Türk kültürü dersi materyali olarak analiz et ve etiketle.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                },
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "resim_analiz_semasi",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "resim_adi": {"type": "string"},
                            "icerik_ozeti": {"type": "string"},
                            "etiketler": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["resim_adi", "icerik_ozeti", "etiketler"],
                    },
                },
            },
            "temperature": 0.3,
            "stream": False,
        }

        start_time = time.time()
        try:
            response = requests.post(
                self.chat_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout,
            )
            duration = time.time() - start_time

            if response.status_code == 200:
                result_json = response.json()
                # Model çıktısını string'den Python sözlüğüne çeviriyoruz
                content_str = result_json["choices"][0]["message"]["content"]
                model_analysis = json.loads(content_str)

                # Dosya adını garantiye alalım
                model_analysis["resim_adi"] = file_name

                usage = result_json.get("usage", {})

                return {
                    "success": True,
                    "analysis": model_analysis,
                    "duration_seconds": round(duration, 4),
                    "token_usage": {
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0),
                    },
                }
            else:
                return {
                    "success": False,
                    "error": f"API Hatası: {response.status_code} - {response.text}",
                    "duration_seconds": round(duration, 4),
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Zaman aşımı (Timeout)",
                "duration_seconds": round(time.time() - start_time, 4),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "duration_seconds": round(time.time() - start_time, 4),
            }

    def run(self):
        """Ana döngüyü çalıştırır."""
        print("LM Studio Görsel İşleyici Başlatılıyor...")

        if not self.check_api_connection():
            return

        image_files = self.get_image_files()
        if not image_files:
            print(
                f"İptal Edildi: '{self.images_folder}' klasöründe işlenecek resim bulunamadı."
            )
            return

        print(
            f"BİLGİ: '{self.images_folder}' klasöründe {len(image_files)} adet resim algılandı."
        )
        print(f"HEDEF MODEL: {self.model_name}")

        # Çıktı klasörünü temizle/oluştur
        safe_model_name = "".join(
            x for x in self.model_name if x.isalnum() or x in "-_."
        )
        output_folder = os.path.join(os.getcwd(), "outputs", safe_model_name)
        os.makedirs(output_folder, exist_ok=True)
        print(f"ÇIKTI KLASÖRÜ: {output_folder}\n")

        all_successful_results = []

        for index, image_path in enumerate(image_files, start=1):
            file_name = os.path.basename(image_path)
            print(
                f"[{index}/{len(image_files)}] Analiz ediliyor: {file_name}...",
                end="",
                flush=True,
            )

            result = self.analyze_image(image_path)

            # Her resmin kendi rapor verisini hazırla
            report_data = {
                "index": index,
                "file_name": file_name,
                "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "SUCCESS" if result["success"] else "FAILED",
                "metrics": {
                    "duration_seconds": result.get("duration_seconds", 0),
                    "token_usage": result.get("token_usage", {}),
                },
            }

            if result["success"]:
                # Modelden dönen analiz objesini rapora ekle
                report_data["analysis"] = result["analysis"]
                all_successful_results.append(result["analysis"])
                print(
                    f" ✓ TAMAMLANDI ({result['duration_seconds']}s, {result['token_usage']['total_tokens']} token)"
                )
            else:
                report_data["error"] = result.get("error")
                print(f" ❌ HATA: {result.get('error')}")

            # 1. Aşama Ayrıştırma: Her resmin sonucunu tekil JSON yap
            base_name, _ = os.path.splitext(file_name)
            individual_json_path = os.path.join(
                output_folder, f"{base_name}_analiz.json"
            )
            with open(individual_json_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=4, ensure_ascii=False)

        # 2. Aşama Ayrıştırma: Tüm başarılı analizleri tek bir büyük havuzda birleştir
        if all_successful_results:
            summary_json_path = os.path.join(output_folder, "toplu_sonuc.json")
            with open(summary_json_path, "w", encoding="utf-8") as f:
                json.dump(
                    all_successful_results, f, indent=4, ensure_ascii=False
                )
            print(
                f"\n✓ Başarılı analizlerin toplu listesi şuraya kaydedildi: {summary_json_path}"
            )

        print("\n" + "=" * 60)
        print("TÜM GÖRSEL İŞLEMLERİ TAMAMLANDI")
        print("=" * 60)


if __name__ == "__main__":
    # Varsayılan parametrelerle çalıştırır
    processor = ImageBatchProcessor()
    processor.run()