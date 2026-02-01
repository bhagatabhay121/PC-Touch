# Laptop Remote Control - Auto-Start Setup Guide

This guide will help you set up the laptop server to automatically start when your laptop boots up.

---

## 📋 Prerequisites

1. Python 3.7 or higher installed
2. Required packages: `pyautogui`, `psutil`, `pillow`
3. The server script: `laptop_server_autostart.py`

---

## 🪟 WINDOWS SETUP

### Method 1: Using Startup Folder (Easiest)

1. **Locate the Startup folder:**
   - Press `Win + R`
   - Type: `shell:startup`
   - Press Enter

2. **Copy the startup script:**
   - Copy `windows_startup_silent.vbs` to the Startup folder
   - Also place `laptop_server_autostart.py` in the same directory

3. **Edit the VBS script (if needed):**
   - Right-click `windows_startup_silent.vbs` → Edit
   - Update the path to your Python script if it's in a different location

4. **Test it:**
   - Double-click the VBS file to test
   - Check Task Manager → Background Processes for "pythonw.exe"

### Method 2: Using Task Scheduler (More Control)

1. **Open Task Scheduler:**
   - Press `Win + R`
   - Type: `taskschd.msc`
   - Press Enter

2. **Create a new task:**
   - Click "Create Basic Task"
   - Name: "Laptop Remote Server"
   - Trigger: "When I log on"
   - Action: "Start a program"
   - Program: `pythonw` (or full path: `C:\Python\pythonw.exe`)
   - Arguments: `"C:\path\to\laptop_server_autostart.py"`
   - Click Finish

3. **Configure advanced settings:**
   - Right-click the task → Properties
   - Check "Run with highest privileges"
   - Check "Hidden" (under Settings)
   - Uncheck "Stop the task if it runs longer than"

### Method 3: Windows Service (Advanced)

```bash
# Install NSSM (Non-Sucking Service Manager)
# Download from: https://nssm.cc/download

# Open Command Prompt as Administrator
nssm install LaptopRemoteServer

# In the NSSM GUI:
# Path: C:\Python\pythonw.exe
# Startup directory: C:\path\to\your\script
# Arguments: laptop_server_autostart.py
# Click "Install service"

# Start the service
nssm start LaptopRemoteServer
```

---

## 🍎 macOS SETUP

### Using LaunchAgent

1. **Copy the server script:**
   ```bash
   cp laptop_server_autostart.py ~/laptop_server_autostart.py
   ```

2. **Edit the plist file:**
   ```bash
   nano com.laptopremote.server.plist
   ```
   - Replace `YOUR_USERNAME` with your actual username (3 places)
   - Save and exit (Ctrl+X, Y, Enter)

3. **Copy plist to LaunchAgents:**
   ```bash
   cp com.laptopremote.server.plist ~/Library/LaunchAgents/
   ```

4. **Create log directory:**
   ```bash
   mkdir -p ~/.laptop_remote
   ```

5. **Load the service:**
   ```bash
   launchctl load ~/Library/LaunchAgents/com.laptopremote.server.plist
   ```

6. **Start the service:**
   ```bash
   launchctl start com.laptopremote.server
   ```

### Useful macOS Commands:

```bash
# Check if running
launchctl list | grep laptopremote

# Stop the service
launchctl stop com.laptopremote.server

# Unload the service
launchctl unload ~/Library/LaunchAgents/com.laptopremote.server.plist

# View logs
tail -f ~/.laptop_remote/server.log
tail -f ~/.laptop_remote/stdout.log
```

---

## 🐧 LINUX SETUP

### Using systemd (Recommended)

1. **Copy the server script:**
   ```bash
   cp laptop_server_autostart.py ~/laptop_server_autostart.py
   chmod +x ~/laptop_server_autostart.py
   ```

2. **Edit the service file:**
   ```bash
   nano laptop-remote.service
   ```
   - Replace `%YOUR_USERNAME%` with your actual username
   - Save and exit

3. **Copy to systemd user directory:**
   ```bash
   mkdir -p ~/.config/systemd/user
   cp laptop-remote.service ~/.config/systemd/user/
   ```

4. **Create log directory:**
   ```bash
   mkdir -p ~/.laptop_remote
   ```

