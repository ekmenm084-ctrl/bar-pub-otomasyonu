@echo off
title GitHub'a Gonder
cd /d "%~dp0"
set PATH=%LOCALAPPDATA%\Programs\MinGit\cmd;%PATH%
echo ===================================================
echo Proje GitHub'a Gonderiliyor...
echo Hedef: https://github.com/ekmenm084-ctrl/bar-pub-otomasyonu.git
echo ===================================================
echo.
git push -u origin main
echo.
echo ===================================================
echo Islem tamamlandi.
echo ===================================================
pause
