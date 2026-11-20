"""
Bar / Pub Kadeh & Altlık Takip PoC (Proof of Concept)
-----------------------------------------------------
Kullanım:
  1. Laptop kamerası için:
       python poc_test.py --source 0
  2. Telefon (IP Webcam / DroidCam Wi-Fi URL) için:
       python poc_test.py --source "http://192.168.1.X:8080/video"
  3. DroidCam/Iriun USB/Sanal kamera için:
       python poc_test.py --source 1

Kontroller:
  - Fare ile sol tık: Tıkladığınız yerin rengini (altlığınızın rengini) referans renk olarak seçer.
  - 'c': Ekran ortasındaki rengi otomatik referans alır.
  - 't': Test için alarm süresini 5 saniye ile 180 saniye (3 dk) arasında değiştirir.
  - 'q': Çıkış.
"""

import cv2
import numpy as np
import time
import argparse
import sys
import os
import json
import urllib.request
import threading

# Windows sesli uyarı desteği
try:
    import winsound
    HAS_SOUND = True
except ImportError:
    HAS_SOUND = False

# Argümanları al
parser = argparse.ArgumentParser(description="Pub Bardak Doluluk Takip PoC")
parser.add_argument("--source", default="0", help="Kamera indeksi (0, 1) veya IP Webcam URL'i")
parser.add_argument("--alarm_sec", type=int, default=5, help="Test için alarm süresi (saniye)")
parser.add_argument("--table", default="Masa 1", help="Kameranın bağlı olduğu masa adı (örn: Masa 1, VIP 2)")
parser.add_argument("--server", default="http://localhost:8000", help="Mobil sunucu adresi")
args = parser.parse_args()

table_id_name = args.table
server_url = args.server
alert_sent_to_server = False

