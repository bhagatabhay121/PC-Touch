@echo off
echo ========================================
echo Laptop Remote Control - Auto-Start Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

echo [1/5] Python found!
echo.

REM Install required packages
echo [2/5] Installing required packages...
pip install pyautogui psutil pillow
if errorlevel 1 (
    echo Warning: Some packages may have failed to install
)
echo.

REM Get the script directory
set "SCRIPT_DIR=%~dp0"

REM Create the startup VBS script with correct path
echo [3/5] Creating startup script...
(
    echo Set WshShell = CreateObject^("WScript.Shell"^)
    echo WshShell.Run "pythonw ""%SCRIPT_DIR%laptop_server_autostart.py""", 0, False
    echo Set WshShell = Nothing
) > "%SCRIPT_DIR%windows_startup_silent.vbs"
echo.

REM Get the Startup folder path
echo [4/5] Adding to Windows Startup...
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

REM Create a shortcut to the VBS script
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%STARTUP_FOLDER%\LaptopRemoteServer.lnk'); $Shortcut.TargetPath = '%SCRIPT_DIR%windows_startup_silent.vbs'; $Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; $Shortcut.Save()"

if exist "%STARTUP_FOLDER%\LaptopRemoteServer.lnk" (
    echo Startup shortcut created successfully!
) else (
    echo Warning: Could not create startup shortcut
    echo You can manually copy windows_startup_silent.vbs to:
    echo %STARTUP_FOLDER%
)
echo.

REM Create log directory
if not exist "%USERPROFILE%\.laptop_remote" mkdir "%USERPROFILE%\.laptop_remote"

echo [5/5] Setup complete!
echo.
echo ========================================
echo Installation Summary:
echo ========================================
echo - Server script: %SCRIPT_DIR%laptop_server_autostart.py
echo - Startup script: %SCRIPT_DIR%windows_startup_silent.vbs
echo - Startup folder: %STARTUP_FOLDER%
echo - Log directory: %USERPROFILE%\.laptop_remote
echo.
echo The server will now start automatically when you log in.
echo.

REM Ask if user wants to start server now
echo Do you want to start the server now? (Y/N)
choice /C YN /N
if errorlevel 2 goto :skip_start
if errorlevel 1 goto :start_now

:start_now
echo.
echo Starting server...
start /B pythonw "%SCRIPT_DIR%laptop_server_autostart.py"
echo Server started in background!
echo.
goto :show_ip

:skip_start
echo.
echo Server will start on next login.
echo To start manually, run: python laptop_server_autostart.py
echo.

:show_ip
echo ========================================
echo Your computer's IP address:
echo ========================================
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do echo %%a
echo.
echo Use this IP address to connect from your mobile device.
echo Default port: 5555
echo.
echo ========================================
echo Firewall Notice:
echo ========================================
echo If the mobile app cannot connect, you may need to:
echo 1. Allow Python through Windows Firewall
echo 2. Ensure both devices are on the same network
echo.

pause
