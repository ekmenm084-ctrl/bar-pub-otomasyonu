# Pub & Bar Otomasyonu - Kadeh ve Doluluk Takip Sistemi

Barlar ve pub'larda müşteri memnuniyetini ve sipariş hızını artırmak amacıyla geliştirilen; kadeh/tabak boşaldığında veya azaldığında kameralar aracılığıyla durumu tespit edip garsonlara bildiren akıllı yapay zeka & bilgisayarlı görü (computer vision) otomasyon sistemi.

---

## 📌 Proje Mimarisi (4 Aşamalı Plan)

### 1. Fiziksel Kurulum & Görüş Açısı (Donanım & "Smart Coaster" Hilesi)
- **Kamera Konumu:** Tavandan masayı kuşbakışı veya açılı gören IP kameralar.
- **Referans Altlık:** Loş ışıkta şeffaf bardağın içindeki sıvıyı doğrudan tespit etmenin zorluğunu aşmak için masalara yüksek kontrastlı renkli altlıklar yerleştirilir. Üzerine dolu bardak konduğunda ışık kırılması ve sıvı altlığı maskeler; içki azaldıkça/bittikçe altlık belirir.

### 2. Görüntü İşleme & Durum Algılama (AI & Vision Core)
- **Teknolojiler:** Python, OpenCV, NumPy, YOLOv8/v11.
- **Edge Computing:** Loş pub ortamında sıfır gecikme ve kesintisiz akış için yerel bilgisayar üzerinde anlık kare işleme.

### 3. Arka Plan Mantığı & Durum Makinesi (Backend)
- **Debounce / Zaman Sınırı Algoritması:** Müşteri kadehten yudum almak için bardağı her kaldırdığında sahte alarm verilmez. Altlık kesintisiz olarak belirli bir süre (ör. 3 dakika) boş kaldığında alarm tetiklenir.
- **API & Dağıtım:** FastAPI ve WebSocket üzerinden anlık durum yayınlama.

### 4. Garson Arayüzü (Frontend & Bildirim)
- Garsonun akıllı telefon veya saatine anında düşen titreşimli ve sesli minimalist uyarı:
  > **🔴 Masa 4 - İçki Bitti (Gidip İkinciyi Sor)**

---

## 🚀 Hızlı Başlangıç (PoC Testi)

### Gereksinimler
- Python 3.10+
- OpenCV (`pip install opencv-python numpy`)
- Web kamerası veya telefon kamerası (Iriun Webcam, IP Webcam vb.)

### Çalıştırma

1. **Laptop Kendi Kamerası:**
   - Masaüstündeki `testi_baslat_laptop.bat` dosyasına çift tıklayın veya:
   ```bash
   python poc_test.py --source 0
   ```

2. **Telefon Kamerası (IP Webcam):**
   - Masaüstündeki `testi_baslat_telefon_ip.bat` dosyasına çift tıklayın veya:
   ```bash
   python poc_test.py --source "http://<TELEFON_IP>:8080/video"
   ```

### Test Kontrolleri
- **Fare ile Sol Tık:** Masadaki altlığın/renkli kağıdın üzerine tıklayarak rengi anında tanıtır.
- **`c` Tuşu:** Ekran merkezindeki rengi referans alır.
- **`t` Tuşu:** Alarm test süresini 5 saniye ile 180 saniye (3 dakika) arasında değiştirir.
- **`q` Tuşu:** Çıkış.

---

## 📄 Lisans
Bu proje özel kullanım için geliştirilmektedir.
