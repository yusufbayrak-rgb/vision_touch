import sys
import os
from modules.virtual_mouse import run_virtual_mouse
from modules.air_canvas import run_air_canvas
from modules.media_controller import run_media_controller
from modules.eye_mouse import run_eye_mouse

def print_banner():
    """Konsol baslik arayuzu."""
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=" * 55)
    print("      VISIONTOUCH - YAPAY ZEKA JEST KONTROL SUITI    ")
    print("             IEEE CIS Komitesi 2026                 ")
    print("=" * 55)
    print(" [1] -> Sanal Fare (Virtual Mouse)")
    print("        (Isaret parmagi: Hareket | 2 Parmak: Sol Tik)")
    print()
    print(" [2] -> Havada Cizim (Air Canvas)")
    print("        (Isaret parmagi: Cizim | 2 Parmak: Renk Secimi)")
    print()
    print(" [3] -> Medya & Ses Kontrolu (Media Controller)")
    print("        (Basparmak - Isaret: Ses | Serce Parmak: Kilit)")
    print()
    print(" [4] -> Gozle Fare Kontrolu (Eye-Tracking Mouse)")
    print("        (Goz Bebegi: Imlec | Goz Kirpma: Sol Tik)")
    print()
    print(" [0] -> Programdan Cikis")
    print("=" * 55)

def main():
    while True:
        try:
            print_banner()
            choice = input("\nCalistirmak istediginiz modun numarasini girin (0-4): ").strip()

            if choice == '1':
                print("\n[BILGI] Sanal Fare baslatiliyor...")
                run_virtual_mouse()
            elif choice == '2':
                print("\n[BILGI] Air Canvas baslatiliyor...")
                run_air_canvas()
            elif choice == '3':
                print("\n[BILGI] Medya & Ses Kontrolu baslatiliyor...")
                run_media_controller()
            elif choice == '4':
                print("\n[BILGI] Gozle Fare Kontrolu baslatiliyor...")
                run_eye_mouse()
            elif choice == '0':
                print("\nVisionTouch sonlandirildi. Iyi calismalar!")
                sys.exit(0)
            else:
                input("\n[HATA] Gecersiz secim! Lutfen 0, 1, 2, 3 veya 4 giriniz. Devam etmek icin Enter'a basin...")

        except KeyboardInterrupt:
            print("\n\n[BILGI] Program kullanici tarafindan durduruldu.")
            sys.exit(0)
        except Exception as e:
            print(f"\n[BEKLENMEYEN HATA]: {e}")
            input("Devam etmek icin Enter'a basin...")

if __name__ == "__main__":
    main()