def notify_mobile_server(table_name, srv_url):
    try:
        url = f"{srv_url}/api/alert"
        payload = json.dumps({
            "table_id": table_name,
            "alert_type": "empty_glass",
            "message": "Kadeh Bitti! (2. Siparişi Sor)"
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=1.5)
        print(f"[BILGI] Mobil aplikasyona ({table_name}) bildirimi firlatildi!")
    except Exception as e:
        # Sunucu kapalıysa sessizce geç
        pass

# Kamera kaynağını belirle
source = args.source
if source.isdigit():
    source = int(source)

cap = cv2.VideoCapture(source)
if not cap.isOpened():
    print(f"[HATA] Kamera kaynagi acilamadi: {source}")
    print("Ipuclari:")
    print("1. Laptop kamerasi icin '--source 0' deneyin.")
    print("2. Telefon IP kamerasi kullaniyorsaniz: '--source http://192.168.1.X:8080/video'")
    sys.exit(1)

# Hedef renk (HSV formatında) - Varsayılan: Parlak Yeşil (Neon Green)
# [Hue: 35-85, Saturation: 60-255, Value: 60-255]
target_hsv = np.array([60, 200, 200]) # Varsayılan yeşil tonu
hsv_tolerance = np.array([20, 100, 100]) # Renk esneklik payı

target_color_calibrated = False
alarm_threshold_sec = args.alarm_sec
empty_start_time = None
alarm_triggered = False

def on_mouse_click(event, x, y, flags, param):
    global target_hsv, target_color_calibrated, hsv_tolerance
    if event == cv2.EVENT_LBUTTONDOWN:
        frame_hsv = param['frame_hsv']
        if frame_hsv is not None and 0 <= y < frame_hsv.shape[0] and 0 <= x < frame_hsv.shape[1]:
            # Tıklanan pikselin etrafındaki 5x5 alanı ortala (gürültüyü önlemek için)
            y1, y2 = max(0, y-2), min(frame_hsv.shape[0], y+3)
            x1, x2 = max(0, x-2), min(frame_hsv.shape[1], x+3)
            patch = frame_hsv[y1:y2, x1:x2]
            avg_hsv = np.mean(patch, axis=(0, 1)).astype(int)
            target_hsv = avg_hsv
            target_color_calibrated = True
            print(f"[BILGI] Yeni referans altlik rengi secildi (HSV: {target_hsv})")

cv2.namedWindow("Pub Bardak Takip Testi")
mouse_params = {'frame_hsv': None}
cv2.setMouseCallback("Pub Bardak Takip Testi", on_mouse_click, mouse_params)

print("\n" + "="*50)
print(" SISTEM BASLATILDI")
print(" Masaniza parlak bir altlik (veya renkli bir kagit) koyun.")
print(" Altliga fare ile sol tiklayarak rengi tanitin.")
print(f" Alarm suresi: {alarm_threshold_sec} saniye (Degistirmek icin 't')")
print(" Cikmak icin 'q' tusuna basin.")
print("="*50 + "\n")

while True:
    ret, frame = cap.read()
    if not ret:
        print("[UYARI] Goruntu alinamadi.")
        break

    # Görüntüyü hafif yumuşat
    blurred = cv2.GaussianBlur(frame, (5, 5), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    mouse_params['frame_hsv'] = hsv

    h, w = frame.shape[:2]

    # Ekranın ortasında bir ROI (Odak Alanı) belirle
    roi_w, roi_h = int(w * 0.45), int(h * 0.55)
    roi_x1 = (w - roi_w) // 2
    roi_y1 = (h - roi_h) // 2
    roi_x2 = roi_x1 + roi_w
    roi_y2 = roi_y1 + roi_h

    roi_hsv = hsv[roi_y1:roi_y2, roi_x1:roi_x2]

    # Renk Aralığı Hesaplama
    lower_bound = np.clip(target_hsv - hsv_tolerance, [0, 50, 50], [179, 255, 255])
    upper_bound = np.clip(target_hsv + hsv_tolerance, [0, 50, 50], [179, 255, 255])

    # Altlık maskesini çıkar
    mask = cv2.inRange(roi_hsv, lower_bound, upper_bound)
    
    # Morfolojik temizleme (küçük parazitleri yok et)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # Görünürlük oranı: Odak alanındaki altlık piksel yüzdesi
    total_roi_pixels = roi_w * roi_h
    coaster_pixels = cv2.countNonZero(mask)
    visibility_ratio = (coaster_pixels / total_roi_pixels) * 100

    # DURUM BELIRLEME (Eşik Değeri: Altlığın %30'undan fazlası görünüyorsa bardak boş/azalmış sayılır)
    # Bardağın içi dolu veya yarımken sıvı ışığı kırar/maskeler, oran düşer.
    is_empty_or_low = visibility_ratio > 30.0

    current_time = time.time()
    timer_text = ""

    if is_empty_or_low:
        if empty_start_time is None:
            empty_start_time = current_time
        
        elapsed = current_time - empty_start_time
        remaining = max(0.0, alarm_threshold_sec - elapsed)
        
        if elapsed >= alarm_threshold_sec:
            if not alarm_triggered and HAS_SOUND:
                try:
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                except Exception:
                    pass
            if not alert_sent_to_server:
                threading.Thread(target=notify_mobile_server, args=(table_id_name, server_url), daemon=True).start()
                alert_sent_to_server = True
            alarm_triggered = True
            timer_text = f"ALARM: {table_id_name} SURE DOLDU! GARSON BILDIRILDI"
        else:
            alarm_triggered = False
            timer_text = f"BOS ALGILANDI: {remaining:.1f}s sonra alarm"
    else:
        # Bardak dolu/üzeri kapalı, sayacı sıfırla
        empty_start_time = None
        alarm_triggered = False
        alert_sent_to_server = False
        timer_text = f"DURUM: {table_id_name} DOLU / ICILIYOR"

    # GÖRSEL ARAYÜZ ÇİZİMİ
    # Odak Alanı Çerçevesi
    roi_color = (0, 0, 255) if alarm_triggered else ((0, 165, 255) if is_empty_or_low else (0, 255, 0))
    cv2.rectangle(frame, (roi_x1, roi_y1), (roi_x2, roi_y2), roi_color, 2)
    cv2.putText(frame, "MASA 1 - ODAK ALANI", (roi_x1, roi_y1 - 10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, roi_color, 2)

    # Üst Bilgi Paneli (Koyu arkaplan)
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 85), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    # Durum ve İstatistik Yazıları
    stat_color = (0, 0, 255) if alarm_triggered else ((0, 200, 255) if is_empty_or_low else (0, 255, 100))
    cv2.putText(frame, f"Altlik Gorunurluk: %{visibility_ratio:.1f}", (15, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, timer_text, (15, 65), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.75, stat_color, 2)

    # Kalibre uyarısı
    if not target_color_calibrated:
        cv2.putText(frame, "[IPUCU: Altligin uzerine fare ile TIKLAYIN!]", (w - 420, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1)

    # Ekrana basılan ALARM Efekti
    if alarm_triggered:
        cv2.rectangle(frame, (0, h - 70), (w, h), (0, 0, 200), -1)
        cv2.putText(frame, "!!! MASA 1 - ICKI BITTI (SIPARIS ALIN) !!!", 
                    (w // 2 - 250, h - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    # Sağ alt köşeye mini maske önizlemesi yerleştir
    mask_small = cv2.resize(mask, (160, 120))
    mask_bgr = cv2.cvtColor(mask_small, cv2.COLOR_GRAY2BGR)
    frame[h - 130:h - 10, w - 170:w - 10] = mask_bgr
    cv2.rectangle(frame, (w - 170, h - 130), (w - 10, h - 10), (255, 255, 255), 1)
    cv2.putText(frame, "Maske Onizleme", (w - 165, h - 115), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

    cv2.imshow("Pub Bardak Takip Testi", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('c'):
        # Merkez noktayı referans al
        center_hsv = hsv[h // 2, w // 2]
        target_hsv = center_hsv
        target_color_calibrated = True
        print(f"[BILGI] Merkez renk secildi: {target_hsv}")
    elif key == ord('t'):
        alarm_threshold_sec = 180 if alarm_threshold_sec == 5 else 5
        print(f"[BILGI] Alarm esik suresi: {alarm_threshold_sec} saniye yapildi.")

cap.release()
cv2.destroyAllWindows()
