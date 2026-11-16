@echo off
title Pub Bardak Takip Testi
cd /d "%~dp0"
echo ===================================================
echo Pub Bardak & Altlik Takip Testi Baslatiliyor...
echo Kamera: Laptop Kamerasi (Kaynak: 0)
echo ===================================================
python poc_test.py --source 0
pause
