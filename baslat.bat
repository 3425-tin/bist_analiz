@echo off
REM BIST Analiz - Windows baslatici. Cift tiklayin.
cd /d "%~dp0"
if not exist .venv (
    echo Ilk kurulum yapiliyor, birkac dakika surebilir...
    python -m venv .venv || (echo Python bulunamadi. python.org'dan Python 3.11+ kurun. & pause & exit /b 1)
    .venv\Scripts\python -m pip install --upgrade pip
    .venv\Scripts\python -m pip install -r requirements.txt
)
.venv\Scripts\python -m streamlit run app.py
pause
