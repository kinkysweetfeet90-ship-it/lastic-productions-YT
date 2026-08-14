import kivy
kivy.require('2.0.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import AsyncImage
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.animation import Animation

import threading
import os
import yt_dlp
import sys
import datetime

# Import tkinter for file dialog (desktop only)
try:
    from tkinter import filedialog
    import tkinter as tk
    HAS_TKINTER = True
except:
    HAS_TKINTER = False

# Helper to check permissions on Android
class YtdlpLogger:
    def debug(self, msg):
        pass
    def warning(self, msg):
        pass
    def error(self, msg):
        print(f"YTDLP ERROR: {msg}")

def check_permissions():
    if platform == "android":
        from android.permissions import request_permissions, Permission
        request_permissions([
            Permission.INTERNET,
            Permission.READ_EXTERNAL_STORAGE,
            Permission.WRITE_EXTERNAL_STORAGE
        ])

KV = '''
<MainLayout>:
    orientation: 'vertical'
    padding: 20
    spacing: 20
    canvas.before:
        Color:
            rgba: 0.04, 0.04, 0.04, 1
        Rectangle:
            pos: self.pos
            size: self.size

    # --- Modern Header ---
    BoxLayout:
        orientation: 'vertical'
        size_hint_y: None
        height: 80
        padding: [0, 10, 0, 20]
        
        Label:
            text: 'LASTIC PRODUCTIONS'
            font_size: '28sp'
            bold: True
            size_hint_y: None
            height: 40
            halign: 'center'
            text_size: self.size
            canvas.before:
                Color:
                    rgba: 0, 0.44, 0.95, 1
                Rectangle:
                    pos: self.x + self.width * 0.1, self.y + self.height * 0.3
                    size: self.width * 0.8, self.height * 0.4
                Color:
                    rgba: 0.47, 0.16, 0.8, 1
                Rectangle:
                    pos: self.x + self.width * 0.2, self.y + self.height * 0.3
                    size: self.width * 0.6, self.height * 0.4
            color: 1, 1, 1, 1
        
        Label:
            text: 'High-Speed Video & Audio Downloader'
            font_size: '14sp'
            size_hint_y: None
            height: 20
            halign: 'center'
            text_size: self.size
            color: 0.63, 0.63, 0.63, 1

    # --- Input Section Card ---
    BoxLayout:
        orientation: 'vertical'
        size_hint_y: None
        height: 100
        spacing: 12
        padding: 20
        canvas.before:
            Color:
                rgba: 0.09, 0.09, 0.09, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [12,]

        Label:
            text: 'ENTER VIDEO URL'
            font_size: '12sp'
            bold: True
            size_hint_y: None
            height: 20
            halign: 'left'
            text_size: self.size
            color: 0.63, 0.63, 0.63, 1

        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: 45
            spacing: 12

            TextInput:
                id: url_input
                hint_text: 'Paste YouTube or Social link here...'
                multiline: False
                size_hint_x: 0.65
                background_color: 0.13, 0.13, 0.13, 1
                foreground_color: 1, 1, 1, 1
                cursor_color: 0, 0.44, 0.95, 1
                padding: [15, 12]
                font_size: '16sp'
                on_text_validate: root.fetch_info_threaded()
                use_bubble: True
                use_handles: True
                write_tab: False
                focus: True
                input_type: 'text'
                keyboard_suggestions: True

            Button:
                text: 'PASTE'
                size_hint_x: None
                width: 70
                background_normal: ''
                background_color: 0.3, 0.3, 0.3, 1
                bold: True
                font_size: '12sp'
                on_release: root.paste_from_clipboard()

            Button:
                text: 'ANALYZE'
                size_hint_x: None
                width: 100
                background_normal: ''
                background_color: 0, 0.44, 0.95, 1
                bold: True
                font_size: '14sp'
                on_release: root.fetch_info_threaded()

    # --- Preview Card ---
    BoxLayout:
        orientation: 'vertical'
        size_hint_y: None
        height: 140 if root.video_title else 0
        opacity: 1 if root.video_title else 0
        padding: 20
        spacing: 15
        canvas.before:
            Color:
                rgba: 0.09, 0.09, 0.09, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [12,]

        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: 70
            spacing: 15
            
            AsyncImage:
                id: thumbnail
                source: ''
                size_hint_x: 0.3
                allow_stretch: True
                keep_ratio: True
                canvas.before:
                    Color:
                        rgba: 0.2, 0.2, 0.2, 1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [6,]
            
            Label:
                id: video_title_label
                text: root.video_title
                text_size: self.width, None
                size_hint_x: 0.7
                valign: 'middle'
                halign: 'left'
                max_lines: 2
                shorten: True
                font_size: '14sp'
                color: 1, 1, 1, 1

        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: 40
            spacing: 10
            
            Label:
                text: 'Video Quality:'
                size_hint_x: 0.3
                font_size: '13sp'
                color: 0.63, 0.63, 0.63, 1
                halign: 'left'
                text_size: self.size
            
            Spinner:
                id: quality_spinner
                text: 'Select Quality'
                values: []
                size_hint_x: 0.7
                background_normal: ''
                background_color: 0.13, 0.13, 0.13, 1
                font_size: '13sp'
                on_text: root.current_quality = self.text

        # Audio Settings (shown when Audio Only selected)
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: 40 if 'Audio' in root.current_quality else 0
            opacity: 1 if 'Audio' in root.current_quality else 0
            spacing: 10
            
            Label:
                text: 'Format:'
                size_hint_x: 0.3
                font_size: '13sp'
                color: 0.63, 0.63, 0.63, 1
                halign: 'left'
                text_size: self.size
            
            Spinner:
                id: audio_format_spinner
                text: 'MP3'
                values: ('MP3', 'M4A', 'OPUS', 'FLAC', 'WAV')
                size_hint_x: 0.7
                background_normal: ''
                background_color: 0.13, 0.13, 0.13, 1
                font_size: '13sp'

        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: 40 if 'Audio' in root.current_quality else 0
            opacity: 1 if 'Audio' in root.current_quality else 0
            spacing: 10
            
            Label:
                text: 'Bitrate:'
                size_hint_x: 0.3
                font_size: '13sp'
                color: 0.63, 0.63, 0.63, 1
                halign: 'left'
                text_size: self.size
            
            Spinner:
                id: audio_quality_spinner
                text: '320'
                values: ('320', '256', '192', '128', '64')
                size_hint_x: 0.7
                background_normal: ''
                background_color: 0.13, 0.13, 0.13, 1
                font_size: '13sp'

        # Action Buttons
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: 90
            spacing: 10

            Button:
                id: download_btn
                text: 'DOWNLOAD VIDEO'
                background_normal: ''
                background_color: 0, 0.8, 0, 1
                bold: True
                font_size: '16sp'
                disabled: True
                on_release: root.start_download()

            Button:
                id: mp3_btn
                text: 'QUICK MP3'
                background_normal: ''
                background_color: 0.47, 0.16, 0.8, 1
                bold: True
                font_size: '16sp'
                disabled: True
                on_release: root.start_mp3_download()

        # Cancel Button (shown during download)
        Button:
            id: cancel_btn
            text: 'CANCEL DOWNLOAD'
            background_normal: ''
            background_color: 0.8, 0.2, 0.2, 1
            bold: True
            font_size: '14sp'
            size_hint_y: None
            height: 0
            opacity: 0
            disabled: True
            on_release: root.cancel_download()

    # --- Progress Section ---
    BoxLayout:
        orientation: 'vertical'
        size_hint_y: None
        height: 80
        padding: 20
        spacing: 8
        canvas.before:
            Color:
                rgba: 0.09, 0.09, 0.09, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [12,]

        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: 20
            
            Label:
                id: status_label
                text: 'READY'
                font_size: '14sp'
                bold: True
                color: 0.8, 0.8, 0.8, 1
                size_hint_x: 0.7
                halign: 'left'
                text_size: self.size
            
            Label:
                id: speed_eta_label
                text: ''
                font_size: '12sp'
                color: 0.5, 0.5, 0.5, 1
                size_hint_x: 0.3
                halign: 'right'
                text_size: self.size

        ProgressBar:
            id: progress_bar
            max: 100
            value: 0
            size_hint_y: None
            height: 8
            canvas.before:
                Color:
                    rgba: 0.2, 0.2, 0.2, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [4,]
            canvas:
                Color:
                    rgba: 0, 0.44, 0.95, 1
                RoundedRectangle:
                    pos: self.pos
                    size: (self.width * self.value / self.max, self.height)
                    radius: [4,]

    # --- Log Section ---
    BoxLayout:
        orientation: 'vertical'
        size_hint_y: 1
        spacing: 0
        
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: 35
            padding: [20, 10, 20, 5]
            spacing: 10
            canvas.before:
                Color:
                    rgba: 0.09, 0.09, 0.09, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [12, 12, 0, 0]
            
            Label:
                text: 'SYSTEM LOG'
                font_size: '12sp'
                bold: True
                color: 0.34, 0.34, 0.34, 1
                size_hint_x: 0.8
                halign: 'left'
                text_size: self.size
            
            Button:
                text: 'CLEAR'
                size_hint_x: 0.2
                background_normal: ''
                background_color: 0, 0, 0, 0
                color: 1, 0.3, 0.3, 1
                font_size: '11sp'
                bold: True
                on_release: root.clear_log()

        ScrollView:
            id: log_scroll
            size_hint_y: 1
            scroll_type: ['bars', 'content']
            bar_width: '8dp'
            scroll_wheel_distance: '60dp'
            canvas.before:
                Color:
                    rgba: 0, 0, 0, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [0, 0, 12, 12]

            Label:
                id: log_label
                text: 'System ready...\\n'
                size_hint_y: None
                height: self.texture_size[1]
                text_size: self.width, None
                padding: [20, 15, 20, 15]
                markup: True
                font_size: '11sp'
                color: 0.7, 0.7, 0.7, 1
'''

class MainLayout(BoxLayout):
    video_title = ObjectProperty('')
    current_quality = StringProperty('')
    download_thread = None
    cancel_requested = False
    
    def log(self, message):
        print(f"APP_LOG: {message}")
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.ids.log_label.text += f"[{timestamp}] {message}\\n"
        
        # Auto-scroll to bottom
        Clock.schedule_once(self._scroll_to_bottom)

    def _scroll_to_bottom(self, dt):
        self.ids.log_scroll.scroll_y = 0
        
    def clear_log(self):
        self.ids.log_label.text = 'System ready...\n'
        self.ids.progress_bar.value = 0
        self.ids.status_label.text = 'READY'
        self.ids.speed_eta_label.text = ''

    def paste_from_clipboard(self):
        try:
            from kivy.core.clipboard import Clipboard
            clipboard_text = Clipboard.paste()
            if clipboard_text:
                self.ids.url_input.text = clipboard_text.strip()
                self.log("URL pasted from clipboard")
                # Auto-analyze after pasting
                Clock.schedule_once(lambda dt: self.fetch_info_threaded(), 0.5)
            else:
                self.log("Clipboard is empty")
        except Exception as e:
            self.log(f"Failed to paste: {str(e)}")

    def fetch_info_threaded(self):
        url = self.ids.url_input.text.strip()
        if not url:
            self.log("Please enter a URL first.")
            return
        
        self.ids.status_label.text = "Fetching video info..."
        self.ids.quality_spinner.text = "Loading..."
        self.ids.download_btn.disabled = True
        
        threading.Thread(target=self.fetch_info, args=(url,), daemon=True).start()


    def fetch_info(self, url):
        ydl_opts = {
            'quiet': True, 
            'no_warnings': True,
            'logger': YtdlpLogger(),
            # Add user agent to help with Twitter/X
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Get Title and Thumbnail
                title = info.get('title', 'Unknown Title')
                thumb = info.get('thumbnail', '')
                
                # Get Formats
                formats = info.get('formats', [])
                valid_qualities = set()
                
                for f in formats:
                    # Filter for video only or video+audio content
                    if f.get('vcodec') != 'none':
                        height = f.get('height')
                        if height:
                            valid_qualities.add(f"{height}p")
                
                # Sort qualities
                sorted_qualities = sorted(list(valid_qualities), key=lambda x: int(x.replace('p', '')), reverse=True)
                sorted_qualities.insert(0, 'Best')
                sorted_qualities.append('Audio Only')
                
                Clock.schedule_once(lambda dt: self.update_ui_with_info(title, thumb, sorted_qualities))
                
        except Exception as e:
            err = str(e)
            print(f"Full error: {err}")  # Debug print
            Clock.schedule_once(lambda dt: self.error_ui(f"Fetch failed: {err}"))

    def update_ui_with_info(self, title, thumb, qualities):
        self.video_title = title
        self.ids.thumbnail.source = thumb
        self.ids.quality_spinner.values = qualities
        self.ids.quality_spinner.text = 'Best'
        self.ids.download_btn.disabled = False
        self.ids.mp3_btn.disabled = False
        self.ids.status_label.text = "READY TO DOWNLOAD"
        self.log(f"Loaded info for: {title}")

    def start_mp3_download(self):
        url = self.ids.url_input.text.strip()
        if not url:
            self.log("Error: Please enter a URL")
            return
        
        self.log("Forcing MP3 High-Quality Download...")
        self.ids.quality_spinner.text = "Audio Only"
        self.ids.audio_format_spinner.text = "MP3"
        self.ids.audio_quality_spinner.text = "320"
        self.start_download()

    def start_download(self):
        url = self.ids.url_input.text.strip()
        quality_text = self.ids.quality_spinner.text
        audio_format = self.ids.audio_format_spinner.text.lower() if 'Audio' in quality_text else None
        audio_quality = self.ids.audio_quality_spinner.text if 'Audio' in quality_text else None
        
        if not url:
            self.log("Error: Please enter a URL")
            return

        # Reset cancel flag
        self.cancel_requested = False

        # Choose download location (desktop only)
        download_dir = None
        if platform != "android" and HAS_TKINTER:
            try:
                root = tk.Tk()
                root.withdraw()  # Hide the main window
                root.attributes('-topmost', True)  # Bring dialog to front
                download_dir = filedialog.askdirectory(
                    title="Choose Download Location",
                    initialdir=os.getcwd()
                )
                root.destroy()
                
                if not download_dir:  # User cancelled
                    self.log("Download cancelled - no folder selected")
                    return
            except Exception as e:
                self.log(f"Folder dialog error: {e}")
                download_dir = os.getcwd()
        
        self.ids.status_label.text = "Initializing..."
        self.log(f"Starting download: {quality_text}" + (f" ({audio_format.upper()} {audio_quality}kbps)" if audio_format else ""))
        
        # Show cancel button, hide download buttons
        self.show_cancel_button()
        
        self.download_thread = threading.Thread(target=self.download_thread_func, args=(url, quality_text, download_dir, audio_format, audio_quality), daemon=True)
        self.download_thread.start()

    def cancel_download(self):
        self.cancel_requested = True
        self.log("Cancelling download...")
        self.ids.status_label.text = "Cancelling..."
        self.hide_cancel_button()
        
    def show_cancel_button(self):
        self.ids.cancel_btn.height = 50
        self.ids.cancel_btn.opacity = 1
        self.ids.cancel_btn.disabled = False
        self.ids.download_btn.disabled = True
        self.ids.mp3_btn.disabled = True
        
    def hide_cancel_button(self):
        self.ids.cancel_btn.height = 0
        self.ids.cancel_btn.opacity = 0
        self.ids.cancel_btn.disabled = True

    def download_thread_func(self, url, quality_text, download_dir=None, audio_format=None, audio_quality=None):
        ydl_opts = {
            'progress_hooks': [self.progress_hook],
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'logger': YtdlpLogger(),
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'player_skip': ['configs', 'webpage'],
                }
            },
            'extractor_retries': 3,
            'fragment_retries': 3,
            'retry_sleep_functions': {
                'http': lambda x: min(x * 2, 30),
                'fragment': lambda x: min(x * 2, 30)
            }
        }

        # Platform specific paths
        if download_dir:
            # Use the chosen directory
            pass
        elif platform == "android":
            from android.storage import primary_external_storage_path
            dir_path = primary_external_storage_path()
            download_dir = os.path.join(dir_path, 'Download')
        else:
            download_dir = os.getcwd()
            
        if not os.path.exists(download_dir):
            try:
                os.makedirs(download_dir)
            except:
                pass 
                download_dir = os.getcwd()

        ydl_opts['paths'] = {'home': download_dir}

        # Quality configuration
        if quality_text == 'Audio Only':
            ydl_opts['format'] = 'bestaudio/best'
            # Use selected audio format or default to mp3
            codec = audio_format if audio_format else 'mp3'
            bitrate = audio_quality if audio_quality else '320'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': codec,
                'preferredquality': bitrate if codec in ['mp3', 'm4a'] else '0',  # Use bitrate for MP3/M4A, best for others
            }]
        elif quality_text == 'Best':
            ydl_opts['format'] = 'bestvideo+bestaudio/best'
        else:
             # e.g., 1080p -> 1080
            height = quality_text.replace('p', '')
            ydl_opts['format'] = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]'

        try:
            Clock.schedule_once(lambda dt: self.log(f"Saving to: {download_dir}"))
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Video')
                if not self.cancel_requested:
                    Clock.schedule_once(lambda dt: self.success_ui(title))
        except Exception as e:
            if not self.cancel_requested:
                error_msg = str(e)
                Clock.schedule_once(lambda dt: self.error_ui(error_msg))
            else:
                Clock.schedule_once(lambda dt: self.log("Download cancelled successfully"))

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                # Try multiple ways to get progress
                if 'downloaded_bytes' in d and 'total_bytes' in d:
                    progress = (d['downloaded_bytes'] / d['total_bytes']) * 100
                elif 'downloaded_bytes' in d and 'total_bytes_estimate' in d:
                    progress = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                else:
                    # Fallback to percent string
                    p_str = d.get('_percent_str', '0%').strip().replace('%', '')
                    progress = float(p_str) if p_str else 0
                
                speed = d.get('_speed_str', 'N/A')
                eta = d.get('_eta_str', 'N/A')
                
                # Log to console for debugging
                print(f"PROGRESS: {progress:.1f}% | Speed: {speed} | ETA: {eta}")
                
                Clock.schedule_once(lambda dt: self.update_progress(progress, speed, eta))
            except Exception as e:
                print(f"Progress hook error: {e}")
        elif d['status'] == 'finished':
            Clock.schedule_once(lambda dt: self.update_status("Processing..."))

    def update_progress(self, progress, speed, eta):
        self.ids.progress_bar.value = progress
        self.ids.status_label.text = f"Downloading: {progress:.1f}%"
        self.ids.speed_eta_label.text = f"Speed: {speed} | ETA: {eta}"

    def update_status(self, msg):
        self.ids.status_label.text = msg

    def success_ui(self, title):
        self.ids.progress_bar.value = 100
        self.ids.status_label.text = "✔️ DOWNLOAD COMPLETE"
        self.ids.speed_eta_label.text = ""
        self.ids.download_btn.disabled = False
        self.ids.mp3_btn.disabled = False
        self.hide_cancel_button()  # Hide cancel button
        self.log(f"Successfully downloaded: {title}")
        
        # Animation: Bright Green Pulse
        anim = Animation(color=(0, 1, 0, 1), font_size=18, duration=0.2, t='out_quad')
        anim += Animation(color=(0.8, 0.8, 0.8, 1), font_size=14, duration=0.5, t='in_quad')
        anim.start(self.ids.status_label)

    def error_ui(self, msg):
        self.ids.status_label.text = "Error"
        self.log(f"Error: {msg}")
        self.ids.download_btn.disabled = False
        self.ids.mp3_btn.disabled = False
        self.hide_cancel_button()  # Hide cancel button

class VideoDownloaderApp(App):
    title = "Lastic Productions"
    def build(self):
        Builder.load_string(KV)
        # Set window size for desktop
        from kivy.config import Config
        Config.set('graphics', 'width', '800')
        Config.set('graphics', 'height', '700')
        Config.set('graphics', 'resizable', '1')
        return MainLayout()

    def on_start(self):
        check_permissions()
        # Focus on the URL input field when app starts
        def focus_input(dt):
            if hasattr(self, 'root') and self.root and hasattr(self.root.ids, 'url_input'):
                self.root.ids.url_input.focus = True
        Clock.schedule_once(focus_input, 1)

if __name__ == '__main__':
    VideoDownloaderApp().run()
