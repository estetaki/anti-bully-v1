@echo off
echo Memulai instalasi dan menjalankan No-Bully App...

REM Cek apakah Python terinstall
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python tidak terinstall. Silakan download dan install Python dari https://www.python.org/downloads/
    echo Pastikan menambahkan Python ke PATH saat instalasi.
    pause
    exit /b 1
)

echo Python ditemukan.

REM Buat virtual environment jika belum ada
if not exist venv (
    echo Membuat virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Gagal membuat virtual environment.
        pause
        exit /b 1
    )
)

echo Virtual environment siap.

REM Activate venv
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Error: Gagal mengaktifkan virtual environment.
    pause
    exit /b 1
)

echo Virtual environment diaktifkan.

REM Install requirements
echo Menginstall dependensi dari Requirements.txt...
pip install -r Requirements.txt
if errorlevel 1 (
    echo Error: Gagal menginstall dependensi.
    pause
    exit /b 1
)

echo Dependensi berhasil diinstall.

REM Jalankan aplikasi
echo Menjalankan aplikasi...
streamlit run Aplikasi.py

pause
