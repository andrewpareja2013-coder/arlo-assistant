# A.R.L.O. Setup Guide

Welcome! Setting up A.R.L.O. is now mostly automatic. This should take
about 10-15 minutes, most of which is just waiting for downloads.

---

## Step 1: Download A.R.L.O.

1. Go to (https://github.com/andrewpareja2013-coder/arlo-assistant/blob/main/Arlo-Setup/SETUP.md)
2. Click the green "Code" button, then "Download ZIP"
3. Right-click the downloaded zip and choose "Extract All..."
4. Choose your Desktop as the destination, then click "Extract"

## Step 2: Run the setup script

1. Open the extracted folder
2. Find the file named `setup.bat`
3. Double-click it
4. If a security popup appears asking if you want to run the file,
   click "More info" then "Run anyway" (this is normal Windows caution
   for new programs, not a sign anything is wrong)
5. The setup script will now automatically:
   - Install Python (if you don't already have it)
   - Install every required component
   - Download LibreHardwareMonitor (used for system temperature readings)
6. This may take several minutes depending on your internet speed --
   let it run, don't close the window
7. When finished, it will automatically open the project in VS Code

## Step 3: Run A.R.L.O. for the first time

1. In VS Code, look at the file list on the left side
2. Click on the file named `main.py`
3. Click the small ▶ (play/run) button in the top-right corner
4. A terminal window will open at the bottom showing A.R.L.O. starting up

## Step 4: Create your account

The first time you run A.R.L.O., it will show "No accounts exist yet."
Follow the on-screen prompts:
1. Choose a username
2. Create a password
3. Confirm that password
4. Answer the two setup questions (temperature units, 24-hour time)

## Step 5: Try it out

Type a message and press Enter to chat. Try asking:
- "What time is it?"
- "What's the weather like?"
- "What's my system status?"

To exit A.R.L.O. at any time, press Enter on a blank line.

---

## Troubleshooting

**A security warning appears when running setup.bat**
This is normal for new downloaded programs. Click "More info" then
"Run anyway."

**Setup seems stuck**
Make sure you have an active internet connection -- setup downloads
several components automatically. Large downloads may just take a
few minutes on slower connections.

**"Python is not recognized" even after setup finishes**
Restart your computer, then try running `main.py` again. Windows
sometimes needs a restart to recognize newly installed programs.

**Still stuck?**
Take a screenshot of the exact error message you're seeing and send
it to your local admin.
