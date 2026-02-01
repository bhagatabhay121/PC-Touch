"""
Advanced KivyMD Mobile Remote Control App - With File Transfer
Features: File Transfer, Preview, Keyboard, Apps
Install: pip install kivy kivymd pillow
"""

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.button import MDIconButton, MDFillRoundFlatButton, MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import TwoLineListItem, ThreeLineListItem, MDList, OneLineListItem, OneLineAvatarIconListItem, OneLineIconListItem
from kivymd.uix.scrollview import MDScrollView
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.animation import Animation
from kivy.graphics import Color, Rectangle
from kivy.uix.image import Image as KivyImage
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
import socket
import json
import threading
import time
import base64
import os


class GradientWidget(Widget):
    """Custom widget for gradient backgrounds"""
    
    def __init__(self, colors=None, **kwargs):
        super().__init__(**kwargs)
        self.colors = colors or [[0.05, 0.1, 0.2, 1], [0.15, 0.05, 0.25, 1]]
        self.bind(size=self.update_gradient, pos=self.update_gradient)
        Clock.schedule_once(lambda dt: self.update_gradient(), 0.1)
    
    def update_gradient(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            steps = 50
            for i in range(steps):
                t = i / steps
                r = self.colors[0][0] + (self.colors[1][0] - self.colors[0][0]) * t
                g = self.colors[0][1] + (self.colors[1][1] - self.colors[0][1]) * t
                b = self.colors[0][2] + (self.colors[1][2] - self.colors[0][2]) * t
                a = self.colors[0][3] + (self.colors[1][3] - self.colors[0][3]) * t
                
                Color(r, g, b, a)
                Rectangle(
                    pos=(self.x, self.y + self.height * t),
                    size=(self.width, self.height / steps + 2)
                )


class ConnectionScreen(MDScreen):
    """Connection screen"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'connection'
        self.build_ui()
    
    def build_ui(self):
        main_layout = FloatLayout()
        gradient = GradientWidget(colors=[[0.02, 0.05, 0.12, 1], [0.08, 0.02, 0.18, 1]])
        main_layout.add_widget(gradient)
        
        content = MDBoxLayout(orientation='vertical', padding=dp(20), spacing=dp(30))
        content.add_widget(Widget(size_hint_y=0.2))
        
        title_box = MDBoxLayout(orientation='vertical', size_hint_y=None, height=dp(100), spacing=dp(10))
        
        title = MDLabel(
            text='REMOTE CONTROL',
            halign='center',
            font_style='H4',
            theme_text_color='Custom',
            text_color=[0.9, 0.95, 1, 1],
            bold=True
        )
        title_box.add_widget(title)
        
        subtitle = MDLabel(
            text='Control & Transfer Files',
            halign='center',
            font_style='Body1',
            theme_text_color='Custom',
            text_color=[0.5, 0.6, 0.8, 0.9]
        )
        title_box.add_widget(subtitle)
        content.add_widget(title_box)
        
        card = MDCard(
            orientation='vertical',
            padding=dp(30),
            spacing=dp(25),
            size_hint=(1, None),
            height=dp(380),
            md_bg_color=[0.08, 0.1, 0.18, 0.95],
            radius=[dp(25)]
        )
        
        self.ip_field = MDTextField(
            hint_text='IP Address',
            text='192.168.1.100',
            mode='rectangle',
            size_hint_y=None,
            height=dp(60)
        )
        card.add_widget(self.ip_field)
        
        self.port_field = MDTextField(
            hint_text='Port',
            text='5555',
            mode='rectangle',
            size_hint_y=None,
            height=dp(60)
        )
        card.add_widget(self.port_field)
        
        self.status_label = MDLabel(
            text='● Disconnected',
            halign='center',
            theme_text_color='Custom',
            text_color=[0.8, 0.3, 0.3, 1],
            size_hint_y=None,
            height=dp(35)
        )
        card.add_widget(self.status_label)
        
        self.connect_btn = MDFillRoundFlatButton(
            text='CONNECT',
            size_hint=(1, None),
            height=dp(50),
            md_bg_color=[0.25, 0.55, 0.95, 1]
        )
        self.connect_btn.bind(on_release=self.connect_to_server)
        card.add_widget(self.connect_btn)
        
        content.add_widget(card)
        content.add_widget(Widget())
        
        main_layout.add_widget(content)
        self.add_widget(main_layout)
    
    def connect_to_server(self, instance):
        ip = self.ip_field.text.strip()
        port = self.port_field.text.strip()
        
        if not ip or not port:
            return
        
        try:
            port = int(port)
        except ValueError:
            return
        
        self.connect_btn.disabled = True
        self.connect_btn.text = 'CONNECTING...'
        self.status_label.text = '● Connecting...'
        self.status_label.text_color = [0.9, 0.7, 0.3, 1]
        
        threading.Thread(target=self.do_connect, args=(ip, port), daemon=True).start()
    
    def do_connect(self, ip, port):
        app = MDApp.get_running_app()
        
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(10)  # Increase timeout to 10 seconds
            
            # Try to connect
            try:
                client_socket.connect((ip, port))
            except socket.timeout:
                raise Exception("Connection timed out. Check if server is running.")
            except ConnectionRefusedError:
                raise Exception("Connection refused. Is the server running on the laptop?")
            except OSError as e:
                if "Network is unreachable" in str(e):
                    raise Exception("Network unreachable. Check WiFi connection.")
                raise Exception(f"Connection failed: {str(e)}")
            
            app.client_socket = client_socket
            app.server_ip = ip
            app.server_port = port
            
            # Test the connection with a simple command
            cmd = json.dumps({'type': 'get_system_info'}) + '\n'
            client_socket.send(cmd.encode('utf-8'))
            
            # Wait for response with timeout
            client_socket.settimeout(5)
            response = client_socket.recv(4096).decode('utf-8')
            
            if not response:
                raise Exception("No response from server")
            
            data = json.loads(response.strip())
            
            Clock.schedule_once(lambda dt: self.on_connect_success(data), 0)
            
        except json.JSONDecodeError:
            error_msg = "Invalid response from server"
            Clock.schedule_once(lambda dt: self.on_connect_error(error_msg), 0)
        except Exception as e:
            error_msg = str(e)
            Clock.schedule_once(lambda dt: self.on_connect_error(error_msg), 0)
            # Close socket on error
            try:
                if 'client_socket' in locals():
                    client_socket.close()
            except:
                pass
    
    def on_connect_success(self, system_info):
        self.status_label.text = '● Connected'
        self.status_label.text_color = [0.3, 0.9, 0.4, 1]
        self.connect_btn.text = 'CONNECTED ✓'
        self.connect_btn.md_bg_color = [0.2, 0.8, 0.3, 1]
        
        Clock.schedule_once(lambda dt: self.switch_to_control(system_info), 1)
    
    def on_connect_error(self, error_msg):
        self.connect_btn.disabled = False
        self.connect_btn.text = 'CONNECT'
        self.connect_btn.md_bg_color = [0.25, 0.55, 0.95, 1]
        self.status_label.text = '● Disconnected'
        self.status_label.text_color = [0.8, 0.3, 0.3, 1]
        
        # Show error dialog
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton
        
        if not hasattr(self, 'error_dialog') or not self.error_dialog:
            self.error_dialog = MDDialog(
                title="Connection Failed",
                text=error_msg,
                buttons=[
                    MDFlatButton(
                        text="OK",
                        on_release=lambda x: self.error_dialog.dismiss()
                    )
                ]
            )
        else:
            self.error_dialog.text = error_msg
        
        self.error_dialog.open()
    
    def switch_to_control(self, system_info):
        app = MDApp.get_running_app()
        control_screen = app.root.get_screen('control')
        control_screen.set_system_info(system_info)
        app.root.current = 'control'


class ControlScreen(MDScreen):
    """Main control screen with File Transfer"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'control'
        self.preview_active = False
        self.stream_active = False
        self.stream_id = None
        self.original_screen_width = 1920
        self.original_screen_height = 1080
        self.system_info = {}
        self.preview_image = None
        self.selected_file = None
        self.active_touches = {}
        self.transfer_progress = 0
        self.fullscreen_mode = False
        self.screen_rotation = 0  # 0, 90, 180, 270
        
        # FPS Quality presets: (fps, quality, scale, name)
        self.fps_presets = [
            (60, 60, 0.4, '60 FPS'),  # 60 FPS - Ultra smooth, lower quality
            (30, 70, 0.6, '30 FPS'),  # 30 FPS - Balanced (default)
            (15, 85, 0.8, '15 FPS'),  # 15 FPS - High quality
        ]
        self.current_fps_preset = 1  # Start with 30 FPS (balanced)
        
        self.build_ui()
    
    def build_ui(self):
        self.main_layout = FloatLayout()
        gradient = GradientWidget(colors=[[0.01, 0.03, 0.1, 1], [0.05, 0.01, 0.15, 1]])
        self.main_layout.add_widget(gradient)
        
        self.content_container = MDBoxLayout(orientation='vertical')
        
        top_bar = self.create_top_bar()
        self.content_container.add_widget(top_bar)
        
        tab_bar = self.create_tab_bar()
        self.content_container.add_widget(tab_bar)
        
        self.content_area = MDBoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        self.content_container.add_widget(self.content_area)
        self.main_layout.add_widget(self.content_container)
        self.add_widget(self.main_layout)
        
        Clock.schedule_once(lambda dt: self.show_preview(), 0.1)
    
    def create_top_bar(self):
        top_bar = MDCard(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(65),
            padding=[dp(12), dp(8)],
            spacing=dp(10),
            md_bg_color=[0.06, 0.08, 0.14, 0.95],
            radius=[0, 0, dp(18), dp(18)]
        )
        
        back_btn = MDIconButton(
            icon='arrow-left',
            theme_text_color='Custom',
            text_color=[0.4, 0.7, 1, 1],
            on_release=self.go_back
        )
        top_bar.add_widget(back_btn)
        
        info_layout = MDBoxLayout(orientation='vertical', spacing=dp(2))
        
        self.hostname_label = MDLabel(
            text='Computer',
            font_style='Subtitle1',
            theme_text_color='Custom',
            text_color=[0.95, 0.97, 1, 1],
            bold=True
        )
        info_layout.add_widget(self.hostname_label)
        
        self.status_label = MDLabel(
            text='● Connected',
            font_style='Caption',
            theme_text_color='Custom',
            text_color=[0.3, 0.9, 0.4, 1]
        )
        info_layout.add_widget(self.status_label)
        
        top_bar.add_widget(info_layout)
        top_bar.add_widget(Widget())
        
        return top_bar
    
    def create_tab_bar(self):
        tab_bar = MDCard(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(55),
            padding=dp(6),
            spacing=dp(6),
            md_bg_color=[0.05, 0.06, 0.12, 0.9],
            radius=[dp(14)]
        )
        
        self.tab_buttons = []
        
        tabs = [
            ('monitor', 'Preview', self.show_preview),
            ('file-upload', 'Files', self.show_file_transfer),
            ('keyboard', 'Keyboard', self.show_keyboard),
            ('apps', 'Apps', self.show_apps),
        ]
        
        for icon, text, callback in tabs:
            btn = MDFillRoundFlatButton(
                text=text,
                icon=icon,
                size_hint_x=1,
                md_bg_color=[0.1, 0.12, 0.18, 1],
                text_color=[0.6, 0.65, 0.75, 1],
                font_size=dp(13)
            )
            btn.bind(on_release=lambda x, cb=callback: self.switch_tab(cb))
            tab_bar.add_widget(btn)
            self.tab_buttons.append(btn)
        
        self.tab_buttons[0].md_bg_color = [0.25, 0.55, 0.95, 1]
        self.tab_buttons[0].text_color = [1, 1, 1, 1]
        
        return tab_bar
    
    def switch_tab(self, callback):
        # Exit fullscreen if active
        if hasattr(self, 'fullscreen_mode') and self.fullscreen_mode:
            # Create a dummy instance for toggle_fullscreen
            class DummyInstance:
                pass
            self.toggle_fullscreen(DummyInstance())
        
        for i, btn in enumerate(self.tab_buttons):
            if callback == [self.show_preview, self.show_file_transfer, self.show_keyboard, self.show_apps][i]:
                btn.md_bg_color = [0.25, 0.55, 0.95, 1]
                btn.text_color = [1, 1, 1, 1]
            else:
                btn.md_bg_color = [0.1, 0.12, 0.18, 1]
                btn.text_color = [0.6, 0.65, 0.75, 1]
        
        callback()
    
    def show_file_transfer(self):
        """Show simplified file transfer interface - Browse PC Files only"""
        self.content_area.clear_widgets()
        
        transfer_card = MDCard(
            orientation='vertical',
            padding=dp(15),
            spacing=dp(15),
            md_bg_color=[0.06, 0.08, 0.14, 0.92],
            radius=[dp(18)]
        )
        
        # Header
        header = MDLabel(
            text='File Manager',
            font_style='H6',
            size_hint_y=None,
            height=dp(35),
            theme_text_color='Custom',
            text_color=[0.8, 0.85, 0.95, 1]
        )
        transfer_card.add_widget(header)
        
        # File Browser Button - ONLY OPTION
        browse_btn = MDFillRoundFlatButton(
            text='📂 Browse PC Files',
            icon='folder-open',
            size_hint=(1, None),
            height=dp(60),
            md_bg_color=[0.25, 0.55, 0.95, 1],
            font_size=dp(16),
            on_release=self.open_file_browser
        )
        transfer_card.add_widget(browse_btn)
        
        # Info text
        info_label = MDLabel(
            text='Browse and navigate through files on your PC',
            font_style='Caption',
            halign='center',
            size_hint_y=None,
            height=dp(40),
            theme_text_color='Custom',
            text_color=[0.5, 0.6, 0.7, 1]
        )
        transfer_card.add_widget(info_label)
        
        self.content_area.add_widget(transfer_card)
    
    def open_file_browser(self, instance):
        """Open the file browser screen"""
        app = MDApp.get_running_app()
        app.root.current = 'filemanager'
    
    def show_preview(self):
        """Show full screen preview"""
        self.content_area.clear_widgets()
        
        preview_layout = FloatLayout()
        
        preview_card = MDCard(
            md_bg_color=[0.02, 0.03, 0.08, 0.95],
            radius=[dp(18)],
            padding=dp(8)
        )
        
        inner_container = MDBoxLayout(orientation='vertical', spacing=dp(8))
        
        control_bar = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10),
            padding=[dp(8), 0]
        )
        
        self.preview_btn = MDFillRoundFlatButton(
            text='Start Preview',
            icon='play',
            size_hint_x=0.5,
            md_bg_color=[0.2, 0.7, 0.4, 1],
            on_release=self.toggle_preview
        )
        control_bar.add_widget(self.preview_btn)
        
        # Rotate button
        self.rotate_btn = MDIconButton(
            icon='screen-rotation',
            theme_text_color='Custom',
            text_color=[0.9, 0.6, 0.3, 1],
            on_release=self.rotate_screen
        )
        control_bar.add_widget(self.rotate_btn)
        
        # Fullscreen button
        self.fullscreen_btn = MDIconButton(
            icon='fullscreen',
            theme_text_color='Custom',
            text_color=[0.6, 0.4, 0.9, 1],
            on_release=self.toggle_fullscreen
        )
        control_bar.add_widget(self.fullscreen_btn)
        
        refresh_btn = MDIconButton(
            icon='refresh',
            theme_text_color='Custom',
            text_color=[0.4, 0.7, 1, 1],
            on_release=lambda x: self.fetch_stream_frame() if self.preview_active and self.stream_active else None
        )
        control_bar.add_widget(refresh_btn)
        
        # FPS Quality selector
        self.fps_btn = MDIconButton(
            icon='speedometer',
            theme_text_color='Custom',
            text_color=[1, 0.8, 0.2, 1],
            on_release=self.cycle_fps_quality
        )
        control_bar.add_widget(self.fps_btn)
        
        inner_container.add_widget(control_bar)
        
        self.preview_container = MDCard(
            md_bg_color=[0.01, 0.02, 0.05, 0.95],
            radius=[dp(12)]
        )
        
        self.preview_image = KivyImage(
            allow_stretch=True,
            keep_ratio=True
        )
        self.preview_container.add_widget(self.preview_image)
        
        self.preview_container.bind(
            on_touch_down=self.on_preview_touch_down,
            on_touch_up=self.on_preview_touch_up
        )
        
        inner_container.add_widget(self.preview_container)
        
        status_bar = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            padding=[dp(12), 0]
        )
        
        self.preview_status = MDLabel(
            text='Tap Start to begin',
            font_style='Caption'
        )
        status_bar.add_widget(self.preview_status)
        status_bar.add_widget(Widget())
        
        self.preview_resolution = MDLabel(
            text='',
            font_style='Caption',
            halign='right'
        )
        status_bar.add_widget(self.preview_resolution)
        
        inner_container.add_widget(status_bar)
        
        preview_card.add_widget(inner_container)
        preview_layout.add_widget(preview_card)
        
        # Store references for fullscreen mode
        self.preview_control_bar = control_bar
        self.preview_status_bar = status_bar
        self.preview_inner_container = inner_container
        self.preview_card_widget = preview_card
        self.preview_layout_widget = preview_layout
        
        # Create and add fullscreen overlay
        self.fullscreen_overlay = self.create_fullscreen_overlay()
        preview_layout.add_widget(self.fullscreen_overlay)
        
        self.content_area.add_widget(preview_layout)
    
    def create_fullscreen_overlay(self):
        """Create the fullscreen overlay with minimal controls"""
        fullscreen_overlay = FloatLayout()
        fullscreen_overlay.opacity = 0
        
        # Back button (top-left)
        back_btn = MDIconButton(
            icon='arrow-left',
            theme_text_color='Custom',
            text_color=[1, 1, 1, 0.9],
            pos_hint={'x': 0.02, 'top': 0.98},
            size_hint=(None, None),
            size=(dp(48), dp(48)),
            md_bg_color=[0.1, 0.1, 0.1, 0.7]
        )
        back_btn.bind(on_release=lambda x: self.toggle_fullscreen(x))
        fullscreen_overlay.add_widget(back_btn)
        
        # RIGHT SIDE CONTROLS - Individual buttons without background box
        
        # --- WINDOW CONTROLS SECTION (Top Right) ---
        
        # Minimize button
        minimize_btn = MDIconButton(
            icon='window-minimize',
            theme_text_color='Custom',
            text_color=[1, 0.85, 0.15, 1],
            md_bg_color=[0.15, 0.15, 0.2, 0.8],
            icon_size=dp(28),
            pos_hint={'right': 0.98, 'top': 0.85},
            size_hint=(None, None),
            size=(dp(55), dp(55)),
            on_release=self.minimize_window
        )
        fullscreen_overlay.add_widget(minimize_btn)
        
        # Maximize/Restore button
        self.maximize_btn = MDIconButton(
            icon='window-maximize',
            theme_text_color='Custom',
            text_color=[0.15, 1, 0.25, 1],
            md_bg_color=[0.15, 0.15, 0.2, 0.8],
            icon_size=dp(28),
            pos_hint={'right': 0.98, 'top': 0.75},
            size_hint=(None, None),
            size=(dp(55), dp(55)),
            on_release=self.maximize_window
        )
        fullscreen_overlay.add_widget(self.maximize_btn)
        
        # Close button
        close_btn = MDIconButton(
            icon='window-close',
            theme_text_color='Custom',
            text_color=[1, 0.15, 0.15, 1],
            md_bg_color=[0.15, 0.15, 0.2, 0.8],
            icon_size=dp(28),
            pos_hint={'right': 0.98, 'top': 0.65},
            size_hint=(None, None),
            size=(dp(55), dp(55)),
            on_release=self.close_window
        )
        fullscreen_overlay.add_widget(close_btn)
        
        # --- PAGE NAVIGATION SECTION (Center Right) ---
        
        # Page Up button
        page_up_btn = MDIconButton(
            icon='chevron-up',
            theme_text_color='Custom',
            text_color=[1, 1, 1, 0.9],
            size_hint=(None, None),
            size=(dp(55), dp(55)),
            pos_hint={'right': 0.98, 'center_y': 0.55},
            md_bg_color=[0.1, 0.1, 0.1, 0.7],
            icon_size=dp(32)
        )
        page_up_btn.bind(on_release=lambda x: self.send_key('pageup'))
        fullscreen_overlay.add_widget(page_up_btn)
        
        # Page Down button
        page_down_btn = MDIconButton(
            icon='chevron-down',
            theme_text_color='Custom',
            text_color=[1, 1, 1, 0.9],
            size_hint=(None, None),
            size=(dp(55), dp(55)),
            pos_hint={'right': 0.98, 'center_y': 0.45},
            md_bg_color=[0.1, 0.1, 0.1, 0.7],
            icon_size=dp(32)
        )
        page_down_btn.bind(on_release=lambda x: self.send_key('pagedown'))
        fullscreen_overlay.add_widget(page_down_btn)
        
        return fullscreen_overlay
    
    def minimize_window(self, instance):
        """Minimize the active window on the laptop"""
        app = MDApp.get_running_app()
        
        # Visual feedback
        instance.md_bg_color = [0.3, 0.25, 0.1, 1]
        Clock.schedule_once(
            lambda dt: setattr(instance, 'md_bg_color', [0.2, 0.18, 0.08, 0.95]), 
            0.2
        )
        
        def _minimize():
            try:
                if hasattr(app, 'client_socket') and app.client_socket:
                    cmd = json.dumps({'type': 'hotkey', 'keys': ['win', 'down']}) + '\n'
                    app.client_socket.send(cmd.encode('utf-8'))
            except Exception as e:
                print(f"Minimize error: {e}")
        
        threading.Thread(target=_minimize, daemon=True).start()
    
    def maximize_window(self, instance):
        """Maximize/Restore the active window on the laptop"""
        app = MDApp.get_running_app()
        
        # Visual feedback
        instance.md_bg_color = [0.1, 0.3, 0.1, 1]
        Clock.schedule_once(
            lambda dt: setattr(instance, 'md_bg_color', [0.08, 0.2, 0.08, 0.95]), 
            0.2
        )
        
        # Toggle icon
        if instance.icon == 'window-maximize':
            instance.icon = 'window-restore'
        else:
            instance.icon = 'window-maximize'
        
        def _maximize():
            try:
                if hasattr(app, 'client_socket') and app.client_socket:
                    # Windows: Win+Up maximizes, Alt+Space then X also works
                    cmd = json.dumps({'type': 'hotkey', 'keys': ['win', 'up']}) + '\n'
                    app.client_socket.send(cmd.encode('utf-8'))
            except Exception as e:
                print(f"Maximize error: {e}")
        
        threading.Thread(target=_maximize, daemon=True).start()
    
    def close_window(self, instance):
        """Close the active window on the laptop"""
        app = MDApp.get_running_app()
        
        # Visual feedback
        instance.md_bg_color = [0.4, 0.1, 0.1, 1]
        Clock.schedule_once(
            lambda dt: setattr(instance, 'md_bg_color', [0.2, 0.08, 0.08, 0.95]), 
            0.2
        )
        
        def _close():
            try:
                if hasattr(app, 'client_socket') and app.client_socket:
                    # Alt+F4 is universal for closing windows
                    cmd = json.dumps({'type': 'hotkey', 'keys': ['alt', 'F4']}) + '\n'
                    app.client_socket.send(cmd.encode('utf-8'))
            except Exception as e:
                print(f"Close window error: {e}")
        
        threading.Thread(target=_close, daemon=True).start()
    
    def rotate_screen(self, instance):
        """Rotate the device screen orientation using Android native code and enter fullscreen"""
        try:
            # Try to use Android's native orientation control
            from android import activity
            from jnius import autoclass
            
            # Get the current activity
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity_instance = PythonActivity.mActivity
            
            # Screen orientation constants
            # 0 = PORTRAIT, 1 = LANDSCAPE, 6 = REVERSE_PORTRAIT, 8 = REVERSE_LANDSCAPE
            # -1 = SENSOR (auto-rotate)
            
            # Cycle through orientations
            self.screen_rotation = (self.screen_rotation + 1) % 4
            
            orientation_map = {
                0: 1,   # LANDSCAPE
                1: 6,   # REVERSE_PORTRAIT  
                2: 8,   # REVERSE_LANDSCAPE
                3: 0    # PORTRAIT
            }
            
            orientation = orientation_map[self.screen_rotation]
            activity_instance.setRequestedOrientation(orientation)
            
        except Exception as e:
            # Fallback for non-Android or if it fails
            print(f"Rotation error: {e}")
            # Just toggle between portrait and landscape using Kivy's Window
            from kivy.core.window import Window
            if Window.width > Window.height:
                # Currently landscape, switch to portrait
                Window.rotation = 90
            else:
                # Currently portrait, switch to landscape  
                Window.rotation = 0
        
        # Automatically enter fullscreen after rotation
        if not self.fullscreen_mode:
            # Small delay to let rotation complete
            Clock.schedule_once(lambda dt: self.toggle_fullscreen(instance), 0.3)
    
    def toggle_fullscreen(self, instance):
        """Toggle fullscreen mode for preview"""
        if not hasattr(self, 'fullscreen_overlay'):
            return
            
        self.fullscreen_mode = not self.fullscreen_mode
        
        if self.fullscreen_mode:
            # Enter fullscreen - hide everything and make it like YouTube
            self.fullscreen_btn.icon = 'fullscreen-exit'
            
            # Hide Android system bars for true fullscreen
            try:
                from android import activity
                from jnius import autoclass
                
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                activity_instance = PythonActivity.mActivity
                View = autoclass('android.view.View')
                
                # Set fullscreen immersive mode
                window = activity_instance.getWindow()
                decorView = window.getDecorView()
                
                # SYSTEM_UI_FLAG_FULLSCREEN | SYSTEM_UI_FLAG_HIDE_NAVIGATION | 
                # SYSTEM_UI_FLAG_IMMERSIVE_STICKY | SYSTEM_UI_FLAG_LAYOUT_STABLE |
                # SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION | SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                uiOptions = (View.SYSTEM_UI_FLAG_FULLSCREEN | 
                           View.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
                           View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY |
                           View.SYSTEM_UI_FLAG_LAYOUT_STABLE |
                           View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION |
                           View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN)
                
                decorView.setSystemUiVisibility(uiOptions)
            except Exception as e:
                print(f"Failed to set immersive mode: {e}")
            
            # Hide the top bar and tab bar completely
            if hasattr(self, 'content_container'):
                # Get the top bar (first child) and tab bar (second child)
                children = self.content_container.children
                if len(children) >= 3:
                    # Hide top bar
                    children[2].opacity = 0
                    children[2].disabled = True
                    children[2].size_hint_y = None
                    children[2].height = 0
                    
                    # Hide tab bar
                    children[1].opacity = 0
                    children[1].disabled = True
                    children[1].size_hint_y = None
                    children[1].height = 0
            
            # Hide all UI elements in preview
            self.preview_control_bar.opacity = 0
            self.preview_control_bar.disabled = True
            self.preview_control_bar.size_hint_y = None
            self.preview_control_bar.height = 0
            
            self.preview_status_bar.opacity = 0
            self.preview_status_bar.size_hint_y = None
            self.preview_status_bar.height = 0
            
            # Make preview card fill everything with no styling
            self.preview_card_widget.md_bg_color = [0, 0, 0, 1]
            self.preview_card_widget.radius = [0]
            self.preview_card_widget.padding = 0
            
            # Make preview container fill completely
            self.preview_container.md_bg_color = [0, 0, 0, 1]
            self.preview_container.radius = [0]
            
            # Show fullscreen overlay controls
            self.fullscreen_overlay.opacity = 1
            
        else:
            # Exit fullscreen - restore everything
            self.fullscreen_btn.icon = 'fullscreen'
            
            # Restore Android system bars
            try:
                from android import activity
                from jnius import autoclass
                
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                activity_instance = PythonActivity.mActivity
                View = autoclass('android.view.View')
                
                window = activity_instance.getWindow()
                decorView = window.getDecorView()
                
                # Clear fullscreen flags
                decorView.setSystemUiVisibility(View.SYSTEM_UI_FLAG_VISIBLE)
            except Exception as e:
                print(f"Failed to restore system UI: {e}")
            
            # Restore top bar and tab bar
            if hasattr(self, 'content_container'):
                children = self.content_container.children
                if len(children) >= 3:
                    # Restore top bar
                    children[2].opacity = 1
                    children[2].disabled = False
                    children[2].size_hint_y = None
                    children[2].height = dp(65)
                    
                    # Restore tab bar
                    children[1].opacity = 1
                    children[1].disabled = False
                    children[1].size_hint_y = None
                    children[1].height = dp(55)
            
            # Restore UI elements
            self.preview_control_bar.opacity = 1
            self.preview_control_bar.disabled = False
            self.preview_control_bar.size_hint_y = None
            self.preview_control_bar.height = dp(50)
            
            self.preview_status_bar.opacity = 1
            self.preview_status_bar.size_hint_y = None
            self.preview_status_bar.height = dp(40)
            
            # Restore styling
            self.preview_card_widget.md_bg_color = [0.02, 0.03, 0.08, 0.95]
            self.preview_card_widget.radius = [dp(18)]
            self.preview_card_widget.padding = dp(8)
            
            self.preview_container.md_bg_color = [0.01, 0.02, 0.05, 0.95]
            self.preview_container.radius = [dp(12)]
            
            # Hide fullscreen overlay
            self.fullscreen_overlay.opacity = 0
    
    def show_keyboard(self):
        self.content_area.clear_widgets()
        
        keyboard_card = MDCard(
            orientation='vertical',
            padding=dp(12),
            spacing=dp(12),
            md_bg_color=[0.06, 0.08, 0.14, 0.92],
            radius=[dp(18)]
        )
        
        input_label = MDLabel(
            text='Type Text',
            font_style='Subtitle1',
            size_hint_y=None,
            height=dp(25)
        )
        keyboard_card.add_widget(input_label)
        
        self.text_input = MDTextField(
            hint_text='Enter text to send...',
            mode='rectangle',
            size_hint_y=None,
            height=dp(100),
            multiline=True
        )
        keyboard_card.add_widget(self.text_input)
        
        send_btn = MDFillRoundFlatButton(
            text='Send Text',
            icon='send',
            pos_hint={'center_x': 0.5},
            size_hint=(None, None),
            size=(dp(200), dp(45)),
            md_bg_color=[0.25, 0.55, 0.95, 1],
            on_release=self.send_typed_text
        )
        keyboard_card.add_widget(send_btn)
        
        keys_label = MDLabel(
            text='Special Keys',
            font_style='Subtitle1',
            size_hint_y=None,
            height=dp(28)
        )
        keyboard_card.add_widget(keys_label)
        
        scroll = ScrollView(size_hint=(1, 1))
        keys_grid = MDGridLayout(
            cols=4,
            spacing=dp(8),
            size_hint_y=None,
            padding=dp(4)
        )
        keys_grid.bind(minimum_height=keys_grid.setter('height'))
        
        special_keys = [
            ('Enter', 'enter'), ('Tab', 'tab'), ('Esc', 'esc'), ('Back', 'backspace'),
            ('Delete', 'delete'), ('Home', 'home'), ('End', 'end'), ('PgUp', 'pageup'),
            ('PgDn', 'pagedown'), ('↑', 'up'), ('↓', 'down'), ('←', 'left'),
            ('→', 'right'), ('Space', 'space'), ('Ctrl+C', 'ctrl+c'), ('Ctrl+V', 'ctrl+v'),
        ]
        
        for label, key in special_keys:
            btn = MDFillRoundFlatButton(
                text=label,
                size_hint_y=None,
                height=dp(45),
                md_bg_color=[0.1, 0.15, 0.25, 0.9],
                font_size=dp(13)
            )
            btn.bind(on_release=lambda x, k=key: self.send_special_key(k))
            keys_grid.add_widget(btn)
        
        scroll.add_widget(keys_grid)
        keyboard_card.add_widget(scroll)
        
        # System Control Section
        system_label = MDLabel(
            text='System Controls',
            font_style='Subtitle1',
            size_hint_y=None,
            height=dp(30),
            theme_text_color='Custom',
            text_color=[0.9, 0.6, 0.3, 1]
        )
        keyboard_card.add_widget(system_label)
        
        system_grid = MDGridLayout(
            cols=2,
            spacing=dp(8),
            size_hint_y=None,
            height=dp(100),
            padding=dp(4)
        )
        
        # Lock button
        lock_btn = MDFillRoundFlatButton(
            text='Lock',
            icon='lock',
            size_hint_y=None,
            height=dp(45),
            md_bg_color=[0.2, 0.5, 0.9, 0.9],
            font_size=dp(13)
        )
        lock_btn.bind(on_release=lambda x: self.show_system_action_dialog('lock'))
        system_grid.add_widget(lock_btn)
        
        # Task Manager button
        taskmanager_btn = MDFillRoundFlatButton(
            text='Task Mgr',
            icon='view-list',
            size_hint_y=None,
            height=dp(45),
            md_bg_color=[0.3, 0.6, 0.8, 0.9],
            font_size=dp(13)
        )
        taskmanager_btn.bind(on_release=lambda x: self.show_system_action_dialog('taskmanager'))
        system_grid.add_widget(taskmanager_btn)
        
        # Restart button
        restart_btn = MDFillRoundFlatButton(
            text='Restart',
            icon='restart',
            size_hint_y=None,
            height=dp(45),
            md_bg_color=[0.9, 0.6, 0.2, 0.9],
            font_size=dp(13)
        )
        restart_btn.bind(on_release=lambda x: self.show_system_action_dialog('restart'))
        system_grid.add_widget(restart_btn)
        
        # Shutdown button
        shutdown_btn = MDFillRoundFlatButton(
            text='Shutdown',
            icon='power',
            size_hint_y=None,
            height=dp(45),
            md_bg_color=[0.9, 0.3, 0.3, 0.9],
            font_size=dp(13)
        )
        shutdown_btn.bind(on_release=lambda x: self.show_system_action_dialog('shutdown'))
        system_grid.add_widget(shutdown_btn)
        
        keyboard_card.add_widget(system_grid)
        
        self.content_area.add_widget(keyboard_card)
    
    def show_system_action_dialog(self, action):
        """Show confirmation dialog for system actions"""
        action_texts = {
            'lock': ('Lock Computer', 'Are you sure you want to lock the computer?', [0.2, 0.5, 0.9, 1]),
            'taskmanager': ('Task Manager', 'Open Task Manager on the computer?', [0.3, 0.6, 0.8, 1]),
            'restart': ('Restart Computer', 'Are you sure you want to restart the computer?', [0.9, 0.6, 0.2, 1]),
            'shutdown': ('Shutdown Computer', 'Are you sure you want to shutdown the computer?', [0.9, 0.3, 0.3, 1])
        }
        
        title, message, color = action_texts.get(action, ('Action', 'Confirm action?', [0.5, 0.5, 0.5, 1]))
        
        self.system_dialog = MDDialog(
            title=title,
            text=message,
            buttons=[
                MDFillRoundFlatButton(
                    text='CANCEL',
                    md_bg_color=[0.3, 0.3, 0.3, 1],
                    on_release=lambda x: self.system_dialog.dismiss()
                ),
                MDFillRoundFlatButton(
                    text='CONFIRM',
                    md_bg_color=color,
                    on_release=lambda x: self.execute_system_action(action)
                ),
            ],
        )
        self.system_dialog.open()
    
    def execute_system_action(self, action):
        """Execute the confirmed system action"""
        self.system_dialog.dismiss()
        
        app = MDApp.get_running_app()
        
        def _send():
            try:
                if hasattr(app, 'client_socket') and app.client_socket:
                    cmd = json.dumps({'type': 'system_action', 'action': action}) + '\n'
                    app.client_socket.send(cmd.encode('utf-8'))
            except Exception as e:
                print(f"System action error: {e}")
        
        threading.Thread(target=_send, daemon=True).start()
    
    def show_apps(self):
        self.content_area.clear_widgets()
        
        apps_card = MDCard(
            orientation='vertical',
            padding=dp(12),
            spacing=dp(12),
            md_bg_color=[0.06, 0.08, 0.14, 0.92],
            radius=[dp(18)]
        )
        
        header = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10)
        )
        
        apps_label = MDLabel(
            text='Applications',
            font_style='H6'
        )
        header.add_widget(apps_label)
        header.add_widget(Widget())
        
        load_btn = MDFillRoundFlatButton(
            text='Load',
            icon='reload',
            size_hint=(None, None),
            size=(dp(120), dp(40)),
            md_bg_color=[0.25, 0.55, 0.95, 1],
            on_release=self.load_applications
        )
        header.add_widget(load_btn)
        
        apps_card.add_widget(header)
        
        scroll = MDScrollView()
        self.apps_list = MDList()
        scroll.add_widget(self.apps_list)
        apps_card.add_widget(scroll)
        
        self.content_area.add_widget(apps_card)
    
    # Preview handling
    def on_preview_touch_down(self, instance, touch):
        if self.preview_active and instance.collide_point(*touch.pos):
            self.active_touches[touch.uid] = touch
            return True
        return False
    
    def on_preview_touch_up(self, instance, touch):
        if touch.uid in self.active_touches and self.preview_active:
            self.click_at_preview_position(touch.pos)
            del self.active_touches[touch.uid]
            return True
        return False
    
    def click_at_preview_position(self, pos):
        try:
            if not self.preview_image or not hasattr(self.preview_image, 'norm_image_size'):
                return
                
            img_x = pos[0] - self.preview_image.x
            img_y = pos[1] - self.preview_image.y
            
            img_width = self.preview_image.norm_image_size[0]
            img_height = self.preview_image.norm_image_size[1]
            
            x_offset = (self.preview_image.width - img_width) / 2
            y_offset = (self.preview_image.height - img_height) / 2
            
            img_x -= x_offset
            img_y -= y_offset
            
            if 0 <= img_x <= img_width and 0 <= img_y <= img_height:
                rel_x = img_x / img_width
                rel_y = 1 - (img_y / img_height)
                
                laptop_x = int(rel_x * self.original_screen_width)
                laptop_y = int(rel_y * self.original_screen_height)
                
                self.send_click_at(laptop_x, laptop_y)
                self.preview_status.text = f'Clicked at ({laptop_x}, {laptop_y})'
        except Exception as e:
            print(f"Click error: {e}")
    
    def cycle_fps_quality(self, instance):
        """Cycle through FPS quality presets"""
        self.current_fps_preset = (self.current_fps_preset + 1) % len(self.fps_presets)
        _, _, _, preset_name = self.fps_presets[self.current_fps_preset]
        
        # Update status to show current preset
        if hasattr(self, 'preview_status'):
            self.preview_status.text = f'Quality: {preset_name}'
        
        # Show toast notification
        from kivymd.toast import toast
        toast(f'Preview quality: {preset_name}')
        
        # If streaming is active, restart with new settings
        if self.stream_active and self.preview_active:
            self.stop_mjpeg_stream()
            Clock.schedule_once(lambda dt: self.start_mjpeg_stream(), 0.5)
    
    def toggle_preview(self, instance):
        if self.preview_active:
            # Stop preview and stream
            self.preview_active = False
            self.stop_mjpeg_stream()
            self.preview_btn.text = 'Start Preview'
            self.preview_btn.icon = 'play'
            self.preview_btn.md_bg_color = [0.2, 0.7, 0.4, 1]
            self.preview_status.text = 'Preview stopped'
        else:
            # Start preview and stream
            self.preview_active = True
            self.preview_btn.text = 'Stop Preview'
            self.preview_btn.icon = 'stop'
            self.preview_btn.md_bg_color = [0.9, 0.4, 0.3, 1]
            self.preview_status.text = 'Starting stream...'
            self.start_mjpeg_stream()
    
    def start_mjpeg_stream(self):
        """Start MJPEG streaming"""
        app = MDApp.get_running_app()
        fps, quality, scale, _ = self.fps_presets[self.current_fps_preset]
        
        def _start():
            try:
                if hasattr(app, 'client_socket') and app.client_socket:
                    # Send start stream command
                    cmd = json.dumps({
                        'type': 'start_stream',
                        'quality': quality,
                        'scale': scale,
                        'fps': fps
                    }) + '\n'
                    app.client_socket.send(cmd.encode('utf-8'))
                    
                    # Wait for response
                    buffer = ""
                    while '\n' not in buffer:
                        data = app.client_socket.recv(4096).decode('utf-8')
                        if not data:
                            break
                        buffer += data
                    
                    if buffer:
                        response = json.loads(buffer.strip())
                        if response.get('status') == 'success':
                            self.stream_id = response.get('stream_id')
                            self.stream_active = True
                            Clock.schedule_once(lambda dt: self._update_stream_status('Stream started'), 0)
                            # Start fetching frames
                            self.fetch_stream_frame()
                        else:
                            Clock.schedule_once(lambda dt: self._update_stream_status('Failed to start'), 0)
            except Exception as e:
                print(f"Start stream error: {e}")
                Clock.schedule_once(lambda dt: self._stop_preview_on_error(), 0)
        
        threading.Thread(target=_start, daemon=True).start()
    
    def stop_mjpeg_stream(self):
        """Stop MJPEG streaming"""
        if not self.stream_active:
            return
        
        app = MDApp.get_running_app()
        self.stream_active = False
        
        def _stop():
            try:
                if hasattr(app, 'client_socket') and app.client_socket:
                    cmd = json.dumps({'type': 'stop_stream'}) + '\n'
                    app.client_socket.send(cmd.encode('utf-8'))
            except Exception as e:
                print(f"Stop stream error: {e}")
        
        threading.Thread(target=_stop, daemon=True).start()
    
    def fetch_stream_frame(self):
        """Fetch next frame from MJPEG stream"""
        if not self.preview_active or not self.stream_active:
            return
        
        app = MDApp.get_running_app()
        
        def _fetch():
            try:
                if hasattr(app, 'client_socket') and app.client_socket:
                    # Request next frame
                    cmd = json.dumps({'type': 'get_stream_frame'}) + '\n'
                    app.client_socket.send(cmd.encode('utf-8'))
                    
                    # Set timeout
                    app.client_socket.settimeout(2.0)
                    
                    buffer = ""
                    while '\n' not in buffer:
                        data = app.client_socket.recv(65536).decode('utf-8')
                        if not data:
                            break
                        buffer += data
                    
                    if buffer:
                        response = json.loads(buffer.strip())
                        
                        if response.get('status') == 'success':
                            img_data = base64.b64decode(response['image'])
                            self.original_screen_width = response['original_width']
                            self.original_screen_height = response['original_height']
                            
                            Clock.schedule_once(
                                lambda dt: self.display_preview(img_data), 0
                            )
                        elif response.get('status') == 'throttled':
                            # Frame rate throttling, wait a bit
                            time.sleep(response.get('wait', 0.01))
                    
                    # Schedule next frame
                    if self.preview_active and self.stream_active:
                        Clock.schedule_once(lambda dt: self.fetch_stream_frame(), 0.001)
                        
            except socket.timeout:
                if self.preview_active and self.stream_active:
                    Clock.schedule_once(lambda dt: self.fetch_stream_frame(), 0.01)
            except (ConnectionResetError, BrokenPipeError):
                print("Connection lost during streaming")
                Clock.schedule_once(lambda dt: self._stop_preview_on_error(), 0)
            except Exception as e:
                print(f"Fetch frame error: {e}")
                if self.preview_active and self.stream_active:
                    Clock.schedule_once(lambda dt: self.fetch_stream_frame(), 0.05)
        
        threading.Thread(target=_fetch, daemon=True).start()
    
    def _update_stream_status(self, message):
        """Update stream status message"""
        if hasattr(self, 'preview_status'):
            fps, _, _, preset_name = self.fps_presets[self.current_fps_preset]
            self.preview_status.text = f'{message} • {preset_name}'
    
    def _stop_preview_on_error(self):
        """Stop preview due to connection error"""
        self.preview_active = False
        self.preview_btn.text = 'Start Preview'
        self.preview_btn.icon = 'play'
        self.preview_btn.md_bg_color = [0.2, 0.7, 0.4, 1]
        self.preview_status.text = 'Connection lost - Click to retry'
    
    
    def display_preview(self, img_data):
        try:
            from PIL import Image as PILImage
            from kivy.graphics.texture import Texture
            import io
            
            image = PILImage.open(io.BytesIO(img_data))
            image_data = image.tobytes()
            
            texture = Texture.create(
                size=(image.width, image.height),
                colorfmt='rgb'
            )
            texture.blit_buffer(image_data, colorfmt='rgb', bufferfmt='ubyte')
            texture.flip_vertical()
            
            self.preview_image.texture = texture
            _, _, _, preset_name = self.fps_presets[self.current_fps_preset]
            self.preview_status.text = f'Live • {preset_name} • Tap to click'
            self.preview_resolution.text = f'{self.original_screen_width}×{self.original_screen_height}'
            
        except Exception as e:
            print(f"Display error: {e}")
    
    # Communication methods
    def send_click_at(self, x, y, button='left'):
        app = MDApp.get_running_app()
        
        def _send():
            try:
                if hasattr(app, 'client_socket') and app.client_socket:
                    cmd = json.dumps({
                        'type': 'click_at_position',
                        'x': x,
                        'y': y,
                        'button': button
                    }) + '\n'
                    app.client_socket.send(cmd.encode('utf-8'))
            except:
                pass
        
        threading.Thread(target=_send, daemon=True).start()
    
    def send_key(self, key):
        app = MDApp.get_running_app()
        
        def _send():
            try:
                if hasattr(app, 'client_socket') and app.client_socket:
                    cmd = json.dumps({'type': 'key_press', 'key': key}) + '\n'
                    app.client_socket.send(cmd.encode('utf-8'))
            except:
                pass
        
        threading.Thread(target=_send, daemon=True).start()
    
    def send_special_key(self, key):
        if '+' in key:
            keys = key.split('+')
            self.send_hotkey(keys)
        else:
            self.send_key(key)
    
    def send_hotkey(self, keys):
        app = MDApp.get_running_app()
        
        def _send():
            try:
                if hasattr(app, 'client_socket') and app.client_socket:
                    cmd = json.dumps({'type': 'hotkey', 'keys': keys}) + '\n'
                    app.client_socket.send(cmd.encode('utf-8'))
            except:
                pass
        
        threading.Thread(target=_send, daemon=True).start()
    
    def send_typed_text(self, instance):
        text = self.text_input.text
        if text:
            app = MDApp.get_running_app()
            
            def _send():
                try:
                    if hasattr(app, 'client_socket') and app.client_socket:
                        cmd = json.dumps({'type': 'type_text', 'text': text}) + '\n'
                        app.client_socket.send(cmd.encode('utf-8'))
                except:
                    pass
            
            threading.Thread(target=_send, daemon=True).start()
            self.text_input.text = ''
    
    def load_applications(self, instance):
        app = MDApp.get_running_app()
        
        instance.disabled = True
        instance.text = 'Loading...'
        
        # Clear previous apps
        self.apps_list.clear_widgets()
        
        # Show loading indicator
        loading_item = OneLineListItem(text="⏳ Loading applications...")
        self.apps_list.add_widget(loading_item)
        
        def _load():
            try:
                if not hasattr(app, 'client_socket') or not app.client_socket:
                    raise Exception("Not connected to server")
                
                # Clear any pending data in the socket buffer before sending new request
                try:
                    app.client_socket.setblocking(False)
                    while True:
                        try:
                            app.client_socket.recv(65536)
                        except:
                            break
                    app.client_socket.setblocking(True)
                except:
                    pass
                
                # Send the request
                cmd = json.dumps({'type': 'get_apps'}) + '\n'
                app.client_socket.send(cmd.encode('utf-8'))
                
                buffer = ""
                start_time = time.time()
                timeout = 10  # 10 second timeout
                
                # Set socket timeout
                app.client_socket.settimeout(2.0)
                
                while True:
                    # Check timeout
                    if time.time() - start_time > timeout:
                        raise TimeoutError("App loading timed out")
                    
                    try:
                        data = app.client_socket.recv(65536).decode('utf-8')
                        if not data:
                            if buffer and '\n' in buffer:
                                break
                            raise Exception("Connection closed by server")
                        
                        buffer += data
                        
                        # Check if we have a complete response
                        if '\n' in buffer:
                            break
                            
                    except socket.timeout:
                        # Check if we have data in buffer
                        if buffer and '\n' in buffer:
                            break
                        # Continue waiting if still within overall timeout
                        continue
                    except Exception as e:
                        raise Exception(f"Receive error: {str(e)}")
                
                if buffer:
                    # Remove any trailing data after first newline
                    response_line = buffer.split('\n')[0].strip()
                    if response_line:
                        try:
                            response = json.loads(response_line)
                            apps = response.get('apps', [])
                            
                            if apps:
                                Clock.schedule_once(
                                    lambda dt: self.display_apps(apps, instance), 0
                                )
                            else:
                                Clock.schedule_once(
                                    lambda dt: self.on_apps_empty(instance), 0
                                )
                        except json.JSONDecodeError as e:
                            raise Exception(f"Invalid JSON response: {str(e)}")
                    else:
                        raise Exception("Empty response from server")
                else:
                    raise Exception("No data received from server")
                    
            except TimeoutError as e:
                Clock.schedule_once(
                    lambda dt: self.on_apps_error(instance, str(e)), 0
                )
            except json.JSONDecodeError as e:
                Clock.schedule_once(
                    lambda dt: self.on_apps_error(instance, "Invalid response format"), 0
                )
            except Exception as e:
                Clock.schedule_once(
                    lambda dt: self.on_apps_error(instance, str(e)), 0
                )
        
        threading.Thread(target=_load, daemon=True).start()
    
    def display_apps(self, apps, button):
        self.apps_list.clear_widgets()
        
        if not apps:
            self.on_apps_empty(button)
            return
        
        # Show count
        count_item = OneLineListItem(
            text=f"✓ Found {len(apps)} applications",
            theme_text_color="Custom",
            text_color=[0.3, 0.9, 0.4, 1]
        )
        self.apps_list.add_widget(count_item)
        
        # Display apps (limit to 30 for performance)
        for app in apps[:30]:
            item = TwoLineListItem(
                text=app.get('name', 'Unknown'),
                secondary_text=app.get('type', 'application'),
                on_release=lambda x, a=app: self.launch_app(a)
            )
            self.apps_list.add_widget(item)
        
        button.disabled = False
        button.text = 'Refresh'
    
    def on_apps_empty(self, button):
        """Handle case when no apps are found"""
        self.apps_list.clear_widgets()
        
        empty_item = OneLineListItem(
            text="⚠ No applications found",
            theme_text_color="Custom",
            text_color=[0.9, 0.7, 0.3, 1]
        )
        self.apps_list.add_widget(empty_item)
        
        retry_item = OneLineListItem(
            text="Tap 'Refresh' to try again",
            theme_text_color="Custom",
            text_color=[0.6, 0.6, 0.7, 1]
        )
        self.apps_list.add_widget(retry_item)
        
        button.disabled = False
        button.text = 'Refresh'
    
    def on_apps_error(self, button, error_msg):
        """Handle app loading errors"""
        self.apps_list.clear_widgets()
        
        error_item = OneLineListItem(
            text=f"❌ Error loading apps",
            theme_text_color="Custom",
            text_color=[0.9, 0.3, 0.3, 1]
        )
        self.apps_list.add_widget(error_item)
        
        detail_item = OneLineListItem(
            text=f"{error_msg[:50]}...",
            theme_text_color="Custom",
            text_color=[0.7, 0.5, 0.5, 1]
        )
        self.apps_list.add_widget(detail_item)
        
        retry_item = OneLineListItem(
            text="Tap 'Refresh' to retry",
            theme_text_color="Custom",
            text_color=[0.6, 0.6, 0.7, 1]
        )
        self.apps_list.add_widget(retry_item)
        
        button.disabled = False
        button.text = 'Refresh'
    
    def launch_app(self, app):
        app_obj = MDApp.get_running_app()
        
        def _launch():
            try:
                if hasattr(app_obj, 'client_socket') and app_obj.client_socket:
                    cmd = json.dumps({
                        'type': 'launch_app',
                        'name': app.get('name'),
                        'path': app.get('path')
                    }) + '\n'
                    app_obj.client_socket.send(cmd.encode('utf-8'))
            except:
                pass
        
        threading.Thread(target=_launch, daemon=True).start()
    
    def set_system_info(self, info):
        self.system_info = info
        hostname = info.get('hostname', 'Computer')
        self.hostname_label.text = hostname
    
    def go_back(self, instance):
        app = MDApp.get_running_app()
        
        # Exit fullscreen if active
        if hasattr(self, 'fullscreen_mode') and self.fullscreen_mode:
            self.toggle_fullscreen(instance)
        
        if self.preview_active:
            self.preview_active = False
        
        if app.client_socket:
            try:
                app.client_socket.close()
            except:
                pass
            app.client_socket = None
        
        app.root.current = 'connection'