5. **Enable and start the service:**
   ```bash
   systemctl --user enable laptop-remote.service
   systemctl --user start laptop-remote.service
   ```

6. **Check status:**
   ```bash
   systemctl --user status laptop-remote.service
   ```

### Using crontab (Alternative)

```bash
# Edit crontab
crontab -e

# Add this line (replace with your path)
@reboot /usr/bin/python3 /home/YOUR_USERNAME/laptop_server_autostart.py &

# Save and exit
```

### Using ~/.profile (Simple)

```bash
# Edit your profile
nano ~/.profile

# Add at the end:
# Start Laptop Remote Server
if ! pgrep -f "laptop_server_autostart.py" > /dev/null; then
    nohup python3 ~/laptop_server_autostart.py > ~/.laptop_remote/server.log 2>&1 &
fi

# Save and exit
```

### Useful Linux Commands:

```bash
# Check if running
ps aux | grep laptop_server_autostart

# Stop the service
systemctl --user stop laptop-remote.service

# View logs
journalctl --user -u laptop-remote.service -f
# OR
tail -f ~/.laptop_remote/server.log

# Disable auto-start
systemctl --user disable laptop-remote.service
```

---

## ✅ Verification

After setup, verify the server is running:

### Windows:
1. Open Task Manager (Ctrl+Shift+Esc)
2. Look for `pythonw.exe` in Background Processes
3. Or run: `netstat -an | findstr 5555`

### macOS/Linux:
```bash
# Check if port 5555 is listening
netstat -an | grep 5555
# OR
lsof -i :5555

# Check process
ps aux | grep laptop_server_autostart
```

### Test Connection:
1. Find your laptop's IP address:
   - Windows: `ipconfig`
   - macOS/Linux: `ifconfig` or `ip addr`

2. Open the mobile app
3. Enter the IP address and connect

---

## 🔧 Troubleshooting

### Server not starting:

1. **Check Python path:**
   ```bash
   # Windows
   where python
   where pythonw
   
   # macOS/Linux
   which python3
   ```

2. **Install dependencies manually:**
   ```bash
   pip install pyautogui psutil pillow
   ```

3. **Check permissions:**
   - Windows: Run as Administrator
   - macOS/Linux: Check file permissions (`chmod +x`)

4. **View logs:**
   - Check `~/.laptop_remote/server.log`
   - Look for error messages

### Firewall Issues:

**Windows:**
```powershell
# Allow Python through firewall
netsh advfirewall firewall add rule name="Laptop Remote Server" dir=in action=allow program="C:\Python\pythonw.exe" enable=yes
```

**macOS:**
- System Preferences → Security & Privacy → Firewall
- Add Python to allowed apps

**Linux:**
```bash
# UFW
sudo ufw allow 5555/tcp

# Firewalld
sudo firewall-cmd --permanent --add-port=5555/tcp
sudo firewall-cmd --reload
```

### Port already in use:

```bash
# Find what's using port 5555
# Windows
netstat -ano | findstr :5555

# macOS/Linux
lsof -i :5555

# Kill the process or change port in server script
```

---

## 🛑 Stop/Disable Auto-Start

### Windows:
- Remove from Startup folder
- Or disable in Task Scheduler

### macOS:
```bash
launchctl unload ~/Library/LaunchAgents/com.laptopremote.server.plist
rm ~/Library/LaunchAgents/com.laptopremote.server.plist
```

### Linux:
```bash
systemctl --user stop laptop-remote.service
systemctl --user disable laptop-remote.service
```

---

## 📱 Mobile App Connection

Once the server is running automatically:

1. Open the mobile app
2. Enter your laptop's IP address (e.g., 192.168.1.100)
3. Port: 5555
4. Click CONNECT

The server will always be ready when your laptop is on!

---

## 🔒 Security Notes

1. **Firewall:** The server only listens on your local network
2. **Logs:** Check logs regularly in `~/.laptop_remote/`
3. **Updates:** Keep Python and packages updated
4. **Network:** Use only on trusted networks

---

## 📞 Need Help?

If you encounter issues:

1. Check the log file: `~/.laptop_remote/server.log`
2. Ensure Python and packages are installed
3. Verify firewall settings
4. Test manual start first: `python laptop_server_autostart.py`

---

Happy remote controlling! 🎮
