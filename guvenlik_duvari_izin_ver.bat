@echo off
title Windows Guvenlik Duvari Port 8000 Izni
cd /d "%~dp0"
echo ========================================================
echo iPhone Baglantisi Icin Port 8000 Guvenlik Duvari Izni Ekleniyor...
echo ========================================================
echo.
netsh advfirewall firewall add rule name="Pub Bar Otomasyonu 8000" dir=in action=allow protocol=TCP localport=8000
echo.
echo Islem tamamlandi. Artik iPhone bu bilgisayara baglanabilir.
echo ========================================================
pause
