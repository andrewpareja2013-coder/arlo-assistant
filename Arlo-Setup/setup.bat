@echo off
cd /d "%USERPROFILE%\Downloads"

echo =============================================
echo   A.R.L.O. Setup
echo =============================================
echo.
echo Tip: don't click inside this window while it runs - clicking pauses it.
echo If it ever looks frozen, press Enter once.
echo.

rem ---------- Python ----------
echo Checking for Python...
python --version >nul 2>&1
if not errorlevel 1 goto python_ok

echo Python not found. Downloading it, this can take a minute...
powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe' -OutFile 'python_installer.exe'"
if not exist "python_installer.exe" goto python_download_failed
for %%F in (python_installer.exe) do echo Downloaded installer size: %%~zF bytes - should be roughly 25-30 million

echo Installing Python for this user only. No window will appear, please wait 1-2 minutes...
start /wait python_installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_launcher=0 Include_test=0 Include_doc=0 /log "%CD%\python_install.log"
echo Python installer exit code: %errorlevel%
set "PY_DIR=%LOCALAPPDATA%\Programs\Python\Python313"
if exist "%PY_DIR%\python.exe" goto python_path

echo.
echo The per-user install did not complete. Trying an all-users install instead.
echo If a Windows permission prompt appears, click Yes.
start /wait python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_launcher=0 Include_test=0 Include_doc=0 /log "%CD%\python_install_allusers.log"
echo All-users installer exit code: %errorlevel%
set "PY_DIR=C:\Program Files\Python313"
if exist "%PY_DIR%\python.exe" goto python_path

echo.
echo Python could not be installed. The installer and its logs are kept in this folder.
echo Please send the exit codes shown above plus the python_install log files.
pause
exit /b 1

:python_download_failed
echo The Python download failed. Check the internet connection and run this again.
pause
exit /b 1

:python_path
set "PATH=%PY_DIR%;%PY_DIR%\Scripts;%PATH%"
python --version >nul 2>&1
if errorlevel 1 (
    echo Python was installed but could not be started. Please restart the PC and run this again.
    pause
    exit /b 1
)
del python_installer.exe

:python_ok
echo Python found.
echo.

rem ---------- VS Code ----------
echo Checking for VS Code...
set "CODE_CMD=%LOCALAPPDATA%\Programs\Microsoft VS Code\bin\code.cmd"
if exist "%CODE_CMD%" goto vscode_ok
where code >nul 2>&1
if errorlevel 1 goto vscode_install
set "CODE_CMD=code"
goto vscode_ok

:vscode_install
echo VS Code not found. Downloading it, this can take a few minutes...
powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri 'https://code.visualstudio.com/sha/download?build=stable&os=win32-x64-user' -OutFile 'vscode_installer.exe'"
echo Installing VS Code - no window will appear, please wait...
start /wait vscode_installer.exe /verysilent /mergetasks=!runcode,addcontextmenufiles,addcontextmenufolders,addtopath
del vscode_installer.exe
if not exist "%CODE_CMD%" (
    echo VS Code could not be installed. Please install it from https://code.visualstudio.com and run this again.
    pause
    exit /b 1
)

:vscode_ok
echo VS Code found.
echo.

echo Installing VS Code Python extension, the first run can take a minute...
call "%CODE_CMD%" --install-extension ms-python.python
echo.

rem ---------- A.R.L.O. ----------
echo Downloading A.R.L.O...
if exist "arlo-assistant" goto arlo_present
if exist "arlo-assistant-main" rmdir /s /q "arlo-assistant-main"
powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri 'https://github.com/andrewpareja2013-coder/arlo-assistant/archive/refs/heads/main.zip' -OutFile 'arlo_temp.zip'; Expand-Archive -Path 'arlo_temp.zip' -DestinationPath '.' -Force; Remove-Item 'arlo_temp.zip'"
ren "arlo-assistant-main" "arlo-assistant"
echo A.R.L.O. downloaded.
goto arlo_done

:arlo_present
echo A.R.L.O. already present.

:arlo_done
cd "arlo-assistant\A.R.L.O PRODUCTION VERSION"
if errorlevel 1 (
    echo Could not find the A.R.L.O. project folder. The download may be incomplete.
    pause
    exit /b 1
)
echo.

rem ---------- Python packages ----------
echo Installing required Python packages, this is the slowest step...
python -m pip install --disable-pip-version-check --progress-bar off requests cryptography pywin32 psutil pygetwindow ddgs Pillow librehardwaremonitor-api faster-whisper sounddevice numpy
if errorlevel 1 (
    echo Some packages failed to install. Check your internet connection and run this again.
    pause
    exit /b 1
)
echo.

rem ---------- LibreHardwareMonitor ----------
echo Checking for LibreHardwareMonitor...
if exist "LibreHardwareMonitor\LibreHardwareMonitor.exe" goto lhm_ok
echo Downloading LibreHardwareMonitor...
powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; $release = Invoke-RestMethod -Uri 'https://api.github.com/repos/LibreHardwareMonitor/LibreHardwareMonitor/releases/latest'; $asset = $release.assets | Where-Object { $_.name -like '*.zip' } | Select-Object -First 1; Invoke-WebRequest -Uri $asset.browser_download_url -OutFile 'lhm_temp.zip'; Expand-Archive -Path 'lhm_temp.zip' -DestinationPath 'LibreHardwareMonitor' -Force; Remove-Item 'lhm_temp.zip'"
echo LibreHardwareMonitor downloaded.
goto lhm_done

:lhm_ok
echo LibreHardwareMonitor already present.

:lhm_done
echo.

echo =============================================
echo   Setup complete!
echo =============================================
echo.
echo Press any key to open the project in VS Code...
pause >nul

set "CODE_EXE=%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"
if exist "%CODE_EXE%" (
    start "" "%CODE_EXE%" .
) else (
    start "" "%CODE_CMD%" .
)
exit