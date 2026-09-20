@echo off
echo =============================================
echo   A.R.L.O. Setup
echo =============================================
echo.

echo Checking for Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found. Downloading and installing Python...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe' -OutFile 'python_installer.exe'"
    python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python_installer.exe
    echo Python installed. Please close this window, restart your computer, then run setup.bat again.
    pause
    exit /b
)
echo Python found.
echo.

echo Checking for VS Code...
where code >nul 2>&1
if errorlevel 1 (
    echo VS Code not found. Downloading and installing VS Code...
    powershell -Command "Invoke-WebRequest -Uri 'https://code.visualstudio.com/sha/download?build=stable&os=win32-x64-user' -OutFile 'vscode_installer.exe'"
    vscode_installer.exe /verysilent /mergetasks=!runcode,addcontextmenufiles,addcontextmenufolders,addtopath
    del vscode_installer.exe
    echo VS Code installed.
) else (
    echo VS Code found.
)
echo.

echo Downloading A.R.L.O...
if not exist "arlo-assistant" (
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/andrewpareja2013-coder/arlo-assistant/archive/refs/heads/main.zip' -OutFile 'arlo_temp.zip'; Expand-Archive -Path 'arlo_temp.zip' -DestinationPath '.' -Force; Remove-Item 'arlo_temp.zip'"
    ren "arlo-assistant-main" "arlo-assistant"
    echo A.R.L.O. downloaded.
) else (
    echo A.R.L.O. already present.
)
cd arlo-assistant
echo.

echo Installing required Python packages...
python -m pip install --upgrade pip
python -m pip install requests cryptography pywin32 psutil pygetwindow ddgs Pillow librehardwaremonitor-api faster-whisper sounddevice numpy
echo.

echo Checking for LibreHardwareMonitor...
if not exist "LibreHardwareMonitor\LibreHardwareMonitor.exe" (
    echo Downloading LibreHardwareMonitor...
    powershell -Command "$release = Invoke-RestMethod -Uri 'https://api.github.com/repos/LibreHardwareMonitor/LibreHardwareMonitor/releases/latest'; $asset = $release.assets | Where-Object { $_.name -like '*.zip' } | Select-Object -First 1; Invoke-WebRequest -Uri $asset.browser_download_url -OutFile 'lhm_temp.zip'; Expand-Archive -Path 'lhm_temp.zip' -DestinationPath 'LibreHardwareMonitor' -Force; Remove-Item 'lhm_temp.zip'"
    echo LibreHardwareMonitor downloaded.
) else (
    echo LibreHardwareMonitor already present.
)
echo.

echo =============================================
echo   Setup complete! Opening the project...
echo =============================================
code .

pause
