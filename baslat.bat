@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title VisionTouch - Jest Kontrol Suiti
cd /d "%~dp0"

echo =========================================================
echo       VISIONTOUCH - KURULUM VE BASLATMA SISTEMI
echo =========================================================
echo.

:: ============================================================
:: 1) Python Kontrolu
:: ============================================================
echo [BILGI] Python araniyor...
echo.

set PYTHON_COUNT=0

:: --- python komutu ---
python --version >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%V in ('python --version 2^>^&1') do (
        for /f "tokens=*" %%L in ('python -c "import sys; print(sys.executable)" 2^>^&1') do (
            set /a PYTHON_COUNT+=1
            set "PYTHON_!PYTHON_COUNT!_CMD=python"
            set "PYTHON_!PYTHON_COUNT!_VER=%%V"
            set "PYTHON_!PYTHON_COUNT!_LOC=%%L"
        )
    )
)

:: --- py launcher ---
py --version >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%V in ('py --version 2^>^&1') do (
        for /f "tokens=*" %%L in ('py -c "import sys; print(sys.executable)" 2^>^&1') do (
            set "PY_LOC=%%L"
            set "IS_DUPLICATE=0"
            for /l %%I in (1,1,!PYTHON_COUNT!) do (
                if "!PYTHON_%%I_LOC!"=="!PY_LOC!" set "IS_DUPLICATE=1"
            )
            if "!IS_DUPLICATE!"=="0" (
                set /a PYTHON_COUNT+=1
                set "PYTHON_!PYTHON_COUNT!_CMD=py"
                set "PYTHON_!PYTHON_COUNT!_VER=%%V"
                set "PYTHON_!PYTHON_COUNT!_LOC=%%L"
            )
        )
    )
)

:: --- python3 komutu ---
python3 --version >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%V in ('python3 --version 2^>^&1') do (
        for /f "tokens=*" %%L in ('python3 -c "import sys; print(sys.executable)" 2^>^&1') do (
            set "PY3_LOC=%%L"
            set "IS_DUPLICATE=0"
            for /l %%I in (1,1,!PYTHON_COUNT!) do (
                if "!PYTHON_%%I_LOC!"=="!PY3_LOC!" set "IS_DUPLICATE=1"
            )
            if "!IS_DUPLICATE!"=="0" (
                set /a PYTHON_COUNT+=1
                set "PYTHON_!PYTHON_COUNT!_CMD=python3"
                set "PYTHON_!PYTHON_COUNT!_VER=%%V"
                set "PYTHON_!PYTHON_COUNT!_LOC=%%L"
            )
        )
    )
)

if !PYTHON_COUNT!==0 (
    echo [HATA] Sistemde Python bulunamadi!
    echo.
    echo   Python'u asagidaki adresten indirip kurun:
    echo   https://www.python.org/downloads/
    echo.
    echo   Kurulumda "Add Python to PATH" secenegini isaretleyin!
    echo.
    pause
    exit /b 1
)

:: ============================================================
:: 2) Python Secimi
:: ============================================================
if !PYTHON_COUNT!==1 (
    echo [BILGI] Bulunan Python: !PYTHON_1_VER!
    echo         Konum: !PYTHON_1_LOC!
    set "SELECTED_PYTHON=!PYTHON_1_CMD!"
    echo.
)

if !PYTHON_COUNT! gtr 1 (
    echo [BILGI] Birden fazla Python kurulumu bulundu:
    echo.
    for /l %%I in (1,1,!PYTHON_COUNT!) do (
        echo   [%%I] !PYTHON_%%I_VER!  -  !PYTHON_%%I_LOC!
    )
    echo.
    set /p PYTHON_CHOICE="Kullanmak istediginiz Python numarasini secin (1-!PYTHON_COUNT!): "

    if "!PYTHON_CHOICE!"=="" set PYTHON_CHOICE=1

    set "VALID_CHOICE="
    for /l %%I in (1,1,!PYTHON_COUNT!) do (
        if "!PYTHON_CHOICE!"=="%%I" set "VALID_CHOICE=1"
    )
    if not defined VALID_CHOICE (
        echo [UYARI] Gecersiz secim! Varsayilan olarak 1 secildi.
        set PYTHON_CHOICE=1
    )

    set "SELECTED_PYTHON=!PYTHON_%PYTHON_CHOICE%_CMD!"
    echo [BILGI] Secilen: !PYTHON_%PYTHON_CHOICE%_VER!
    echo.
)

:: Secimi dosyaya yaz, sonra endlocal yap - boylece activate.bat ile cakisma olmaz
set "SELECTED_PY=!SELECTED_PYTHON!"
endlocal & set "SELECTED_PYTHON=%SELECTED_PY%"

:: ============================================================
:: 3) Sanal Ortam (venv) Kontrolu ve Kurulumu
::    NOT: Buradan sonra goto/label KULLANILMIYOR
::         activate.bat kendi setlocal/endlocal yapar
::         bu yuzden goto ile label bulunamaz hatasini onluyoruz
:: ============================================================
set "NEED_INSTALL=0"

if exist "venv\Scripts\activate.bat" (
    echo [BILGI] Mevcut sanal ortam bulundu, aktive ediliyor...
    call venv\Scripts\activate.bat
    echo [OK] Sanal ortam aktif.
    echo.
) else (
    echo [BILGI] Sanal ortam bulunamadi, olusturuluyor...
    %SELECTED_PYTHON% -m venv venv
    if errorlevel 1 (
        echo [HATA] Sanal ortam olusturulamadi!
        echo        Python'un venv modulu yuklu oldugundan emin olun.
        pause
        exit /b 1
    )
    call venv\Scripts\activate.bat
    echo [OK] Sanal ortam olusturuldu ve aktive edildi.
    echo.
    set "NEED_INSTALL=1"
)

:: ============================================================
:: 4) Bagimliliklari Kontrol Et ve Kur
:: ============================================================
echo [BILGI] Bagimliliklar kontrol ediliyor...

if "%NEED_INSTALL%"=="0" (
    python -c "import cv2, mediapipe, numpy, pyautogui" >nul 2>&1
    if errorlevel 1 set "NEED_INSTALL=1"
)

if "%NEED_INSTALL%"=="1" (
    echo [BILGI] Eksik paketler tespit edildi, yukleniyor...
    echo         Bu islem ilk seferde biraz zaman alabilir...
    echo.
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [HATA] Paket yukleme basarisiz oldu!
        echo        Internet baglantinizi kontrol edin.
        pause
        exit /b 1
    )
    echo.
    echo [OK] Tum bagimliliklar basariyla yuklendi.
) else (
    echo [OK] Tum bagimliliklar mevcut.
)
echo.

:: ============================================================
:: 5) Programi Baslat
:: ============================================================
echo =========================================================
echo        VISIONTOUCH BASLATILIYOR...
echo =========================================================
echo.
python main.py
echo.
echo =========================================================
echo        VISIONTOUCH SONLANDIRILDI
echo =========================================================
pause
exit /b 0
