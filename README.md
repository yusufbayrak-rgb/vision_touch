# VisionTouch: Yapay Zeka Tabanlı Jest Kontrol Süiti
## IEEE CIS Komitesi 2026

Bu proje; **el takibi (Hand Tracking)**, **sanal fare (Virtual Mouse)**, **havada çizim (Air Canvas)**, **medya kontrolü (Media Controller)** ve **göz takibi fare (Eye-Tracking Mouse)** modüllerini tek bir Python mimarisi altında birleştiren jest kontrol süitidir.

---

## 🚀 Hızlı Başlatma

### Windows - Tek Tıkla Çalıştırma

**`baslat.bat`** dosyasına çift tıklayın. Başlatıcı otomatik olarak:
1. Sistemdeki Python kurulumlarını algılar (birden fazla varsa seçtirir)
2. Sanal ortamı (venv) oluşturur veya mevcut olanı aktive eder
3. Eksik bağımlılıkları otomatik yükler
4. Programı başlatır

> **Not:** İlk çalıştırmada bağımlılık yüklemesi birkaç dakika sürebilir.

### Manuel Kurulum

```bash
# 1. Proje dizinine giriş
cd VisionTouch

# 2. Sanal ortam oluşturma
python -m venv venv

# 3. Sanal ortamı etkinleştirme
# Windows (CMD):
venv\Scripts\activate
# Windows (PowerShell):
venv\Scripts\Activate.ps1
# macOS / Linux:
source venv/bin/activate

# 4. Bağımlılıkları yükleme
pip install -r requirements.txt

# 5. Programı çalıştırma
python main.py
```

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
   - [Modül 4: Göz Takibi Fare (Eye-Tracking Mouse)](#54-modül-4---göz-takibi-fare-moduleseye_mousepy)
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
│   ├── media_controller.py      # Ses seviyesi ve medya kontrolleri
│   └── eye_mouse.py             # Göz takibi ile fare kontrolü ve göz kırpma tıklama
│
├── main.py                      # Modlar arası konsol tabanlı geçiş sağlayan ana yönetici
├── baslat.bat                   # Windows için otomatik kurulum ve başlatma betiği
├── requirements.txt             # Gerekli Python bağımlılıkları
└── README.md                    # Mimari ve kullanım dokümantasyonu
```

---

## 2. Ortam Kurulumu ve Bağımlılıklar

> **Tavsiye:** Python 3.10 veya 3.11 sürümü önerilir.

> **⚠️ Önemli:** `mediapipe==0.10.14` sürümü kullanılmalıdır. Daha yeni sürümlerde (0.10.30+, 1.0.x) `mp.solutions` API'si kaldırılmıştır ve proje çalışmaz.

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
mediapipe==0.10.14
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

### Sınıf: `HandDetector`

| Metot | Açıklama |
|-------|----------|
| `__init__(mode, max_hands, detection_con, track_con)` | MediaPipe Hands modelini başlatır |
| `find_hands(img, draw)` | Kamera görüntüsünde elleri arar ve eklemleri çizer |
| `find_positions(img, hand_no)` | 21 eklem noktasının piksel (x, y) koordinatlarını döndürür |
| `fingers_up()` | Hangi parmakların açık olduğunu belirler → `[Baş, İşaret, Orta, Yüzük, Serçe]` |
| `find_distance(p1, p2, img, draw)` | İki eklem noktası arasındaki Öklid mesafesini hesaplar |

---

## 5. Modüller

### 5.1 Modül 1 - Sanal Fare (`modules/virtual_mouse.py`)

**Akıllı Kalem Faresi** — El pozisyonunu kalem tutar gibi kullanarak fare kontrolü sağlar.

| Özellik | Kontrol |
|---------|---------|
| **İmleç Hareketi** | Başparmak + işaret parmağı boğumu orta noktası (kalem ucu) |
| **Sol Tıklama** | İşaret parmağını başparmağa değdirme (pinch ratio < 0.24) |
| **Çift Tıklama** | 0.35 saniye içinde iki kez temas |

**Teknik Detaylar:**
- Ergonomik çalışma alanı çerçevesi (110-530 x 60-340 px)
- El boyutu normalize mesafe hesaplaması (uzaklıktan bağımsız)
- Yumuşatma katsayısı: 3.2

---

### 5.2 Modül 2 - Havada Çizim (`modules/air_canvas.py`)

| Özellik | Kontrol |
|---------|---------|
| **Çizim Modu** | Sadece işaret parmağı açık |
| **Renk Seçim Modu** | İşaret ve orta parmak birlikte açık |
| **Tuvali Temizleme** | Tüm parmaklar açık |

**Renk Paleti:** Kırmızı, Yeşil, Mavi, Sarı, Silgi

**Teknik Detaylar:**
- 1280x720 çözünürlük
- `cv2.bitwise_and` / `cv2.bitwise_or` ile şeffaf tuval birleştirme

---

### 5.3 Modül 3 - Medya ve Ses Kontrolü (`modules/media_controller.py`)

| Özellik | Kontrol |
|---------|---------|
| **Ses Ayarlama** | Başparmak + İşaret parmağı mesafesi |
| **Ses Kilidi** | Serçe parmak açık veya yumruk |

**Teknik Detaylar:**
- PyCaw ile doğrudan Windows ses aygıtı kontrolü
- Fallback: Klavye medya tuşları
- Mesafe eşlemesi: 25px - 160px → %0 - %100

---

### 5.4 Modül 4 - Göz Takibi Fare (`modules/eye_mouse.py`)

MediaPipe FaceMesh kullanarak göz bebeği pozisyonu ile fare kontrolü ve göz kırpma ile tıklama sağlar.

| Özellik | Kontrol |
|---------|---------|
| **İmleç Hareketi** | Kaş ortası (glabella) pozisyonu |
| **Sol Tıklama** | Tek göz kırpma |
| **Çift Tıklama** | 0.55 saniye içinde iki hızlı kırpma |

**Teknik Detaylar:**
- Ultra dar ergonomik alan (x: 0.465-0.535, y: 0.410-0.465)
- CursorStabilizer sınıfı: deadzone (7px) + adaptif alpha yumuşatma
- 3 karelik ham gürültü temizleme (ortalama)
- EAR (Eye Aspect Ratio) < 0.17 → göz kırpma algılama

---

## 6. Ana Yönetici (`main.py`)

Kullanıcının terminal arayüzünden istediği modu seçmesini ve pencereler kapandığında ana menüye dönmesini sağlayan orkestrasyon dosyasıdır.

**Mevcut Modlar:**

| Tuş | Modül | Açıklama |
|-----|-------|----------|
| `1` | Sanal Fare | El ile imleç hareketi ve tıklama |
| `2` | Air Canvas | Havada çizim ve renk seçimi |
| `3` | Medya Kontrol | Ses seviyesi ayarı |
| `4` | Göz Takibi Fare | Göz bebeği ile imleç, kırpma ile tıklama |
| `0` | Çıkış | Programı sonlandırır |

---

## 7. Test ve Kalibrasyon İpuçları

1. **Aydınlatma ve Kontrast:** MediaPipe, elin arka plandan belirgin biçimde ayrıldığı dengeli aydınlatma koşullarında en iyi doğruluğu sunar. Güçlü arka ışık (örneğin pencere önünde oturmak) silüet etkisine ve eklem kaybına sebep olabilir.
2. **Kamera Aynalama (`cv2.flip`):** Doğal insan etkileşimi için sağ el kaldırıldığında ekranda da sağ tarafın tepki vermesi adına görüntüler `cv2.flip(img, 1)` ile yatayda aynalanmıştır.
3. **Titreme Önleme (Smooth Factor):** `smoothening` katsayısını artırmak (7–9) imleç kararlılığını artırır ancak gecikmeyi (latency) hafif artırabilir. İdeal değer donanım ve el hızına göre ayarlanmalıdır.
4. **PyAutoGUI Failsafe:** Köşelere hızlı çarpmalarda istisnaları önlemek için `pyautogui.FAILSAFE = False` tanımlanmıştır.
5. **MediaPipe Sürümü:** `mediapipe==0.10.14` kullanılmalıdır. Daha yeni sürümlerde `mp.solutions` API'si kaldırılmıştır.
