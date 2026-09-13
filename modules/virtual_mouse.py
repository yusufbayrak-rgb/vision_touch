import cv2
import numpy as np
import pyautogui
import time
import math
from core.hand_detector import HandDetector

def run_virtual_mouse():
    w_cam, h_cam = 640, 480
    
    # 🎯 Ergonomik Çalışma Alanı
    frame_left = 110
    frame_right = 530
    frame_top = 60
    frame_bottom = 340
    
    smoothening = 3.2

    p_loc_x, p_loc_y = 0, 0
    c_loc_x, c_loc_y = 0, 0
    
    is_pressed = False
    last_click_time = 0

    cap = cv2.VideoCapture(0)
    cap.set(3, w_cam)
    cap.set(4, h_cam)

    detector = HandDetector(max_hands=1, detection_con=0.8, track_con=0.75)
    w_scr, h_scr = pyautogui.size()
    
    pyautogui.PAUSE = 0
    pyautogui.FAILSAFE = False

    print("[BILGI] Akilli Kalem Faresi baslatildi. Cikis icin 'q' basin.")

    while True:
        success, img = cap.read()
        if not success:
            break

        img = cv2.flip(img, 1)
        img = detector.find_hands(img, draw=True)
        lm_list = detector.find_positions(img)

        # Aktif Çalışma Alanı Çerçevesi
        cv2.rectangle(img, (frame_left, frame_top), (frame_right, frame_bottom), (0, 255, 255), 2)

        if len(lm_list) != 0:
            # 0: Bilek, 4: Başparmak ucu, 5: İşaret boğumu, 8: İşaret parmağı ucu
            x_wrist, y_wrist = lm_list[0][1:]
            x_thumb, y_thumb = lm_list[4][1:]
            x_knuckle, y_knuckle = lm_list[5][1:]
            x_index, y_index = lm_list[8][1:]

            # 1. REFERANS EL BOYUTU (Uzaklıktan etkilenmemek için)
            hand_size = math.hypot(x_knuckle - x_wrist, y_knuckle - y_wrist) + 1e-5

            # 2. İMLEÇ HAREKETİ: Kalemi tutan el/kalem noktası (İşaret parmağını kaldırırken imleç oynamaz)
            pen_x = int((x_thumb + x_knuckle) / 2)
            pen_y = int((y_thumb + y_knuckle) / 2)

            x3 = np.interp(pen_x, (frame_left, frame_right), (0, w_scr))
            y3 = np.interp(pen_y, (frame_top, frame_bottom), (0, h_scr))
            
            x3 = np.clip(x3, 0, w_scr - 1)
            y3 = np.clip(y3, 0, h_scr - 1)

            # Yumuşatma
            c_loc_x = p_loc_x + (x3 - p_loc_x) / smoothening
            c_loc_y = p_loc_y + (y3 - p_loc_y) / smoothening

            pyautogui.moveTo(c_loc_x, c_loc_y)
            p_loc_x, p_loc_y = c_loc_x, c_loc_y

            # 3. KALEME DOKUNMA ORANI (Normalize Mesafe)
            dist_finger = math.hypot(x_index - x_thumb, y_index - y_thumb)
            pinch_ratio = dist_finger / hand_size

            # Kalem ucu göstergesi (Cyan Nokta)
            cv2.circle(img, (pen_x, pen_y), 6, (255, 255, 0), cv2.FILLED)

            # TIKLAMA KONTROLÜ (İşaret parmağı kaleme değdiğinde: ratio < 0.24)
            if pinch_ratio < 0.24:
                cv2.circle(img, (x_index, y_index), 12, (0, 0, 255), cv2.FILLED)
                cv2.putText(img, "TIKLANDI!", (x_index - 30, y_index - 20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                if not is_pressed:
                    if (time.time() - last_click_time) < 0.35:
                        pyautogui.doubleClick()
                    else:
                        pyautogui.click()
                    
                    last_click_time = time.time()
                    is_pressed = True
            else:
                is_pressed = False
                cv2.circle(img, (x_index, y_index), 6, (0, 255, 0), cv2.FILLED)

            # Ekranda temas çubuğu / oranı bilgisi
            cv2.putText(img, f"Temas: {int(pinch_ratio * 100)}%", (10, 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if pinch_ratio >= 0.24 else (0, 0, 255), 2)

        # Bilgi Arayüzü
        cv2.putText(img, "Akilli Kalem Faresi (Kalemi Tut: Gezdir | Isaret Parmagini Kaleme Bas: Tik)", 
                    (10, 30), cv2.FONT_HERSHEY_PLAIN, 1.1, (255, 255, 255), 1)
        
        cv2.imshow("VisionTouch - Akilli Kalem Faresi", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_virtual_mouse()
