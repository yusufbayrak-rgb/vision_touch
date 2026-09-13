import cv2
import numpy as np
from core.hand_detector import HandDetector

def run_air_canvas():
    cap = cv2.VideoCapture(0)
    # Kamera cozunurlugunu garantiye al
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    detector = HandDetector(max_hands=1, detection_con=0.85, track_con=0.7)
    
    draw_color = (0, 0, 255) # Kirmizi
    brush_thickness = 10
    eraser_thickness = 60

    xp, yp = 0, 0
    img_canvas = None

    print("[BILGI] Air Canvas calisiyor. Cikmak icin pencerede 'q' tusuna basin.")

    while True:
        success, img = cap.read()
        if not success:
            break

        img = cv2.flip(img, 1)
        h, w, _ = img.shape

        if img_canvas is None:
            img_canvas = np.zeros((h, w, 3), np.uint8)

        img = detector.find_hands(img, draw=False)
        lm_list = detector.find_positions(img)

        # ------------------- UST MENU BUTONLARI -------------------
        btn_w = w // 5
        # Kirmizi
        cv2.rectangle(img, (10, 10), (btn_w - 10, 80), (0, 0, 255), cv2.FILLED)
        cv2.putText(img, "KIRMIZI", (btn_w//2 - 50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        # Yesil
        cv2.rectangle(img, (btn_w + 10, 10), (2*btn_w - 10, 80), (0, 255, 0), cv2.FILLED)
        cv2.putText(img, "YESIL", (btn_w + btn_w//2 - 40, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        # Mavi
        cv2.rectangle(img, (2*btn_w + 10, 10), (3*btn_w - 10, 80), (255, 0, 0), cv2.FILLED)
        cv2.putText(img, "MAVI", (2*btn_w + btn_w//2 - 35, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        # Sari
        cv2.rectangle(img, (3*btn_w + 10, 10), (4*btn_w - 10, 80), (0, 255, 255), cv2.FILLED)
        cv2.putText(img, "SARI", (3*btn_w + btn_w//2 - 35, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        # Silgi
        cv2.rectangle(img, (4*btn_w + 10, 10), (w - 10, 80), (60, 60, 60), cv2.FILLED)
        cv2.putText(img, "SILGI", (4*btn_w + btn_w//2 - 35, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        if len(lm_list) != 0:
            x1, y1 = lm_list[8][1:]   # Isaret parmagi
            fingers = detector.fingers_up()

            # A) SECIM MODU: Isaret ve Orta Parmak Birlikte Acik (veya El Acik)
            if len(fingers) >= 3 and fingers[1] == 1 and fingers[2] == 1:
                xp, yp = 0, 0
                cv2.circle(img, (x1, y1), 15, draw_color, cv2.FILLED)

                # Buton secimi
                if y1 < 90:
                    if 10 < x1 < btn_w - 10:
                        draw_color = (0, 0, 255)
                    elif btn_w + 10 < x1 < 2*btn_w - 10:
                        draw_color = (0, 255, 0)
                    elif 2*btn_w + 10 < x1 < 3*btn_w - 10:
                        draw_color = (255, 0, 0)
                    elif 3*btn_w + 10 < x1 < 4*btn_w - 10:
                        draw_color = (0, 255, 255)
                    elif 4*btn_w + 10 < x1 < w - 10:
                        draw_color = (0, 0, 0) # Silgi

            # B) CIZIM MODU: SADECE Isaret Parmagi Acik
            elif len(fingers) >= 3 and fingers[1] == 1 and fingers[2] == 0:
                cv2.circle(img, (x1, y1), 8, draw_color, cv2.FILLED)

                if xp == 0 and yp == 0:
                    xp, yp = x1, y1

                thick = eraser_thickness if draw_color == (0, 0, 0) else brush_thickness
                cv2.line(img, (xp, yp), (x1, y1), draw_color, thick)
                cv2.line(img_canvas, (xp, yp), (x1, y1), draw_color, thick)

                xp, yp = x1, y1

            # C) TUVALI TEMIZLEME: Yumruk yapilirsa veya butun parmaklar aciksa
            elif all(fingers):
                img_canvas = np.zeros((h, w, 3), np.uint8)
                xp, yp = 0, 0
            else:
                xp, yp = 0, 0
        else:
            xp, yp = 0, 0

        # Tuvali Canli Goruntuyle Birlestirme
        img_gray = cv2.cvtColor(img_canvas, cv2.COLOR_BGR2GRAY)
        _, img_inv = cv2.threshold(img_gray, 20, 255, cv2.THRESH_BINARY_INV)
        img_inv = cv2.cvtColor(img_inv, cv2.COLOR_GRAY2BGR)
        img = cv2.bitwise_and(img, img_inv)
        img = cv2.bitwise_or(img, img_canvas)

        cv2.putText(img, "Air Canvas (1 Parmak: Ciz | 2 Parmak: Renk Sec | Tum Parmaklar: Temizle)", 
                    (20, h - 20), cv2.FONT_HERSHEY_PLAIN, 1.2, (255, 255, 255), 2)
        
        cv2.imshow("VisionTouch - Air Canvas", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_air_canvas()
