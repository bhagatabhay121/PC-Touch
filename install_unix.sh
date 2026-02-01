#!/bin/bash

echo "========================================"
echo "Laptop Remote Control - Auto-Start Setup"
echo "========================================"
echo ""

# Detect OS
OS_TYPE=$(uname -s)

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3 first"
    exit 1
fi

echo "[1/6] Python found: $(python3 --version)"
echo ""

# Install required packages
echo "[2/6] Installing required packages..."
pip3 install pyautogui psutil pillow 2>/dev/null || pip3 install pyautogui psutil pillow --user
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Copy server script to home directory
echo "[3/6] Setting up server script..."
cp "$SCRIPT_DIR/laptop_server_autostart.py" "$HOME/laptop_server_autostart.py"
chmod +x "$HOME/laptop_server_autostart.py"
echo ""

# Create log directory
mkdir -p "$HOME/.laptop_remote"

if [ "$OS_TYPE" == "Darwin" ]; then
    # macOS setup
    echo "[4/6] Configuring macOS LaunchAgent..."
    
    # Get username
    USERNAME=$(whoami)
    
    # Create plist file
    cat > "$HOME/Library/LaunchAgents/com.laptopremote.server.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.laptopremote.server</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$HOME/laptop_server_autostart.py</string>
    </array>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <true/>
    
    <key>StandardOutPath</key>
    <string>$HOME/.laptop_remote/stdout.log</string>
    
    <key>StandardErrorPath</key>
    <string>$HOME/.laptop_remote/stderr.log</string>
    
    <key>WorkingDirectory</key>
    <string>$HOME</string>
</dict>
</plist>
EOF
    
    echo "[5/6] Loading LaunchAgent..."
    launchctl load "$HOME/Library/LaunchAgents/com.laptopremote.server.plist"
    
    echo "[6/6] Starting server..."
    launchctl start com.laptopremote.server
    
    echo ""
    echo "========================================"
    echo "Installation Complete!"
    echo "========================================"
    echo "Server installed as macOS LaunchAgent"
    echo ""
    echo "Useful commands:"
    echo "  Check status: launchctl list | grep laptopremote"
    echo "  View logs:    tail -f ~/.laptop_remote/server.log"
    echo "  Stop server:  launchctl stop com.laptopremote.server"
    echo "  Uninstall:    launchctl unload ~/Library/LaunchAgents/com.laptopremote.server.plist"
    echo ""

elif [ "$OS_TYPE" == "Linux" ]; then
    # Linux setup
    echo "[4/6] Configuring systemd service..."
    
    # Get username
    USERNAME=$(whoami)
    
    # Create systemd user directory
    mkdir -p "$HOME/.config/systemd/user"
    
    # Create service file
    cat > "$HOME/.config/systemd/user/laptop-remote.service" << EOF
[Unit]
Description=Laptop Remote Control Server
After=network.target

[Service]
Type=simple
WorkingDirectory=$HOME
ExecStart=/usr/bin/python3 $HOME/laptop_server_autostart.py
Restart=always
RestartSec=10
StandardOutput=append:$HOME/.laptop_remote/server.log
StandardError=append:$HOME/.laptop_remote/error.log

[Install]
WantedBy=default.target
EOF
    
    echo "[5/6] Enabling service..."
    systemctl --user enable laptop-remote.service
    
    echo "[6/6] Starting server..."
    systemctl --user start laptop-remote.service
    
    echo ""
    echo "========================================"
    echo "Installation Complete!"
    echo "========================================"
    echo "Server installed as systemd user service"
    echo ""
    echo "Useful commands:"
    echo "  Check status: systemctl --user status laptop-remote.service"
    echo "  View logs:    journalctl --user -u laptop-remote.service -f"
    echo "  Stop server:  systemctl --user stop laptop-remote.service"
    echo "  Disable:      systemctl --user disable laptop-remote.service"
    echo ""

else
    echo "[4/6] Detected: $OS_TYPE"
    echo "Setting up using crontab..."
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "@reboot /usr/bin/python3 $HOME/laptop_server_autostart.py &") | crontab -
    
    echo "[5/6] Starting server..."
    nohup python3 "$HOME/laptop_server_autostart.py" > "$HOME/.laptop_remote/server.log" 2>&1 &
    
    echo "[6/6] Setup complete!"
    echo ""
    echo "========================================"
    echo "Installation Complete!"
    echo "========================================"
    echo "Server will start automatically on boot"
    echo ""
fi

# Show IP address
echo "========================================"
echo "Your computer's IP address:"
echo "========================================"
if [ "$OS_TYPE" == "Darwin" ]; then
    ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}'
else
    hostname -I | awk '{print $1}'
fi
echo ""
echo "Use this IP address to connect from your mobile device."
echo "Default port: 5555"
echo ""

# Check if server is running
sleep 2
if lsof -i :5555 &> /dev/null || netstat -an 2>/dev/null | grep -q ":5555"; then
    echo "✓ Server is running and listening on port 5555"
else
    echo "⚠ Server may not be running. Check logs:"
    echo "  cat ~/.laptop_remote/server.log"
fi

echo ""
echo "========================================"
echo "Firewall Notice:"
echo "========================================"
echo "If the mobile app cannot connect, ensure:"
echo "1. Both devices are on the same WiFi network"
echo "2. Firewall allows connections on port 5555"
if [ "$OS_TYPE" == "Linux" ]; then
    echo "3. Run: sudo ufw allow 5555/tcp (if using UFW)"
fi
echo ""
echo "Installation complete! 🎉"
