# VisionTouch: Yapay Zeka Tabanlı Jest Kontrol Süiti
## Eksiksiz Geliştirme, Mimari ve Uygulama Planı

Bu doküman; **el takibi (Hand Tracking)**, **sanal fare (Virtual Mouse)**, **havada çizim (Air Canvas)** ve **medya kontrollerini (Media Controller)** tek bir Python mimarisi altında sıfırdan hayata geçirmek için gereken tüm kurulum, mimari, matematiksel mantık ve referans uygulama detaylarını içerir.

---

## 📋 İçindekiler
1. [Proje Mimarisi ve Dizin Yapısı](#1-proje-mimarisi-ve-dizin-yapısı)
2. [Ortam Kurulumu ve Bağımlılıklar](#2-ortam-kurulumu-ve-bağımlılıklar)
3. [MediaPipe El Anatomisi ve Matematiksel Mantık](#3-mediapipe-el-anatomisi-ve-matematiksel-mantık)
   - [3.1 21 Eklem Noktası (Landmarks)](#31-21-eklem-noktası-landmark-haritası)
   - [3.2 Parmak Açık/Kapalı Tespiti](#32-parmak-açıkkapalı-tespiti)
   - [3.3 İki Nokta Arasındaki Öklid Mesafesi](#33-iki-nokta-arasındaki-öklid-mesafesi)
   - [3.4 İmleç Yumuşatma (Exponential Moving Average)](#34-imleç-yumuşatma-exponential-moving-average)
4. [Çekirdek Motor (Core Engine: HandDetector)](#4-çekirdek-motor-corehand_detectorpy)
5. [Modüller](#5-modüller)
   - [Modül 1: Sanal Fare (Virtual Mouse)](#51-modül-1---sanal-fare-modulesvirtual_mousepy)
   - [Modül 2: Havada Çizim (Air Canvas)](#52-modül-2---havada-çizim-modulesair_canvaspy)
   - [Modül 3: Medya ve Ses Kontrolü (Media Controller)](#53-modül-3---medya-ve-ses-kontrolü-modulesmedia_controllerpy)
6. [Ana Yönetici (Main Runner)](#6-ana-yönetici-mainpy)
7. [Test, Kalibrasyon ve Optimizasyon İpuçları](#7-test-ve-kalibrasyon-ipuçları)

---

## 1. Proje Mimarisi ve Dizin Yapısı

Proje, kod tekrarını önlemek ve yüksek genişletilebilirlik sağlamak amacıyla ortak bir motor (`HandDetector`) üzerine inşa edilen modüler bir mimariye sahiptir.

```plaintext
VisionTouch/
│
├── core/
│   ├── __init__.py
│   └── hand_detector.py         # MediaPipe motoru, eklem tespiti ve koordinat çıkarımı
│
├── modules/
│   ├── __init__.py
│   ├── virtual_mouse.py         # Sanal fare imleç hareketi ve tıklama kontrolü
│   ├── air_canvas.py            # Havada çizim, renk paleti ve silgi motoru
│   └── media_controller.py      # Ses seviyesi ve medya kontrolleri
│
├── main.py                      # Modlar arası konsol tabanlı geçiş sağlayan ana yönetici
├── requirements.txt             # Gerekli Python bağımlılıkları
└── README.md                    # Mimari ve kullanım dokümantasyonu
```

---

## 2. Ortam Kurulumu ve Bağımlılıklar

> **Tavsiye:** Python 3.10 veya 3.11 sürümü önerilir.

### 2.1 Sanal Ortamın Oluşturulması

```bash
# Proje dizinine giriş
cd VisionTouch

# Sanal ortam oluşturma
python -m venv venv

# Sanal ortamı etkinleştirme:
# Windows (PowerShell / CMD):
venv\Scripts\activate

# macOS / Linux:
source venv/bin/activate
```

### 2.2 `requirements.txt` Bağımlılık Listesi

```plaintext
opencv-python>=4.8.0
mediapipe>=0.10.0
numpy>=1.24.0
pyautogui>=0.9.54
pycaw>=20240210; platform_system == "Windows"
comtypes>=1.2.0; platform_system == "Windows"
```

Paketlerin yüklenmesi:
```bash
pip install -r requirements.txt
```

---

## 3. MediaPipe El Anatomisi ve Matematiksel Mantık

MediaPipe Hands, el üzerinde 21 adet 3 boyutlu normalize edilmiş eklem noktası ($x, y, z$) döndürür.

### 3.1 21 Eklem Noktası (Landmark Haritası)

| ID | Eklem Tanımı (Landmark) | ID | Eklem Tanımı (Landmark) |
|---|---|---|---|
| **0** | Bilek (WRIST) | **11** | Orta Parmak DIP |
| **1** | Başparmak CMC | **12** | **Orta Parmak Ucu (MIDDLE FINGER TIP)** |
| **2** | Başparmak MCP | **13** | Yüzük Parmağı MCP |
| **3** | Başparmak IP | **14** | Yüzük Parmağı PIP |
| **4** | **Başparmak Ucu (THUMB TIP)** | **15** | Yüzük Parmağı DIP |
| **5** | İşaret Parmağı MCP | **16** | **Yüzük Parmağı Ucu (RING FINGER TIP)** |
| **6** | İşaret Parmağı PIP | **17** | Serçe Parmak MCP |
| **7** | İşaret Parmağı DIP | **18** | Serçe Parmak PIP |
| **8** | **İşaret Parmağı Ucu (INDEX FINGER TIP)** | **19** | Serçe Parmak DIP |
| **9** | Orta Parmak MCP | **20** | **Serçe Parmak Ucu (PINKY TIP)** |
| **10**| Orta Parmak PIP | | |

---

### 3.2 Parmak Açık/Kapalı Tespiti

- **İşaret, Orta, Yüzük ve Serçe Parmakları:** Parmak ucunun ($y_{\text{tip}}$), bir alt ekleminden ($y_{\text{pip}}$) ekranda daha yukarıda (y ekseninde piksel değeri daha küçük) olup olmadığı kontrol edilir:
  $$\text{Parmak Açık} \iff y_{\text{tip}} < y_{\text{pip}}$$
- **Başparmak:** Sağ el referans alındığında yatay eksen ($x$) bazlı kontrol yapılır ($x_{\text{tip}} > x_{\text{ip}}$ veya el yönüne göre normalize edilir).

---

### 3.3 İki Nokta Arasındaki Öklid Mesafesi

İki parmak ucu veya eklem arasındaki piksel mesafesi şu formülle hesaplanır:
$$d = \sqrt{(x_2 - x_1)^2 + (y_2 - y_1)^2}$$

---

### 3.4 İmleç Yumuşatma (Exponential Moving Average)

Kameradaki mikro-titremelerin fare imlecine yansımasını önlemek ve akıcı bir deneyim sunmak için yumuşatma filtresi uygulanır:
$$x_{\text{mevcut}} = x_{\text{önceki}} + \frac{x_{\text{hedef}} - x_{\text{önceki}}}{\text{smooth\_factor}}$$

---

## 4. Çekirdek Motor (`core/hand_detector.py`)

Tüm alt modüllerin ortak olarak kullandığı el tespit, eklem pozisyonu ve mesafe hesaplama sınıfıdır.

```python
import cv2
import mediapipe as mp
import math

class HandDetector:
    def __init__(self, mode=False, max_hands=1, detection_con=0.7, track_con=0.5):
        self.mode = mode
        self.max_hands = max_hands
        self.detection_con = detection_con
        self.track_con = track_con

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.max_hands,
            min_detection_confidence=self.detection_con,
            min_tracking_confidence=self.track_con
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.tip_ids = [4, 8, 12, 16, 20]
        self.lm_list = []

    def find_hands(self, img, draw=True):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)

        if self.results.multi_hand_landmarks:
            for hand_lms in self.results.multi_hand_landmarks:
                if draw:
                    self.mp_draw.draw_landmarks(img, hand_lms, self.mp_hands.HAND_CONNECTIONS)
        return img

    def find_positions(self, img, hand_no=0):
        self.lm_list = []
        if self.results.multi_hand_landmarks:
            my_hand = self.results.multi_hand_landmarks[hand_no]
            h, w, c = img.shape
            for id, lm in enumerate(my_hand.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                self.lm_list.append([id, cx, cy])
        return self.lm_list

    def fingers_up(self):
        fingers = []
        if len(self.lm_list) == 0:
            return fingers

        # Başparmak (Sağ el referansı: başparmak ucu, bir önceki boğumun solunda/sağında mı)
        if self.lm_list[self.tip_ids[0]][1] > self.lm_list[self.tip_ids[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)

        # Diğer 4 parmak (Y ekseninde uç, alt boğumdan yukarıda mı)
        for id in range(1, 5):
            if self.lm_list[self.tip_ids[id]][2] < self.lm_list[self.tip_ids[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
        return fingers

    def find_distance(self, p1, p2, img=None, draw=True):
        x1, y1 = self.lm_list[p1][1], self.lm_list[p1][2]
        x2, y2 = self.lm_list[p2][1], self.lm_list[p2][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        length = math.hypot(x2 - x1, y2 - y1)

        if draw and img is not None:
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 2)
            cv2.circle(img, (cx, cy), 5, (0, 0, 255), cv2.FILLED)

        return length, img, [x1, y1, x2, y2, cx, cy]
```

---

## 5. Modüller

### 5.1 Modül 1 - Sanal Fare (`modules/virtual_mouse.py`)

- **Hareket Modu:** Yalnızca işaret parmağı açıksa ($fingers = [0, 1, 0, 0, 0]$), işaret parmağının koordinatları ekran çözünürlüğüne dönüştürülür ve imleç yumuşatılarak hareket ettirilir.
- **Tıklama Modu:** İşaret ve orta parmak açık ve birbirine yakınsa ($d < 35 \text{ px}$), sol tıklama (`pyautogui.click()`) tetiklenir.

```python
import cv2
import numpy as np
import pyautogui
import time
from core.hand_detector import HandDetector

def run_virtual_mouse():
    w_cam, h_cam = 640, 480
    frame_r = 100  # Ekran kenar payı (margin)
    smoothening = 5

    p_loc_x, p_loc_y = 0, 0
    c_loc_x, c_loc_y = 0, 0

    cap = cv2.VideoCapture(0)
    cap.set(3, w_cam)
    cap.set(4, h_cam)

    detector = HandDetector(max_hands=1, detection_con=0.8)
    w_scr, h_scr = pyautogui.size()
    pyautogui.FAILSAFE = False

    while True:
        success, img = cap.read()
        if not success:
            break

        img = cv2.flip(img, 1)
        img = detector.find_hands(img)
        lm_list = detector.find_positions(img)

        if len(lm_list) != 0:
            x1, y1 = lm_list[8][1:]   # İşaret parmağı ucu
            x2, y2 = lm_list[12][1:]  # Orta parmak ucu
            fingers = detector.fingers_up()

            cv2.rectangle(img, (frame_r, frame_r), (w_cam - frame_r, h_cam - frame_r), (255, 0, 255), 2)

            # Hareket modu: Sadece işaret parmağı açık
            if fingers[1] == 1 and fingers[2] == 0:
                x3 = np.interp(x1, (frame_r, w_cam - frame_r), (0, w_scr))
                y3 = np.interp(y1, (frame_r, h_cam - frame_r), (0, h_scr))

                c_loc_x = p_loc_x + (x3 - p_loc_x) / smoothening
                c_loc_y = p_loc_y + (y3 - p_loc_y) / smoothening

                pyautogui.moveTo(c_loc_x, c_loc_y)
                cv2.circle(img, (x1, y1), 10, (255, 0, 0), cv2.FILLED)
                p_loc_x, p_loc_y = c_loc_x, c_loc_y

            # Tıklama modu: İşaret ve orta parmak açık ve birbirine yakın
            if fingers[1] == 1 and fingers[2] == 1:
                length, img, _ = detector.find_distance(8, 12, img)
                if length < 35:
                    cv2.circle(img, (x1, y1), 10, (0, 255, 0), cv2.FILLED)
                    pyautogui.click()
                    time.sleep(0.15)

        cv2.putText(img, "Mod: Sanal Fare (Cikis: Q)", (10, 30), cv2.FONT_HERSHEY_PLAIN, 1.5, (0, 255, 0), 2)
        cv2.imshow("VisionTouch - Sanal Fare", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_virtual_mouse()
```

---

### 5.2 Modül 2 - Havada Çizim (`modules/air_canvas.py`)

- **Seçim Modu:** İşaret ve orta parmak birlikte açıksa, üst menüdeki renk butonları (Kırmızı, Yeşil, Mavi, Sarı, Silgi) seçilebilir.
- **Çizim Modu:** Sadece işaret parmağı açıksa, seçili renkte çizim tuvaline (`img_canvas`) ve kamera çerçevesine çizgiler çizilir.
- **Maskeleme:** Şeffaf çizim hissi için `cv2.bitwise_and` ve `cv2.bitwise_or` operasyonları uygulanır.

```python
import cv2
import numpy as np
from core.hand_detector import HandDetector

def run_air_canvas():
    cap = cv2.VideoCapture(0)
    cap.set(3, 1280)
    cap.set(4, 720)

    detector = HandDetector(detection_con=0.85)
    draw_color = (0, 0, 255) # Varsayılan Kırmızı
    brush_thickness = 12
    eraser_thickness = 50

    xp, yp = 0, 0
    img_canvas = np.zeros((720, 1280, 3), np.uint8)

    while True:
        success, img = cap.read()
        if not success:
            break

        img = cv2.flip(img, 1)
        img = detector.find_hands(img)
        lm_list = detector.find_positions(img)

        # Üst Arayüz (Renk Paleti Butonları)
        cv2.rectangle(img, (50, 10), (250, 90), (0, 0, 255), cv2.FILLED)      # Kırmızı
        cv2.rectangle(img, (300, 10), (500, 90), (0, 255, 0), cv2.FILLED)    # Yeşil
        cv2.rectangle(img, (550, 10), (750, 90), (255, 0, 0), cv2.FILLED)    # Mavi
        cv2.rectangle(img, (800, 10), (1000, 90), (0, 255, 255), cv2.FILLED) # Sarı
        cv2.rectangle(img, (1050, 10), (1230, 90), (50, 50, 50), cv2.FILLED) # Silgi
        cv2.putText(img, "SILGI", (1100, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        if len(lm_list) != 0:
            x1, y1 = lm_list[8][1:]   # İşaret parmağı
            x2, y2 = lm_list[12][1:]  # Orta parmak
            fingers = detector.fingers_up()

            # Seçim Modu: İki parmak yukarıda
            if fingers[1] and fingers[2]:
                xp, yp = 0, 0
                if y1 < 90:
                    if 50 < x1 < 250:
                        draw_color = (0, 0, 255)
                    elif 300 < x1 < 500:
                        draw_color = (0, 255, 0)
                    elif 550 < x1 < 750:
                        draw_color = (255, 0, 0)
                    elif 800 < x1 < 1000:
                        draw_color = (0, 255, 255)
                    elif 1050 < x1 < 1230:
                        draw_color = (0, 0, 0) # Silgi
                cv2.circle(img, (x1, y1), 15, draw_color, cv2.FILLED)

            # Çizim Modu: Sadece işaret parmağı yukarıda
            elif fingers[1] and not fingers[2]:
                if xp == 0 and yp == 0:
                    xp, yp = x1, y1

                thickness = eraser_thickness if draw_color == (0, 0, 0) else brush_thickness

                cv2.line(img, (xp, yp), (x1, y1), draw_color, thickness)
                cv2.line(img_canvas, (xp, yp), (x1, y1), draw_color, thickness)
                xp, yp = x1, y1
            else:
                xp, yp = 0, 0

        # Çizim tuvali ile kamera görüntüsünü harmanlama
        img_gray = cv2.cvtColor(img_canvas, cv2.COLOR_BGR2GRAY)
        _, img_inv = cv2.threshold(img_gray, 50, 255, cv2.THRESH_BINARY_INV)
        img_inv = cv2.cvtColor(img_inv, cv2.COLOR_GRAY2BGR)
        img = cv2.bitwise_and(img, img_inv)
        img = cv2.bitwise_or(img, img_canvas)

        cv2.putText(img, "Mod: Air Canvas (Cikis: Q)", (10, 710), cv2.FONT_HERSHEY_PLAIN, 1.5, (255, 255, 255), 2)
        cv2.imshow("VisionTouch - Air Canvas", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_air_canvas()
```

---

### 5.3 Modül 3 - Medya ve Ses Kontrolü (`modules/media_controller.py`)

- **Ses Seviyesi Ayarı:** Başparmak ucu (Landmark 4) ile İşaret parmağı ucu (Landmark 8) arasındaki Öklid mesafesi hesaplanır.
- **Doğrusal Eşleme:** 25 px - 160 px aralığı, %0 - %100 sistem ses seviyesine eşlenir (`np.interp`).
- **Windows Entegrasyonu:** `pycaw` kütüphanesi üzerinden doğrudan ana sistem ses aygıtı kontrol edilir.

```python
import cv2
import numpy as np
import pyautogui
from core.hand_detector import HandDetector

# Windows için PyCaw Ses Kontrolü (Fallback mekanizmalı)
try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    vol_range = volume.GetVolumeRange()
    min_vol, max_vol = vol_range[0], vol_range[1]
    HAS_PYCAW = True
except Exception:
    HAS_PYCAW = False

def run_media_controller():
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)

    detector = HandDetector(max_hands=1, detection_con=0.75)
    vol_bar = 400
    vol_per = 0

    while True:
        success, img = cap.read()
        if not success:
            break

        img = cv2.flip(img, 1)
        img = detector.find_hands(img)
        lm_list = detector.find_positions(img)

        if len(lm_list) != 0:
            # 4: Başparmak ucu, 8: İşaret parmağı ucu
            length, img, line_info = detector.find_distance(4, 8, img)

            # Mesafe: 25px - 160px arasını %0 - %100 skalasına eşleme
            vol_bar = np.interp(length, [25, 160], [400, 150])
            vol_per = np.interp(length, [25, 160], [0, 100])

            if HAS_PYCAW:
                system_vol = np.interp(length, [25, 160], [min_vol, max_vol])
                volume.SetMasterVolumeLevel(system_vol, None)

            if length < 25:
                cv2.circle(img, (line_info[4], line_info[5]), 8, (0, 255, 0), cv2.FILLED)

        # Arayüz: Ses Gösterge Çubuğu
        cv2.rectangle(img, (50, 150), (85, 400), (0, 255, 0), 3)
        cv2.rectangle(img, (50, int(vol_bar)), (85, 400), (0, 255, 0), cv2.FILLED)
        cv2.putText(img, f'{int(vol_per)} %', (40, 435), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 255, 0), 2)

        cv2.putText(img, "Mod: Medya Kontrol (Cikis: Q)", (10, 30), cv2.FONT_HERSHEY_PLAIN, 1.5, (255, 255, 0), 2)
        cv2.imshow("VisionTouch - Medya Kontrol", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_media_controller()
```

---

## 6. Ana Yönetici (`main.py`)

Kullanıcının terminal arayüzünden istediği modu seçmesini ve pencereler kapandığında ana menüye dönmesini sağlayan orkestrasyon dosyasıdır.

```python
import sys
from modules.virtual_mouse import run_virtual_mouse
from modules.air_canvas import run_air_canvas
from modules.media_controller import run_media_controller

def print_menu():
    print("=" * 45)
    print("      VISIONTOUCH - JEST KONTROL SUITI      ")
    print("=" * 45)
    print("1 -> Sanal Fare (Virtual Mouse)")
    print("2 -> Havada Cizim (Air Canvas)")
    print("3 -> Medya & Ses Kontrolu (Media Controller)")
    print("0 -> Cikis")
    print("=" * 45)

def main():
    while True:
        print_menu()
        choice = input("Calistirmak istediginiz modun numarasini girin: ").strip()

        if choice == '1':
            print("\n[BILGI] Sanal Fare baslatiliyor... (Kapatmak icin pencerede 'q' basin)")
            run_virtual_mouse()
        elif choice == '2':
            print("\n[BILGI] Air Canvas baslatiliyor... (Kapatmak icin pencerede 'q' basin)")
            run_air_canvas()
        elif choice == '3':
            print("\n[BILGI] Medya Kontrolu baslatiliyor... (Kapatmak icin pencerede 'q' basin)")
            run_media_controller()
        elif choice == '0':
            print("\nProgram kapatiliyor. Iyi calismalar!")
            sys.exit(0)
        else:
            print("\n[HATA] Gecersiz secim! Lutfen 0, 1, 2 veya 3 giriniz.\n")

if __name__ == "__main__":
    main()
```

---

## 7. Test ve Kalibrasyon İpuçları

1. **Aydınlatma ve Kontrast:** MediaPipe, elin arka plandan belirgin biçimde ayrıldığı dengeli aydınlatma koşullarında en iyi doğruluğu sunar. Güçlü arka ışık (örneğin pencere önünde oturmak) silüet etkisine ve eklem kaybına sebep olabilir.
2. **Kamera Aynalama (`cv2.flip`):** Doğal insan etkileşimi için sağ el kaldırıldığında ekranda da sağ tarafın tepki vermesi adına görüntüler `cv2.flip(img, 1)` ile yatayda aynalanmıştır.
3. **Titreme Önleme (Smooth Factor):** `smoothening` katsayısını artırmak (7–9) imleç kararlılığını artırır ancak gecikmeyi (latency) hafif artırabilir. İdeal değer donanım ve el hızına göre ayarlanmalıdır.
4. **PyAutoGUI Failsafe:** Köşelere hızlı çarpmalarda istisnaları önlemek için `pyautogui.FAILSAFE = False` tanımlanmıştır.
