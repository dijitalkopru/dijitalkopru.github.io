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

        #model_name="google/gemma-4-e2b",
        #model_name="google/gemma-3-4b",
        model_name="google/gemma-4-12b-qat",
        
        
        images_folder="giris",
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
            "Aynı zamanda yaratıcı bir sosyal medya içerik üreticisisin. "
            "Sana gönderilen görseli 'Türkçe ve Türk Kültürü' dersi bağlamında incele. "
            "Görseli Instagram'da paylaşacağımızı düşünerek; takipçilerin ilgisini çekecek, "
            "merak uyandıran, kültürel derinliği olan, emojilerle süslenmiş ve uygun hashtag'ler içeren "
            "etkileyici bir Instagram post açıklaması yaz. "
            "Çıktıyı her zaman belirtilen JSON şemasına uygun olarak ver. Başka hiçbir açıklama yazma."
        )

        # API Gövdesi (Payload) - Yeni 'instagram_post' alanı şemaya eklendi
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_instruction},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Lütfen '{file_name}' isimli bu resmi Türkçe ve Türk kültürü dersi materyali olarak analiz et, etiketle ve ilgi çekici bir Instagram post metni oluştur.",
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
                            "instagram_post": {"type": "string"},  # Yeni eklenen alan
                            "etiketler": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["resim_adi", "icerik_ozeti", "instagram_post", "etiketler"],
                    },
                },
            },
            "temperature": 0.4, # Yaratıcılık için biraz artırıldı
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
                content_str = result_json["choices"][0]["message"]["content"]
                model_analysis = json.loads(content_str)

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

            base_name, _ = os.path.splitext(file_name)

            if result["success"]:
                report_data["analysis"] = result["analysis"]
                all_successful_results.append(result["analysis"])
                
                # --- YENİ MODİFİKASYON: INSTAGRAM TXT DOSYASI OLUŞTURMA ---
                instagram_post_text = result["analysis"].get("instagram_post", "")
                individual_txt_path = os.path.join(output_folder, f"{base_name}.txt")
                
                with open(individual_txt_path, "w", encoding="utf-8") as txt_file:
                    txt_file.write(instagram_post_text)
                # --------------------------------------------------------

                print(
                    f" ✓ TAMAMLANDI ({result['duration_seconds']}s, {result['token_usage']['total_tokens']} token) -> TXT Oluşturuldu"
                )
            else:
                report_data["error"] = result.get("error")
                print(f" ❌ HATA: {result.get('error')}")

            # Orijinal JSON kaydı (Yedeklilik ve metrik takibi için kalması faydalı)
            individual_json_path = os.path.join(
                output_folder, f"{base_name}_analiz.json"
            )
            with open(individual_json_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=4, ensure_ascii=False)

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
    processor = ImageBatchProcessor()
    processor.run()