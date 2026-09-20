@echo off
echo =============================================
echo   A.R.L.O. V3 Setup
echo =============================================
echo.

echo Checking for Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python was not found. Please install Python from https://python.org first, then run this setup again.
    pause
    exit /b
)
echo Python found.
echo.

echo Installing required Python packages...
python -m pip install --upgrade pip
python -m pip install requests cryptography pywin32 psutil pygetwindow ddgs Pillow librehardwaremonitor-api faster-whisper sounddevice numpy
echo.

echo Checking for LibreHardwareMonitor...
if not exist "LibreHardwareMonitor\LibreHardwareMonitor.exe" (
    echo Downloading LibreHardwareMonitor, this may take a minute...
    powershell -Command "$release = Invoke-RestMethod -Uri 'https://api.github.com/repos/LibreHardwareMonitor/LibreHardwareMonitor/releases/latest'; $asset = $release.assets | Where-Object { $_.name -like '*.zip' } | Select-Object -First 1; Invoke-WebRequest -Uri $asset.browser_download_url -OutFile 'lhm_temp.zip'; Expand-Archive -Path 'lhm_temp.zip' -DestinationPath 'LibreHardwareMonitor' -Force; Remove-Item 'lhm_temp.zip'"
    echo LibreHardwareMonitor downloaded and ready.
) else (
    echo LibreHardwareMonitor already present.
)
echo.

echo =============================================
echo   Setup complete! Opening the project in VS Code...
echo =============================================
code .

pause