class FileManagerScreen(MDScreen):
    """Full file manager screen with navigation"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'filemanager'
        self.current_path = None
        self.build_ui()
    
    def build_ui(self):
        main_layout = MDBoxLayout(orientation='vertical')
        
        # Top bar with back and navigation
        top_bar = MDCard(
            orientation='horizontal',
            padding=dp(10),
            spacing=dp(10),
            size_hint_y=None,
            height=dp(65),
            md_bg_color=[0.08, 0.1, 0.15, 1],
            radius=[0]
        )
        
        back_btn = MDIconButton(
            icon='arrow-left',
            on_release=self.go_back_to_control
        )
        top_bar.add_widget(back_btn)
        
        top_bar.add_widget(MDLabel(
            text='File Manager',
            font_style='H6',
            size_hint_x=0.5
        ))
        
        refresh_btn = MDIconButton(
            icon='refresh',
            on_release=self.refresh_current_folder
        )
        top_bar.add_widget(refresh_btn)
        
        main_layout.add_widget(top_bar)
        
        # Path bar
        path_bar = MDCard(
            orientation='horizontal',
            padding=dp(10),
            spacing=dp(5),
            size_hint_y=None,
            height=dp(50),
            md_bg_color=[0.06, 0.08, 0.12, 1],
            radius=[0]
        )
        
        self.path_label = MDLabel(
            text='📂 Loading...',
            size_hint_x=1,
            theme_text_color='Custom',
            text_color=[0.5, 0.7, 1, 1]
        )
        path_bar.add_widget(self.path_label)
        
        up_btn = MDIconButton(
            icon='arrow-up',
            on_release=self.go_to_parent
        )
        path_bar.add_widget(up_btn)
        
        main_layout.add_widget(path_bar)
        
        # Files list
        scroll = MDScrollView()
        self.files_list = MDList(
            md_bg_color=[0.02, 0.03, 0.08, 1]
        )
        scroll.add_widget(self.files_list)
        main_layout.add_widget(scroll)
        
        # Bottom action bar
        action_bar = MDCard(
            orientation='horizontal',
            padding=dp(10),
            spacing=dp(10),
            size_hint_y=None,
            height=dp(60),
            md_bg_color=[0.06, 0.08, 0.12, 1],
            radius=[0]
        )
        
        self.status_label = MDLabel(
            text='Ready',
            size_hint_x=1,
            theme_text_color='Custom',
            text_color=[0.6, 0.7, 0.8, 1]
        )
        action_bar.add_widget(self.status_label)
        
        main_layout.add_widget(action_bar)
        
        self.add_widget(main_layout)
    
    def on_enter(self):
        """Called when screen is entered"""
        if self.current_path is None:
            # Load home directory on first entry
            self.browse_folder(None)
    
    def browse_folder(self, path):
        """Browse a folder on the PC"""
        self.status_label.text = 'Loading...'
        self.files_list.clear_widgets()
        
        threading.Thread(
            target=self.fetch_folder_contents,
            args=(path,),
            daemon=True
        ).start()
    
    def fetch_folder_contents(self, path):
        """Fetch folder contents from server"""
        app = MDApp.get_running_app()
        
        try:
            if not hasattr(app, 'client_socket') or not app.client_socket:
                raise Exception("Not connected")
            
            # Send browse command
            cmd = json.dumps({
                'type': 'browse_files',
                'path': path
            }) + '\n'
            app.client_socket.send(cmd.encode('utf-8'))
            
            # Receive response
            buffer = ""
            app.client_socket.settimeout(5.0)
            
            while '\n' not in buffer:
                data = app.client_socket.recv(65536).decode('utf-8')
                if not data:
                    break
                buffer += data
            
            if buffer:
                response = json.loads(buffer.split('\n')[0].strip())
                
                if response.get('status') == 'success':
                    self.current_path = response.get('path')
                    contents = response.get('contents', [])
                    parent_path = response.get('parent')
                    
                    Clock.schedule_once(
                        lambda dt: self.display_folder_contents(contents, parent_path), 0
                    )
                else:
                    error_msg = response.get('message', 'Failed to browse')
                    Clock.schedule_once(
                        lambda dt: self.show_error(error_msg), 0
                    )
        
        except Exception as e:
            Clock.schedule_once(
                lambda dt: self.show_error(str(e)), 0
            )
    
    def display_folder_contents(self, contents, parent_path):
        """Display folder contents in list"""
        self.files_list.clear_widgets()
        
        # Update path label
        self.path_label.text = f'📂 {self.current_path}'
        
        # Separate directories and files
        directories = [c for c in contents if c.get('is_dir')]
        files = [c for c in contents if not c.get('is_dir')]
        
        # Add parent directory option if available
        if parent_path:
            parent_item = OneLineIconListItem(
                text=".. (Parent Directory)",
                on_release=lambda x: self.browse_folder(parent_path)
            )
            parent_item.add_widget(MDIconButton(
                icon="folder-upload",
                theme_text_color="Custom",
                text_color=[0.9, 0.7, 0.3, 1],
                pos_hint={"center_y": 0.5}
            ))
            self.files_list.add_widget(parent_item)
        
        # Add directories
        for item in directories:
            dir_item = OneLineIconListItem(
                text=f"📁 {item['name']}",
                on_release=lambda x, p=item['path']: self.browse_folder(p)
            )
            dir_item.add_widget(MDIconButton(
                icon="folder",
                theme_text_color="Custom",
                text_color=[0.9, 0.7, 0.3, 1],
                pos_hint={"center_y": 0.5}
            ))
            self.files_list.add_widget(dir_item)
        
        # Add files
        for item in files:
            size = item.get('size', 0)
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            
            file_item = TwoLineListItem(
                text=f"📄 {item['name']}",
                secondary_text=size_str,
                on_release=lambda x, i=item: self.show_file_actions(i)
            )
            self.files_list.add_widget(file_item)
        
        # Update status
        total = len(directories) + len(files)
        self.status_label.text = f'{len(directories)} folders, {len(files)} files'
        
        if total == 0:
            empty_item = OneLineListItem(
                text="(Empty folder)",
                theme_text_color="Custom",
                text_color=[0.5, 0.5, 0.5, 1]
            )
            self.files_list.add_widget(empty_item)
    
    def show_file_actions(self, file_info):
        """Show action dialog for a file"""
        file_name = file_info.get('name', 'Unknown')
        file_path = file_info.get('path', '')
        
        dialog = MDDialog(
            title=f"📄 {file_name}",
            text=f"Choose action for this file:",
            buttons=[
                MDRaisedButton(
                    text="Download",
                    md_bg_color=[0.2, 0.6, 0.9, 1],
                    on_release=lambda x: self.download_file(file_path, file_name, dialog)
                ),
                MDRaisedButton(
                    text="Open",
                    md_bg_color=[0.3, 0.7, 0.4, 1],
                    on_release=lambda x: self.open_file(file_path, dialog)
                ),
                MDRaisedButton(
                    text="Cancel",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()
    
    def download_file(self, file_path, file_name, dialog):
        """Download file from PC"""
        dialog.dismiss()
        self.status_label.text = f'Downloading {file_name}...'
        
        threading.Thread(
            target=self.do_download_file,
            args=(file_path, file_name),
            daemon=True
        ).start()
    
    def do_download_file(self, remote_path, file_name):
        """Perform file download"""
        app = MDApp.get_running_app()
        
        try:
            if not hasattr(app, 'client_socket') or not app.client_socket:
                raise Exception("Not connected to server")
            
            cmd = json.dumps({
                'type': 'download_file',
                'path': remote_path
            }) + '\n'
            app.client_socket.send(cmd.encode('utf-8'))
            
            buffer = ""
            app.client_socket.settimeout(30.0)
            
            while '\n' not in buffer:
                data = app.client_socket.recv(65536).decode('utf-8')
                if not data:
                    break
                buffer += data
            
            response_line = buffer.split('\n')[0].strip()
            response = json.loads(response_line)
            
            if response.get('status') == 'success':
                file_data = base64.b64decode(response['data'])
                filename = response.get('filename', file_name)
                
                # Save to Downloads
                save_path = f'/storage/emulated/0/Download/{filename}'
                with open(save_path, 'wb') as f:
                    f.write(file_data)
                
                Clock.schedule_once(
                    lambda dt: setattr(self.status_label, 'text', f'✓ Downloaded: {filename}'), 0
                )
            else:
                error_msg = response.get('message', 'Download failed')
                Clock.schedule_once(
                    lambda dt: setattr(self.status_label, 'text', f'✗ Error: {error_msg}'), 0
                )
        
        except Exception as e:
            Clock.schedule_once(
                lambda dt: setattr(self.status_label, 'text', f'✗ Error: {str(e)}'), 0
            )
    
    def open_file(self, file_path, dialog):
        """Open file on PC"""
        dialog.dismiss()
        self.status_label.text = f'Opening file...'
        
        threading.Thread(
            target=self.do_open_file,
            args=(file_path,),
            daemon=True
        ).start()
    
    def do_open_file(self, file_path):
        """Send open file command"""
        app = MDApp.get_running_app()
        
        try:
            if not hasattr(app, 'client_socket') or not app.client_socket:
                raise Exception("Not connected")
            
            cmd = json.dumps({
                'type': 'open_file',
                'file_path': file_path
            }) + '\n'
            app.client_socket.send(cmd.encode('utf-8'))
            
            buffer = ""
            app.client_socket.settimeout(5.0)
            
            while '\n' not in buffer:
                data = app.client_socket.recv(4096).decode('utf-8')
                if not data:
                    break
                buffer += data
            
            response = json.loads(buffer.split('\n')[0].strip())
            
            if response.get('status') == 'success':
                Clock.schedule_once(
                    lambda dt: setattr(self.status_label, 'text', '✓ File opened on PC'), 0
                )
            else:
                error_msg = response.get('message', 'Failed')
                Clock.schedule_once(
                    lambda dt: setattr(self.status_label, 'text', f'✗ {error_msg}'), 0
                )
        
        except Exception as e:
            Clock.schedule_once(
                lambda dt: setattr(self.status_label, 'text', f'✗ Error: {str(e)}'), 0
            )
    
    def go_to_parent(self, instance):
        """Navigate to parent directory"""
        if self.current_path:
            # Try to get parent from current path
            import os
            parent = os.path.dirname(self.current_path)
            if parent and parent != self.current_path:
                self.browse_folder(parent)
    
    def refresh_current_folder(self, instance):
        """Refresh current folder"""
        if self.current_path:
            self.browse_folder(self.current_path)
    
    def show_error(self, message):
        """Show error message"""
        self.status_label.text = f'✗ Error: {message}'
    
    def go_back_to_control(self, instance):
        """Go back to control screen"""
        app = MDApp.get_running_app()
        app.root.current = 'control'


class LaptopRemoteApp(MDApp):
    """Remote control app with file transfer"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Remote Control Pro'
        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.primary_palette = 'Blue'
        self.client_socket = None
        self.server_ip = None
        self.server_port = None
    
    def build(self):
        Window.clearcolor = (0.01, 0.03, 0.1, 1)
        
        sm = MDScreenManager()
        sm.add_widget(ConnectionScreen())
        sm.add_widget(ControlScreen())
        sm.add_widget(FileManagerScreen())
        return sm
    
    def on_stop(self):
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass


if __name__ == '__main__':
    LaptopRemoteApp().run()
