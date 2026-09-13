import cv2
import mediapipe as mp
import math

class HandDetector:
    def __init__(self, mode=False, max_hands=1, detection_con=0.7, track_con=0.5):
        """
        MediaPipe el tespit modelini ilklendirir.
        :param mode: Statik goruntu modu (False: video akisi icin optimize)
        :param max_hands: Takip edilecek maksimum el sayisi
        :param detection_con: Ilk el tespit esik guveni (0.0 - 1.0)
        :param track_con: Eklemleri takip etme esik guveni (0.0 - 1.0)
        """
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
        self.tip_ids = [4, 8, 12, 16, 20]  # Bas, Isaret, Orta, Yuzuk, Serce uclari
        self.lm_list = []
        self.results = None

    def find_hands(self, img, draw=True):
        """
        Kamera goruntusunde elleri arar ve eklemleri cizer.
        """
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)

        if self.results.multi_hand_landmarks:
            for hand_lms in self.results.multi_hand_landmarks:
                if draw:
                    self.mp_draw.draw_landmarks(img, hand_lms, self.mp_hands.HAND_CONNECTIONS)
        return img

    def find_positions(self, img, hand_no=0):
        """
        21 adet eklem noktasinin piksel (x, y) koordinatlarini dondurur.
        Format: [[id, x, y], [id, x, y], ...]
        """
        self.lm_list = []
        if self.results and self.results.multi_hand_landmarks:
            if len(self.results.multi_hand_landmarks) > hand_no:
                my_hand = self.results.multi_hand_landmarks[hand_no]
                h, w, _ = img.shape
                for id, lm in enumerate(my_hand.landmark):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    self.lm_list.append([id, cx, cy])
        return self.lm_list

    def fingers_up(self):
        """
        Hangi parmaklarin havada (acik) oldugunu belirler.
        Dondurur: [Bas, Isaret, Orta, Yuzuk, Serce] -> ornek: [0, 1, 0, 0, 0]
        """
        fingers = []
        if len(self.lm_list) == 0:
            return fingers

        # 1. Basparmak (X ekseni kontrolu: el ayasinin konumuna gore)
        if self.lm_list[self.tip_ids[0]][1] > self.lm_list[self.tip_ids[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)

        # 2. Diger 4 Parmak (Y ekseni kontrolu: Parmak ucu, bir alt bogumdan yukarida mi?)
        for id in range(1, 5):
            if self.lm_list[self.tip_ids[id]][2] < self.lm_list[self.tip_ids[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
        return fingers

    def find_distance(self, p1, p2, img=None, draw=True):
        """
        Iki eklem noktasi (p1, p2) arasindaki Oklid mesafesini hesaplar.
        """
        if len(self.lm_list) <= max(p1, p2):
            return 0, img, [0, 0, 0, 0, 0, 0]

        x1, y1 = self.lm_list[p1][1], self.lm_list[p1][2]
        x2, y2 = self.lm_list[p2][1], self.lm_list[p2][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        length = math.hypot(x2 - x1, y2 - y1)

        if draw and img is not None:
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 2)
            cv2.circle(img, (x1, y1), 6, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 6, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (cx, cy), 6, (0, 0, 255), cv2.FILLED)

        return length, img, [x1, y1, x2, y2, cx, cy]
