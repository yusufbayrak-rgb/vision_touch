import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
import math
from collections import deque

class CursorStabilizer:
    """AR/VR tipi titreme engelleyici ve hedef sabitleyici."""
    def __init__(self, deadzone=7.0):
        self.x = None
        self.y = None
        self.deadzone = deadzone

    def update(self, target_x, target_y):
        if self.x is None:
            self.x, self.y = target_x, target_y
            return int(self.x), int(self.y)

        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)

        # 🎯 KAYA GİBİ SABİT: Titreme eşiği altındaysa imleci asla oynatma
        if dist < self.deadzone:
            return int(self.x), int(self.y)

        # Hızlıyken anında takip (alpha=0.38), yavaşlarken ultra pürüzsüz (alpha=0.08)
        alpha = np.interp(dist, [self.deadzone, 50.0], [0.08, 0.38])
        self.x += dx * alpha
        self.y += dy * alpha
        return int(self.x), int(self.y)

def run_eye_mouse():
    w_cam, h_cam = 640, 480
    cap = cv2.VideoCapture(0)
    cap.set(3, w_cam)
    cap.set(4, h_cam)

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.75,
        min_tracking_confidence=0.75
    )

    w_scr, h_scr = pyautogui.size()
    pyautogui.PAUSE = 0
    pyautogui.FAILSAFE = False

    # 🎯 ULTRA DAR ERGONOMİK ALAN
    forehead_min_x, forehead_max_x = 0.465, 0.535
    forehead_min_y, forehead_max_y = 0.410, 0.465

    stabilizer = CursorStabilizer(deadzone=7.0)
    raw_buffer_x = deque(maxlen=3)
    raw_buffer_y = deque(maxlen=3)

    is_blinking = False
    last_click_time = 0

    print("[BILGI] Titresimsiz Cift Tiklamali Kas Faresi baslatildi. Cikis icin 'q' basin.")

    while True:
        success, img = cap.read()
        if not success:
            break

        img = cv2.flip(img, 1)
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_img)

        h, w, _ = img.shape

        # Mikro Kontrol Kutusu (Cyan)
        cv2.rectangle(img, 
                      (int(forehead_min_x * w), int(forehead_min_y * h)), 
                      (int(forehead_max_x * w), int(forehead_max_y * h)), 
                      (255, 255, 0), 2)
        cv2.putText(img, "Mikro Kontrol", (int(forehead_min_x * w), int(forehead_min_y * h) - 8), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark

            # 1. HAM KAMERA GÜRÜLTÜSÜNÜ TEMİZLEME (3 Karelik Ortalama)
            glabella = landmarks[168]
            raw_buffer_x.append(glabella.x)
            raw_buffer_y.append(glabella.y)

            smooth_gx = sum(raw_buffer_x) / len(raw_buffer_x)
            smooth_gy = sum(raw_buffer_y) / len(raw_buffer_y)

            # Ekran koordinatına eşleme
            x3 = np.interp(smooth_gx, (forehead_min_x, forehead_max_x), (0, w_scr))
            y3 = np.interp(smooth_gy, (forehead_min_y, forehead_max_y), (0, h_scr))
            x3 = np.clip(x3, 0, w_scr - 1)
            y3 = np.clip(y3, 0, h_scr - 1)

            # 2. GÖZ KIRPMA (Sol Göz) - TIKLAMA HESAPLAMA
            top_lid = landmarks[159]
            bottom_lid = landmarks[145]
            eye_left = landmarks[33]
            eye_right = landmarks[133]

            eye_h = abs(top_lid.y - bottom_lid.y)
            eye_w = abs(eye_left.x - eye_right.x) + 1e-5
            ear = eye_h / eye_w

            # GÖZ KIRPMA VE ÇİFT TIKLAMA
            if ear < 0.17:
                cv2.circle(img, (int(top_lid.x * w), int(top_lid.y * h)), 10, (0, 0, 255), cv2.FILLED)
                now = time.time()
                if not is_blinking and (now - last_click_time) > 0.15:
                    if (now - last_click_time) < 0.55:
                        cv2.putText(img, "CIFT TIKLANDI! (ACILDI)", (int(w/2 - 140), int(h/2)), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                        pyautogui.doubleClick()
                    else:
                        cv2.putText(img, "TIKLANDI!", (int(w/2 - 60), int(h/2)), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 0), 2)
                        pyautogui.click()

                    last_click_time = now
                    is_blinking = True
            else:
                is_blinking = False

                # 3. İMLEÇ HAREKETİ (Kaya gibi sabit Stabilizer)
                final_x, final_y = stabilizer.update(x3, y3)
                pyautogui.moveTo(final_x, final_y)

            # Kaş ortasına takip noktası
            g_px = int(smooth_gx * w)
            g_py = int(smooth_gy * h)
            cv2.circle(img, (g_px, g_py), 5, (0, 255, 0), cv2.FILLED)

        # Bilgi Arayüzü
        cv2.putText(img, "Stabil Kas Faresi (1 Kirpma: Sec | 2 Hizli Kirpma: Klasor Ac | Q: Cikis)", 
                    (10, 30), cv2.FONT_HERSHEY_PLAIN, 1.1, (255, 255, 255), 1)
        
        cv2.imshow("VisionTouch - Titresimsiz Kas Faresi", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_eye_mouse()
