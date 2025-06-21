@echo off
echo ========================================
echo  BARCODE SCANNER FIREWALL SETUP
echo ========================================
echo.
echo This script will configure Windows Firewall
echo to allow your barcode scanner app to be
echo accessed from mobile devices on your network.
echo.
echo You will need Administrator privileges.
echo.
pause

echo Checking if running as Administrator...
net session >nul 2>&1
if %errorLevel% == 0 (
    echo SUCCESS: Running as Administrator
) else (
    echo ERROR: Not running as Administrator
    echo Please right-click this file and "Run as Administrator"
    pause
    exit /b 1
)

echo.
echo Adding firewall rules for Python...
netsh advfirewall firewall add rule name="Python Barcode Scanner - HTTP" dir=in action=allow protocol=TCP localport=5000 program=python.exe
netsh advfirewall firewall add rule name="Python Barcode Scanner - HTTPS" dir=in action=allow protocol=TCP localport=5000 program=python.exe

echo.
echo Adding generic port rules (backup)...
netsh advfirewall firewall add rule name="Barcode Scanner Port 5000" dir=in action=allow protocol=TCP localport=5000

echo.
echo ========================================
echo  FIREWALL CONFIGURATION COMPLETE!
echo ========================================
echo.
echo Your barcode scanner should now be accessible
echo from mobile devices on the same WiFi network.
echo.
echo Next steps:
echo 1. Run: python barcode_scanner_app.py
echo 2. Use the network URL on your mobile device
echo 3. Accept the HTTPS certificate warning if prompted
echo.
pause 