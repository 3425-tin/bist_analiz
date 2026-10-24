#!/usr/bin/env bash
# BIST Analiz - macOS/Linux baslatici:  ./baslat.sh
set -e
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
    echo "Ilk kurulum yapiliyor, birkac dakika surebilir..."
    python3 -m venv .venv
    .venv/bin/python -m pip install --upgrade pip
    .venv/bin/python -m pip install -r requirements.txt
fi
# Streamlit ilk acilista e-posta sorar; bos kimlik dosyasi ile atla
if [ ! -f ~/.streamlit/credentials.toml ]; then
    mkdir -p ~/.streamlit && printf '[general]\nemail = ""\n' > ~/.streamlit/credentials.toml
fi
exec .venv/bin/python -m streamlit run app.py
