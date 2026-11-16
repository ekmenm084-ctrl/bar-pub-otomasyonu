@echo off
title Pub Bardak Takip Testi (Telefon IP Kamera)
cd /d "%~dp0"
echo ===================================================
echo Telefondaki IP Webcam adresini girin
echo Ornek: http://192.168.1.35:8080/video
echo ===================================================
set /p ip_url="Adresi buraya yapistirin: "
python poc_test.py --source "%ip_url%"
pause
