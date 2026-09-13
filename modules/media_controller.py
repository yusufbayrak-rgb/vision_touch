import cv2
import numpy as np
import pyautogui
from core.hand_detector import HandDetector

class SystemVolumeManager:
    """Windows ses seviyesini yoneten gelismis yonetici sinifi."""
    def __init__(self):
        self.has_pycaw = False
        self.volume = None
        self.last_percent = 50

        try:
            import comtypes
            comtypes.CoInitialize()
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            devices = AudioUtilities.GetSpeakers()
            if hasattr(devices, 'EndpointVolume'):
                self.volume = devices.EndpointVolume
            else:
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                self.volume = cast(interface, POINTER(IAudioEndpointVolume))

            self.has_pycaw = True
            print("[BILGI] Windows ses aygitina (PyCaw) basariyla baglanildi.")
        except Exception as e:
            print(f"[BILGI] Donanim ses baglantisi saglanamadi, klavye ses motoru aktif: {e}")

    def set_volume(self, percent):
        """Sesi %0 ile %100 arasinda ayarlar."""
        percent = int(max(0, min(100, percent)))

        # 1. PyCaw Dogrudan Donanim Seviyesi
        if self.has_pycaw and self.volume is not None:
            try:
                self.volume.SetMasterVolumeLevelScalar(percent / 100.0, None)
                return
            except Exception:
                pass

        # 2. Klavye Medya Tuslari Fallback
        diff = percent - self.last_percent
        if abs(diff) >= 4:
            steps = int(abs(diff) / 2)
            key = 'volumeup' if diff > 0 else 'volumedown'
            for _ in range(steps):
                pyautogui.press(key)
            self.last_percent = percent


def run_media_controller():
    """
    Medya ve Ses Kontrol Modulunu baslatir.
    - Basparmak + Isaret: Ses Seviyesi Ayarlama
    - Serce Parmak Acik veya Yumruk: SES KILIDI (Degismez)
    - 'q' tusu: Moddan cikis
    """
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)

    detector = HandDetector(max_hands=1, detection_con=0.75)
    vol_manager = SystemVolumeManager()
    
    vol_bar = 400
    vol_per = 50
    is_locked = False

    print("[BILGI] Medya & Ses Kontrolu calisiyor. Cikmak icin pencerede 'q' tusuna basin.")

    while True:
        success, img = cap.read()
        if not success:
            print("[HATA] Kamera goruntusu alinamadi!")
            break

        img = cv2.flip(img, 1)  # Aynalama
        img = detector.find_hands(img)
        lm_list = detector.find_positions(img)

        status_text = "El Bekleniyor"
        status_color = (200, 200, 200)

        if len(lm_list) != 0:
            fingers = detector.fingers_up()

            # Serce Parmak Aciksa (fingers[4] == 1) veya Yumruk ise (sum == 0) -> KILITLE
            if (len(fingers) >= 5 and fingers[4] == 1) or sum(fingers) == 0:
                is_locked = True
                status_text = "🔒 SES KILITLI (Serce Parmak Acik)"
                status_color = (0, 0, 255)  # Kirmizi
            else:
                # Ayar Modu (Sadece basparmak ve isaret parmagi araligi)
                is_locked = False
                status_text = "🔊 SES AYARLANIYOR"
                status_color = (0, 255, 0)  # Yesil

                length, img, line_info = detector.find_distance(4, 8, img)

                # Mesafe araligini (25px - 160px) ses skalasina (%0 - %100) esleme
                vol_bar = np.interp(length, [25, 160], [400, 150])
                vol_per = np.interp(length, [25, 160], [0, 100])

                # Sesi Windows'a uygula
                vol_manager.set_volume(vol_per)

                if length < 25:
                    cv2.circle(img, (line_info[4], line_info[5]), 9, (0, 255, 0), cv2.FILLED)

        # ------------------- ARAYUZ CIZIMLERI -------------------
        # Ses Barı
        cv2.rectangle(img, (50, 150), (85, 400), (0, 255, 0), 3)
        cv2.rectangle(img, (50, int(vol_bar)), (85, 400), (0, 255, 0), cv2.FILLED)
        cv2.putText(img, f'{int(vol_per)} %', (40, 440), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 255, 0), 2)

        # Durum Bilgisi (Kilitli / Ayarlanıyor)
        cv2.putText(img, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        cv2.putText(img, "Kitlemek: Serce Parmagi Kaldirin | Cikis: Q", (10, 470), 
                    cv2.FONT_HERSHEY_PLAIN, 1.1, (255, 255, 255), 1)

        cv2.imshow("VisionTouch - Medya Kontrol", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_media_controller()
