@echo off
REM BIST Analiz - Windows baslatici. Cift tiklayin.
cd /d "%~dp0"
if not exist .venv (
    echo Ilk kurulum yapiliyor, birkac dakika surebilir...
    py -3 -m venv .venv 2>nul || python -m venv .venv
    if not exist .venv\Scripts\python.exe (
        echo Python bulunamadi. Python 3.11+ kurup bu pencereyi yeniden acin.
        pause
        exit /b 1
    )
    .venv\Scripts\python -m pip install --upgrade pip
    .venv\Scripts\python -m pip install -r requirements.txt
)
.venv\Scripts\python -m streamlit run app.py
pause
