"""
Advanced Laptop Control Server - Auto-Start Version with File Transfer
Runs on the laptop with automatic startup and background mode
Features MJPEG streaming for smooth real-time preview and FILE TRANSFER
"""

import socket
import threading
import json
import pyautogui
import subprocess
import platform
import psutil
import os
import base64
import sys
import logging
import time
import struct
from datetime import datetime
from pathlib import Path
from io import BytesIO

class LaptopControlServer:
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.clients = []
        self.streaming_clients = {}  # Track which clients are streaming
        
        # Configure pyautogui
        pyautogui.FAILSAFE = False
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging to file"""
        log_dir = Path.home() / '.laptop_remote'
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / 'server.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("=== Server Starting ===")
    
    def get_system_info(self):
        """Get system information"""
        try:
            return {
                'hostname': platform.node(),
                'platform': platform.system(),
                'platform_release': platform.release(),
                'platform_version': platform.version(),
                'architecture': platform.machine(),
                'processor': platform.processor(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'battery': psutil.sensors_battery().percent if psutil.sensors_battery() else 'N/A'
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_installed_apps(self):
        """Get list of installed applications"""
        apps = []
        system = platform.system()
        
        try:
            if system == 'Windows':
                import winreg
                
                common_apps = [
                    'notepad.exe', 'calc.exe', 'mspaint.exe', 'wordpad.exe',
                    'chrome.exe', 'firefox.exe', 'msedge.exe', 'explorer.exe'
                ]
                
                reg_paths = [
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                    r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
                ]
                
                for reg_path in reg_paths:
                    try:
                        reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                        for i in range(winreg.QueryInfoKey(reg_key)[0]):
                            try:
                                subkey_name = winreg.EnumKey(reg_key, i)
                                subkey = winreg.OpenKey(reg_key, subkey_name)
                                try:
                                    app_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                    try:
                                        app_path = winreg.QueryValueEx(subkey, "DisplayIcon")[0]
                                        if app_path and app_name:
                                            app_path = app_path.split(',')[0].strip('"')
                                            apps.append({
                                                'name': app_name,
                                                'path': app_path,
                                                'type': 'installed'
                                            })
                                    except:
                                        pass
                                except:
                                    pass
                                winreg.CloseKey(subkey)
                            except:
                                continue
                        winreg.CloseKey(reg_key)
                    except:
                        continue

                for app in common_apps:
                    apps.append({
                        'name': app.replace('.exe', '').title(),
                        'path': app,
                        'type': 'system'
                    })
            
            elif system == 'Darwin':
                app_dir = '/Applications'
                if os.path.exists(app_dir):
                    for item in os.listdir(app_dir):
                        if item.endswith('.app'):
                            apps.append({
                                'name': item.replace('.app', ''),
                                'path': item.replace('.app', ''),
                                'type': 'application'
                            })

                common_mac_apps = [
                    'Safari', 'Mail', 'Calendar', 'Notes', 'Reminders',
                    'Photos', 'Music', 'Finder', 'System Preferences'
                ]
                for app in common_mac_apps:
                    if not any(a['name'] == app for a in apps):
                        apps.append({
                            'name': app,
                            'path': app,
                            'type': 'system'
                        })
            
            else:
                common_linux_apps = [
                    'firefox', 'chrome', 'chromium', 'nautilus', 'dolphin',
                    'konsole', 'gnome-terminal', 'kate', 'gedit', 'libreoffice',
                    'vlc', 'gimp', 'inkscape', 'thunderbird'
                ]
                
                for app in common_linux_apps:
                    try:
                        result = subprocess.run(['which', app], 
                                              capture_output=True, 
                                              text=True, 
                                              timeout=1)
                        if result.returncode == 0:
                            apps.append({
                                'name': app.title(),
                                'path': app,
                                'type': 'application'
                            })
                    except:
                        pass
                
                desktop_dirs = [
                    '/usr/share/applications',
                    os.path.expanduser('~/.local/share/applications')
                ]
                
                for desktop_dir in desktop_dirs:
                    if os.path.exists(desktop_dir):
                        try:
                            for filename in os.listdir(desktop_dir):
                                if filename.endswith('.desktop'):
                                    desktop_file = os.path.join(desktop_dir, filename)
                                    try:
                                        with open(desktop_file, 'r') as f:
                                            content = f.read()
                                            name_line = [line for line in content.split('\n') 
                                                       if line.startswith('Name=')]
                                            exec_line = [line for line in content.split('\n') 
                                                       if line.startswith('Exec=')]
                                            
                                            if name_line and exec_line:
                                                app_name = name_line[0].replace('Name=', '').strip()
                                                app_exec = exec_line[0].replace('Exec=', '').split()[0]
                                                
                                                if not any(a['name'] == app_name for a in apps):
                                                    apps.append({
                                                        'name': app_name,
                                                        'path': app_exec,
                                                        'type': 'application'
                                                    })
                                    except:
                                        continue
                        except:
                            continue
            
            return apps[:100]  # Limit to 100 apps
            
        except Exception as e:
            self.logger.error(f"Error getting apps: {e}")
            return []
    
    def launch_application(self, app_path):
        """Launch an application"""
        try:
            system = platform.system()
            
            if system == 'Windows':
                subprocess.Popen(app_path, shell=True)
            elif system == 'Darwin':
                if not app_path.endswith('.app'):
                    subprocess.Popen(['open', '-a', app_path])
                else:
                    subprocess.Popen(['open', app_path])
            else:
                subprocess.Popen([app_path])
            
            return {'status': 'success', 'message': f'Launched {app_path}'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def get_directory_contents(self, path=None):
        """Get contents of a directory"""
        try:
            if path is None:
                path = str(Path.home())
            
            path = Path(path)
            
            if not path.exists():
                return {'status': 'error', 'message': 'Path does not exist'}
            
            if not path.is_dir():
                return {'status': 'error', 'message': 'Path is not a directory'}
            
            contents = []
            
            try:
                for item in sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                    try:
                        stat_info = item.stat()
                        contents.append({
                            'name': item.name,
                            'path': str(item),
                            'is_dir': item.is_dir(),
                            'size': stat_info.st_size if item.is_file() else 0,
                            'modified': datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M')
                        })
                    except (PermissionError, OSError):
                        continue
            except PermissionError:
                return {'status': 'error', 'message': 'Permission denied'}
            
            return {
                'status': 'success',
                'path': str(path),
                'parent': str(path.parent) if path.parent != path else None,
                'contents': contents
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def list_files_for_download(self):
        """List files available for download from common directories"""
        try:
            file_list = []
            
            # Common directories to search
            search_dirs = [
                Path.home() / 'Downloads',
                Path.home() / 'Documents',
                Path.home() / 'Desktop',
                Path.home() / 'Pictures',
            ]
            
            for directory in search_dirs:
                if directory.exists() and directory.is_dir():
                    try:
                        for item in directory.iterdir():
                            if item.is_file():
                                try:
                                    stat_info = item.stat()
                                    # Skip very large files (>100MB)
                                    if stat_info.st_size < 100 * 1024 * 1024:
                                        file_list.append({
                                            'name': item.name,
                                            'path': str(item),
                                            'size': stat_info.st_size,
                                            'modified': datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M')
                                        })
                                except (PermissionError, OSError):
                                    continue
                    except PermissionError:
                        continue
            
            return {
                'status': 'success',
                'files': file_list[:100]  # Limit to 100 files
            }
        except Exception as e:
            self.logger.error(f"Error listing files: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def download_file(self, file_path):
        """Read file and return as base64"""
        try:
            path = Path(file_path)
            
            if not path.exists():
                return {'status': 'error', 'message': 'File not found'}
            
            if not path.is_file():
                return {'status': 'error', 'message': 'Path is not a file'}
            
            # Check file size (limit to 50MB)
            file_size = path.stat().st_size
            if file_size > 50 * 1024 * 1024:
                return {'status': 'error', 'message': 'File too large (max 50MB)'}
            
            # Read file
            with open(path, 'rb') as f:
                file_data = f.read()
            
            # Encode to base64
            encoded_data = base64.b64encode(file_data).decode('utf-8')
            
            return {
                'status': 'success',
                'filename': path.name,
                'size': file_size,
                'data': encoded_data
            }
        except PermissionError:
            return {'status': 'error', 'message': 'Permission denied'}
        except Exception as e:
            self.logger.error(f"Error downloading file: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def upload_file(self, filename, file_data_b64):
        """Save uploaded file to Downloads directory"""
        try:
            # Decode base64 data
            file_data = base64.b64decode(file_data_b64)
            
            # Save to Downloads
            downloads_dir = Path.home() / 'Downloads'
            downloads_dir.mkdir(exist_ok=True)
            
            # Create unique filename if file exists
            save_path = downloads_dir / filename
            counter = 1
            base_name = save_path.stem
            extension = save_path.suffix
            
            while save_path.exists():
                save_path = downloads_dir / f"{base_name}_{counter}{extension}"
                counter += 1
            
            # Write file
            with open(save_path, 'wb') as f:
                f.write(file_data)
            
            return {
                'status': 'success',
                'message': f'File saved to {save_path}',
                'path': str(save_path),
                'size': len(file_data)
            }
        except Exception as e:
            self.logger.error(f"Error uploading file: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def open_file(self, file_path):
        """Open a file with default application"""
        try:
            system = platform.system()
            
            if system == 'Windows':
                os.startfile(file_path)
            elif system == 'Darwin':
                subprocess.Popen(['open', file_path])
            else:
                subprocess.Popen(['xdg-open', file_path])
            
            return {'status': 'success', 'message': f'Opened {file_path}'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def execute_command(self, command_data):
        """Execute a command received from client"""
        try:
            cmd_type = command_data.get('type')
            
            if cmd_type == 'get_system_info' or cmd_type == 'system_info':
                return self.get_system_info()
            
            elif cmd_type == 'get_apps':
                return {'status': 'success', 'apps': self.get_installed_apps()}
            
            elif cmd_type == 'launch_app':
                app_path = command_data.get('path') or command_data.get('app_path')
                if not app_path:
                    return {'status': 'error', 'message': 'No app path provided'}
                return self.launch_application(app_path)
            
            elif cmd_type == 'browse_files':
                path = command_data.get('path')
                return self.get_directory_contents(path)
            
            elif cmd_type == 'list_files':
                # NEW: List files for download
                return self.list_files_for_download()
            
            elif cmd_type == 'download_file':
                # NEW: Download file
                file_path = command_data.get('path')
                if not file_path:
                    return {'status': 'error', 'message': 'No file path provided'}
                return self.download_file(file_path)
            
            elif cmd_type == 'upload_file':
                # NEW: Upload file
                filename = command_data.get('filename')
                file_data = command_data.get('data')
                if not filename or not file_data:
                    return {'status': 'error', 'message': 'Missing filename or data'}
                return self.upload_file(filename, file_data)
            
            elif cmd_type == 'open_file':
                file_path = command_data.get('file_path')
                return self.open_file(file_path)
            
            elif cmd_type == 'mouse_move':
                x = command_data.get('x', 0)
                y = command_data.get('y', 0)
                pyautogui.moveTo(x, y)
                return {'status': 'success'}
            
            elif cmd_type == 'mouse_click':
                button = command_data.get('button', 'left')
                pyautogui.click(button=button)
                return {'status': 'success'}
            
            elif cmd_type == 'type_text':
                text = command_data.get('text', '')
                pyautogui.write(text)
                return {'status': 'success'}
            
            elif cmd_type == 'key_press':
                key = command_data.get('key')
                if key:
                    pyautogui.press(key)
                return {'status': 'success'}
            
            elif cmd_type == 'volume':
                action = command_data.get('action')
                if action == 'up':
                    pyautogui.press('volumeup')
                elif action == 'down':
                    pyautogui.press('volumedown')
                elif action == 'mute':
                    pyautogui.press('volumemute')
                return {'status': 'success'}
            
            elif cmd_type == 'media':
                action = command_data.get('action')
                if action == 'play_pause':
                    pyautogui.press('playpause')
                elif action == 'next':
                    pyautogui.press('nexttrack')
                elif action == 'previous':
                    pyautogui.press('prevtrack')
                return {'status': 'success'}
            
            elif cmd_type == 'system_action':
                action = command_data.get('action')
                system = platform.system()
                
                if action == 'shutdown':
                    if system == 'Windows':
                        subprocess.Popen(['shutdown', '/s', '/t', '5'])
                    elif system == 'Darwin':
                        subprocess.Popen(['sudo', 'shutdown', '-h', '+1'])
                    else:
                        subprocess.Popen(['shutdown', '-h', '+1'])
                elif action == 'restart':
                    if system == 'Windows':
                        subprocess.Popen(['shutdown', '/r', '/t', '5'])
                    elif system == 'Darwin':
                        subprocess.Popen(['sudo', 'shutdown', '-r', '+1'])
                    else:
                        subprocess.Popen(['shutdown', '-r', '+1'])
                elif action == 'lock':
                    if system == 'Windows':
                        subprocess.Popen(['rundll32.exe', 'user32.dll,LockWorkStation'])
                    elif system == 'Darwin':
                        subprocess.Popen(['/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession', '-suspend'])
                    else:
                        # Try multiple lock commands for Linux
                        lock_commands = [
                            ['gnome-screensaver-command', '--lock'],
                            ['xdg-screensaver', 'lock'],
                            ['loginctl', 'lock-session'],
                            ['dm-tool', 'lock']
                        ]
                        for cmd in lock_commands:
                            try:
                                subprocess.Popen(cmd)
                                break
                            except:
                                continue
                elif action == 'taskmanager':
                    if system == 'Windows':
                        subprocess.Popen(['taskmgr.exe'])
                    elif system == 'Darwin':
                        subprocess.Popen(['open', '-a', 'Activity Monitor'])
                    else:
                        # Try common system monitors for Linux
                        monitor_commands = [
                            ['gnome-system-monitor'],
                            ['ksysguard'],
                            ['mate-system-monitor'],
                            ['xfce4-taskmanager'],
                            ['htop']
                        ]
                        for cmd in monitor_commands:
                            try:
                                subprocess.Popen(cmd)
                                break
                            except:
                                continue
                elif action == 'sleep':
                    if system == 'Windows':
                        subprocess.Popen(['rundll32.exe', 'powrprof.dll,SetSuspendState', '0,1,0'])
                    elif system == 'Darwin':
                        subprocess.Popen(['pmset', 'sleepnow'])
                    else:
                        subprocess.Popen(['systemctl', 'suspend'])
                
                return {'status': 'success'}
            
            elif cmd_type == 'scroll':
                clicks = command_data.get('clicks', 5)
                pyautogui.scroll(clicks)
                return {'status': 'success'}
            
            elif cmd_type == 'start_stream':
                try:
                    quality = command_data.get('quality', 50)
                    scale = command_data.get('scale', 0.5)
                    fps = command_data.get('fps', 30)
                    
                    # Store stream settings for this client
                    client_id = id(threading.current_thread())
                    self.streaming_clients[client_id] = {
                        'active': True,
                        'quality': quality,
                        'scale': scale,
                        'fps': fps,
                        'last_frame_time': 0
                    }
                    
                    self.logger.info(f"Started MJPEG stream for client {client_id}: {fps}fps, quality={quality}, scale={scale}")
                    
                    return {
                        'status': 'success',
                        'message': 'Stream started',
                        'stream_id': client_id
                    }
                except Exception as e:
                    return {'status': 'error', 'message': f'Failed to start stream: {str(e)}'}
            
            elif cmd_type == 'stop_stream':
                try:
                    client_id = id(threading.current_thread())
                    if client_id in self.streaming_clients:
                        self.streaming_clients[client_id]['active'] = False
                        del self.streaming_clients[client_id]
                        self.logger.info(f"Stopped stream for client {client_id}")
                    
                    return {'status': 'success', 'message': 'Stream stopped'}
                except Exception as e:
                    return {'status': 'error', 'message': f'Failed to stop stream: {str(e)}'}
            
            elif cmd_type == 'get_stream_frame':
                try:
                    from PIL import Image
                    
                    client_id = id(threading.current_thread())
                    
                    # Get stream settings
                    if client_id not in self.streaming_clients:
                        return {'status': 'error', 'message': 'Stream not started'}
                    
                    settings = self.streaming_clients[client_id]
                    
                    # FPS throttling
                    current_time = time.time()
                    min_frame_interval = 1.0 / settings['fps']
                    time_since_last = current_time - settings['last_frame_time']
                    
                    if time_since_last < min_frame_interval:
                        # Return empty frame to maintain connection
                        return {
                            'status': 'throttled',
                            'wait': min_frame_interval - time_since_last
                        }
                    
                    settings['last_frame_time'] = current_time
                    
                    # Capture and encode frame
                    screenshot = pyautogui.screenshot()
                    original_width = screenshot.width
                    original_height = screenshot.height
                    
                    # Resize if needed
                    if settings['scale'] < 1.0:
                        new_size = (int(screenshot.width * settings['scale']), 
                                   int(screenshot.height * settings['scale']))
                        screenshot = screenshot.resize(new_size, Image.Resampling.BILINEAR)
                    
                    # Encode as JPEG
                    buffer = BytesIO()
                    screenshot.save(buffer, format='JPEG', quality=settings['quality'], optimize=False)
                    buffer.seek(0)
                    img_bytes = buffer.read()
                    
                    # Send as binary with length prefix
                    return {
                        'status': 'success',
                        'frame_size': len(img_bytes),
                        'image': base64.b64encode(img_bytes).decode('utf-8'),
                        'width': screenshot.width,
                        'height': screenshot.height,
                        'original_width': original_width,
                        'original_height': original_height,
                        'timestamp': current_time
                    }
                    
                except Exception as e:
                    return {'status': 'error', 'message': f'Frame capture failed: {str(e)}'}
            
            elif cmd_type == 'screenshot':
                try:
                    import io
                    from PIL import Image
                    
                    quality = command_data.get('quality', 30)
                    scale = command_data.get('scale', 0.5)
                    
                    # Take screenshot
                    screenshot = pyautogui.screenshot()
                    original_width = screenshot.width
                    original_height = screenshot.height
                    
                    # Resize if needed (use faster NEAREST for real-time preview)
                    if scale < 1.0:
                        new_size = (int(screenshot.width * scale), int(screenshot.height * scale))
                        # Use NEAREST for speed, or BILINEAR for balance
                        resize_method = Image.Resampling.BILINEAR if scale >= 0.5 else Image.Resampling.NEAREST
                        screenshot = screenshot.resize(new_size, resize_method)
                    
                    # Convert to JPEG with specified quality
                    buffer = io.BytesIO()
                    screenshot.save(buffer, format='JPEG', quality=quality, optimize=False)  # optimize=False for speed
                    buffer.seek(0)
                    
                    img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
                    
                    return {
                        'status': 'success',
                        'image': img_base64,
                        'width': screenshot.width,
                        'height': screenshot.height,
                        'original_width': original_width,
                        'original_height': original_height,
                        'scale': scale
                    }
                except Exception as e:
                    return {'status': 'error', 'message': f'Screenshot failed: {str(e)}'}
            
            elif cmd_type == 'click_at_position':
                try:
                    x = command_data.get('x', 0)
                    y = command_data.get('y', 0)
                    button = command_data.get('button', 'left')
                    clicks = command_data.get('clicks', 1)
                    
                    pyautogui.click(x, y, button=button, clicks=clicks)
                    click_type = 'Double-clicked' if clicks == 2 else 'Clicked'
                    return {'status': 'success', 'message': f'{click_type} at ({x}, {y})'}
                except Exception as e:
                    return {'status': 'error', 'message': f'Click failed: {str(e)}'}
            
            elif cmd_type == 'hotkey':
                # Handle hotkey combinations (for gestures like zoom)
                try:
                    keys = command_data.get('keys', [])
                    if keys:
                        pyautogui.hotkey(*keys)
                        return {'status': 'success', 'message': f'Hotkey: {"+".join(keys)}'}
                    return {'status': 'error', 'message': 'No keys specified'}
                except Exception as e:
                    return {'status': 'error', 'message': f'Hotkey failed: {str(e)}'}
            
            else:
                return {'status': 'error', 'message': 'Unknown command type'}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def handle_client(self, client_socket, address):
        self.logger.info(f"New connection from {address}")
        self.clients.append(client_socket)
        
        # Set socket options for better performance
        try:
            client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Disable Nagle's algorithm
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1048576)  # 1MB send buffer
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1048576)  # 1MB receive buffer
            client_socket.settimeout(10.0)  # 10 second timeout
        except Exception as e:
            self.logger.warning(f"Could not set socket options: {e}")
        
        buffer = ""
        
        try:
            while self.running:
                try:
                    data = client_socket.recv(65536)
                    if not data:
                        break
                except socket.timeout:
                    continue  # Continue on timeout, don't break
                except Exception as e:
                    self.logger.error(f"Receive error: {e}")
                    break
                
                buffer += data.decode('utf-8')
                
                while '\n' in buffer:
                    try:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        
                        if not line:
                            continue
                        
                        command = json.loads(line)
                        cmd_type = command.get('type')
                        
                        if cmd_type not in ['mouse_move', 'click_at_position']:
                            self.logger.info(f"Received command: {cmd_type}")
                        
                        response = self.execute_command(command)
                        
                        if cmd_type not in ['mouse_move', 'scroll', 'click_at_position']:
                            response_json = json.dumps(response) + '\n'
                            response_bytes = response_json.encode('utf-8')
                            try:
                                client_socket.sendall(response_bytes)
                            except BrokenPipeError:
                                self.logger.error("Broken pipe - client disconnected")
                                break
                            except Exception as e:
                                self.logger.error(f"Send error: {e}")
                                break
                        
                    except json.JSONDecodeError as e:
                        self.logger.error(f"JSON decode error: {e}")
                        continue
                    except Exception as e:
                        self.logger.error(f"Error processing command: {e}")
                        error_response = {'status': 'error', 'message': str(e)}
                        try:
                            client_socket.send((json.dumps(error_response) + '\n').encode('utf-8'))
                        except:
                            pass
                        continue
                    
        except Exception as e:
            self.logger.error(f"Error handling client {address}: {e}")
        finally:
            if client_socket in self.clients:
                self.clients.remove(client_socket)
            try:
                client_socket.close()
            except:
                pass
            self.logger.info(f"Connection closed: {address}")
    
    def start(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Optimize socket buffers for high-frequency data
            try:
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2097152)  # 2MB send buffer
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2097152)  # 2MB receive buffer
            except Exception as e:
                self.logger.warning(f"Could not set server socket buffers: {e}")
            
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            
            self.logger.info(f"Server started on {self.host}:{self.port}")
            
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            self.logger.info(f"Local IP: {local_ip}")
            
            while self.running:
                client_socket, address = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
        except KeyboardInterrupt:
            self.logger.info("Server shutting down...")
        except Exception as e:
            self.logger.error(f"Server error: {e}")
        finally:
            self.stop()
    
    def stop(self):
        self.running = False
        for client in self.clients:
            client.close()
        if self.server_socket:
            self.server_socket.close()
        self.logger.info("Server stopped")

if __name__ == '__main__':
    # Install required packages if not available
    try:
        import pyautogui
        import psutil
        from PIL import Image
    except ImportError:
        print("Installing required packages...")
        import subprocess
        packages = ['pyautogui', 'psutil', 'pillow']
        for package in packages:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            except:
                pass
    
    server = LaptopControlServer()
    server.start()
