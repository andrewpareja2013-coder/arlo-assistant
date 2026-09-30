# A.R.L.O. Setup Guide

Welcome! Setup is mostly automatic. Follow the steps for your operating system.

---

## Windows

### Step 1: Download A.R.L.O.
1. Go to https://github.com/andrewpareja2013-coder/arlo-assistant
2. Click the green "Code" button, then "Download ZIP"
3. Right-click the downloaded zip and choose "Extract All..."
4. Extract it to your Desktop (or anywhere you like)

### Step 2: Run the setup script
1. Open the extracted folder
2. Double-click `setup.bat`
3. If a security popup appears, click "More info" then "Run anyway"
4. The script will automatically install Python, VS Code, all required components,
   and LibreHardwareMonitor (used for system temperature readings)
5. This may take several minutes -- let it run, don't close the window
6. When finished, it will open the project in VS Code automatically

### Step 3: Run A.R.L.O.
1. In VS Code, click on `core/main.py` in the file list
2. Click the small ▶ (play/run) button in the top-right corner

---

## Linux

### Step 1: Download A.R.L.O.
1. Go to https://github.com/andrewpareja2013-coder/arlo-assistant
2. Click the green "Code" button, then "Download ZIP"
3. Extract it wherever you like (right-click the zip → Extract, or `unzip` in a terminal)

### Step 2: Run the setup script
1. Open a terminal in the extracted folder
2. Run:
3. You'll be prompted for your password during installation (this is normal --
   the script needs it to install system packages like Python and VS Code)
4. This may take several minutes -- let it run
5. When finished, it will open the project in VS Code automatically

### Step 3: Run A.R.L.O.
1. In VS Code, click on `core/main.py` in the file list
2. Click the small ▶ (play/run) button in the top-right corner

---

## First-time account setup (both platforms)

The first time you run A.R.L.O., it will show "No accounts exist yet." Follow the prompts:
1. Choose a username
2. Create a password
3. Confirm that password
4. Answer the two setup questions (temperature units, 24-hour time)

## Try it out

Type a message and press Enter to chat. Try asking:
- "What time is it?"
- "What's the weather like?"
- "What's my system status?"

To exit at any time, press Enter on a blank line.

---

## Troubleshooting

**Windows: A security warning appears when running setup.bat**
Normal for new downloaded programs. Click "More info" then "Run anyway."

**Linux: "Permission denied" when running ./setup.sh**
Run `chmod +x setup.sh` first, then try again.

**Setup seems stuck**
Make sure you have an active internet connection -- setup downloads several
components automatically. Large downloads may take a few minutes.

**Linux: system temperature readings don't work**
The setup script runs `sensors-detect` automatically, but some hardware needs
manual configuration. Try running `sudo sensors-detect` yourself and following
its prompts, then restart A.R.L.O.

**Still stuck?**
Take a screenshot of the exact error message and send it to Work.Pareja@gmail.com.