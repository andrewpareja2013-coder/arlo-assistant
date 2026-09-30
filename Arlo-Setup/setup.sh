#!/bin/bash
set -e

echo "============================================="
echo "  A.R.L.O. Setup"
echo "============================================="
echo

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Checking for Python 3..."
if ! command -v python3 &> /dev/null; then
    echo "Python 3 not found. Attempting to install..."
    if command -v apt &> /dev/null; then
        sudo apt update
        sudo apt install -y python3 python3-pip
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y python3 python3-pip
    elif command -v pacman &> /dev/null; then
        sudo pacman -Sy --noconfirm python python-pip
    else
        echo "Could not detect a supported package manager. Please install Python 3 manually, then run this script again."
        exit 1
    fi
fi
echo "Python 3 found."
echo

echo "Checking for VS Code..."
if ! command -v code &> /dev/null; then
    echo "VS Code not found. Attempting to install..."
    if command -v apt &> /dev/null; then
        sudo apt install -y wget gpg
        wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
        sudo install -D -o root -g root -m 644 packages.microsoft.gpg /etc/apt/keyrings/packages.microsoft.gpg
        echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" | sudo tee /etc/apt/sources.list.d/vscode.list > /dev/null
        rm packages.microsoft.gpg
        sudo apt update
        sudo apt install -y code
    else
        echo "Automatic VS Code install is only supported on Debian/Ubuntu-based systems right now."
        echo "Please install VS Code manually from https://code.visualstudio.com, then run this script again."
        exit 1
    fi
fi
echo "VS Code found."
echo

echo "Installing lm-sensors (for system temperature monitoring)..."
if command -v apt &> /dev/null; then
    sudo apt install -y lm-sensors espeak
    sudo sensors-detect --auto
elif command -v dnf &> /dev/null; then
    sudo dnf install -y lm_sensors espeak
elif command -v pacman &> /dev/null; then
    sudo pacman -Sy --noconfirm lm_sensors espeak
fi
echo

echo "Downloading A.R.L.O..."
if [ ! -d "arlo-assistant" ]; then
    curl -L "https://github.com/andrewpareja2013-coder/arlo-assistant/archive/refs/heads/main.zip" -o arlo_temp.zip
    unzip -q arlo_temp.zip
    mv arlo-assistant-main arlo-assistant
    rm arlo_temp.zip
    echo "A.R.L.O. downloaded."
else
    echo "A.R.L.O. already present."
fi
cd arlo-assistant
echo

echo "Installing required Python packages..."
python3 -m pip install --upgrade pip --break-system-packages
python3 -m pip install requests cryptography psutil pygetwindow ddgs Pillow faster-whisper sounddevice numpy --break-system-packages
echo

echo "============================================="
echo "  Setup complete! Opening the project..."
echo "============================================="
code .