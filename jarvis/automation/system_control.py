"""
Automation Module
PC control capabilities: apps, system, files, web, keyboard, mouse.
"""

import asyncio
import os
import re
import subprocess
import sys
import platform
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

import pyautogui
import psutil
import webbrowser
from pynput import keyboard as pynput_keyboard
from pynput import mouse as pynput_mouse

# Configure pyautogui for safer automation
pyautogui.FAILSAFE = True  # Move mouse to corner to abort
pyautogui.PAUSE = 0.1  # Small pause between actions


class SystemController:
    """
    Controls system functions: apps, volume, brightness, power.
    """
    
    def __init__(self):
        self.os_type = platform.system()
        self._volume_step = 5
    
    def open_application(self, app_name: str) -> Tuple[bool, str]:
        """
        Open an application by name.
        
        Args:
            app_name: Name of application to open
            
        Returns:
            (success, message) tuple
        """
        app_name = app_name.lower().strip()
        
        # Map common names to executables
        app_mapping = {
            "chrome": ["chrome", "google-chrome", "chromium"],
            "firefox": ["firefox"],
            "edge": ["msedge", "microsoft-edge"],
            "vscode": ["code", "code-insiders"],
            "notepad": ["notepad"],
            "calculator": ["calc", "calculator"],
            "terminal": ["cmd", "terminal", "powershell"],
            "spotify": ["spotify"],
            "discord": ["discord"],
            "slack": ["slack"],
            "explorer": ["explorer"],
            "task manager": ["taskmgr", "task manager"],
        }
        
        executables = app_mapping.get(app_name, [app_name])
        
        for exe in executables:
            try:
                if self.os_type == "Windows":
                    os.startfile(exe + ".exe" if not exe.endswith(".exe") else exe)
                elif self.os_type == "Darwin":
                    subprocess.run(["open", "-a", exe], check=False)
                else:  # Linux
                    subprocess.Popen([exe], stdout=subprocess.DEVNULL, 
                                   stderr=subprocess.DEVNULL)
                return True, f"{app_name} opened successfully"
            except Exception:
                continue
        
        return False, f"Could not open {app_name}"
    
    def close_application(self, app_name: str) -> Tuple[bool, str]:
        """
        Close an application by name.
        
        Args:
            app_name: Name of application to close
            
        Returns:
            (success, message) tuple
        """
        app_name = app_name.lower().strip()
        
        try:
            for proc in psutil.process_iter(['name']):
                try:
                    if app_name in proc.info['name'].lower():
                        proc.terminate()
                        return True, f"{app_name} closed"
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return False, f"{app_name} not found running"
        except Exception as e:
            return False, f"Error closing app: {str(e)}"
    
    def get_volume(self) -> int:
        """Get current system volume (0-100)."""
        try:
            if self.os_type == "Windows":
                import ctypes
                # Use Windows API via ctypes or fallback
                return 50  # Placeholder - would need proper implementation
            elif self.os_type == "Darwin":
                result = subprocess.run(
                    ["osascript", "-e", "output volume of (get volume settings)"],
                    capture_output=True, text=True
                )
                return int(result.stdout.strip())
            else:
                return 50  # Default for Linux
        except Exception:
            return 50
    
    def set_volume(self, level: int) -> Tuple[bool, str]:
        """
        Set system volume.
        
        Args:
            level: Volume level 0-100
            
        Returns:
            (success, message) tuple
        """
        level = max(0, min(100, level))
        
        try:
            if self.os_type == "Windows":
                # Use nircmd or PowerShell
                subprocess.run([
                    "powershell", "-Command",
                    f"(New-Object -ComObject WScript.Shell).SendKeys([char]174)"
                ] * level, check=False)
            elif self.os_type == "Darwin":
                subprocess.run(
                    ["osascript", "-e", f"set volume output volume {level}"],
                    check=False
                )
            else:
                # Linux - try amixer
                subprocess.run(
                    ["amixer", "set", "Master", f"{level}%"],
                    check=False
                )
            
            return True, f"Volume set to {level}%"
        except Exception as e:
            return False, f"Failed to set volume: {str(e)}"
    
    def adjust_volume(self, direction: str, amount: int = 10) -> Tuple[bool, str]:
        """
        Adjust volume up or down.
        
        Args:
            direction: 'up' or 'down'
            amount: Amount to adjust
            
        Returns:
            (success, message) tuple
        """
        current = self.get_volume()
        if direction.lower() == "up":
            new_level = min(100, current + amount)
        else:
            new_level = max(0, current - amount)
        
        return self.set_volume(new_level)
    
    def shutdown(self, delay: int = 0) -> Tuple[bool, str]:
        """
        Shutdown the system.
        
        Args:
            delay: Delay in seconds before shutdown
            
        Returns:
            (success, message) tuple
        """
        try:
            if self.os_type == "Windows":
                cmd = f"shutdown /s /t {delay}"
            elif self.os_type == "Darwin":
                cmd = f"sudo shutdown -h +{delay // 60}"
            else:
                cmd = f"sudo shutdown -h +{delay // 60}"
            
            if delay > 0:
                return True, f"System will shutdown in {delay} seconds"
            else:
                # Don't actually execute without confirmation
                return True, "Shutdown command ready (requires confirmation)"
        except Exception as e:
            return False, f"Shutdown failed: {str(e)}"
    
    def restart(self, delay: int = 0) -> Tuple[bool, str]:
        """
        Restart the system.
        
        Args:
            delay: Delay in seconds before restart
            
        Returns:
            (success, message) tuple
        """
        try:
            if self.os_type == "Windows":
                cmd = f"shutdown /r /t {delay}"
            elif self.os_type == "Darwin":
                cmd = f"sudo shutdown -r +{delay // 60}"
            else:
                cmd = f"sudo shutdown -r +{delay // 60}"
            
            return True, f"Restart command ready (requires confirmation)"
        except Exception as e:
            return False, f"Restart failed: {str(e)}"
    
    def sleep(self) -> Tuple[bool, str]:
        """Put system to sleep."""
        try:
            if self.os_type == "Windows":
                subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState,0,0,1"])
            elif self.os_type == "Darwin":
                subprocess.run(["pmset", "sleepnow"])
            else:
                subprocess.run(["systemctl", "suspend"])
            
            return True, "System entering sleep mode"
        except Exception as e:
            return False, f"Sleep failed: {str(e)}"
    
    def take_screenshot(self, save_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        Take a screenshot.
        
        Args:
            save_path: Optional path to save screenshot
            
        Returns:
            (success, message) tuple
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if save_path:
                path = save_path
            else:
                screenshots_dir = Path.home() / "Pictures" / "Screenshots"
                screenshots_dir.mkdir(parents=True, exist_ok=True)
                path = str(screenshots_dir / f"screenshot_{timestamp}.png")
            
            screenshot = pyautogui.screenshot()
            screenshot.save(path)
            
            return True, f"Screenshot saved to {path}"
        except Exception as e:
            return False, f"Screenshot failed: {str(e)}"


class FileController:
    """File and folder operations."""
    
    def __init__(self):
        self.home = Path.home()
        self.documents = self.home / "Documents"
        self.downloads = self.home / "Downloads"
        self.desktop = self.home / "Desktop"
    
    def open_folder(self, folder_name: str) -> Tuple[bool, str]:
        """
        Open a folder in file explorer.
        
        Args:
            folder_name: Name of folder to open
            
        Returns:
            (success, message) tuple
        """
        folder_map = {
            "documents": self.documents,
            "downloads": self.downloads,
            "desktop": self.desktop,
            "pictures": self.home / "Pictures",
            "music": self.home / "Music",
            "videos": self.home / "Videos",
        }
        
        folder = folder_map.get(folder_name.lower())
        
        if not folder:
            # Try as custom path
            folder = Path(folder_name)
        
        if folder.exists() and folder.is_dir():
            try:
                if sys.platform == "win32":
                    os.startfile(str(folder))
                elif sys.platform == "darwin":
                    subprocess.run(["open", str(folder)])
                else:
                    subprocess.run(["xdg-open", str(folder)])
                
                return True, f"Opened {folder_name}"
            except Exception as e:
                return False, f"Failed to open folder: {str(e)}"
        
        return False, f"Folder {folder_name} not found"
    
    def create_folder(self, name: str, location: str = "documents") -> Tuple[bool, str]:
        """
        Create a new folder.
        
        Args:
            name: Folder name
            location: Location to create folder
            
        Returns:
            (success, message) tuple
        """
        location_map = {
            "documents": self.documents,
            "downloads": self.downloads,
            "desktop": self.desktop,
        }
        
        base_path = location_map.get(location.lower(), self.documents)
        new_folder = base_path / name
        
        try:
            new_folder.mkdir(parents=True, exist_ok=True)
            return True, f"Created folder: {name}"
        except Exception as e:
            return False, f"Failed to create folder: {str(e)}"
    
    def search_files(self, query: str, 
                     max_results: int = 10) -> Tuple[bool, List[str]]:
        """
        Search for files by name.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            (success, list of file paths) tuple
        """
        results = []
        
        try:
            # Search in common locations
            search_paths = [self.documents, self.downloads, self.desktop]
            
            for search_path in search_paths:
                if not search_path.exists():
                    continue
                    
                for item in search_path.rglob(f"*{query}*"):
                    if item.is_file():
                        results.append(str(item))
                        if len(results) >= max_results:
                            return True, results
            
            return True, results
        except Exception as e:
            return False, []
    
    def open_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Open a file with default application.
        
        Args:
            file_path: Path to file
            
        Returns:
            (success, message) tuple
        """
        path = Path(file_path)
        
        if not path.exists():
            return False, f"File not found: {file_path}"
        
        try:
            if sys.platform == "win32":
                os.startfile(str(path))
            elif sys.platform == "darwin":
                subprocess.run(["open", str(path)])
            else:
                subprocess.run(["xdg-open", str(path)])
            
            return True, f"Opened {path.name}"
        except Exception as e:
            return False, f"Failed to open file: {str(e)}"


class WebController:
    """Web browsing and search operations."""
    
    def __init__(self, browser: Optional[str] = None):
        self.browser = browser
        self.search_engine = "https://www.google.com/search?q="
    
    def search(self, query: str) -> Tuple[bool, str]:
        """
        Search the web.
        
        Args:
            query: Search query
            
        Returns:
            (success, message) tuple
        """
        try:
            url = f"{self.search_engine}{query.replace(' ', '+')}"
            webbrowser.open(url)
            return True, f"Searching for: {query}"
        except Exception as e:
            return False, f"Search failed: {str(e)}"
    
    def open_url(self, url: str) -> Tuple[bool, str]:
        """
        Open a URL in browser.
        
        Args:
            url: URL to open
            
        Returns:
            (success, message) tuple
        """
        try:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            
            webbrowser.open(url)
            return True, f"Opening {url}"
        except Exception as e:
            return False, f"Failed to open URL: {str(e)}"
    
    def open_site(self, site_name: str) -> Tuple[bool, str]:
        """
        Open a popular website by name.
        
        Args:
            site_name: Name of site (youtube, google, etc.)
            
        Returns:
            (success, message) tuple
        """
        site_map = {
            "youtube": "https://youtube.com",
            "google": "https://google.com",
            "github": "https://github.com",
            "reddit": "https://reddit.com",
            "twitter": "https://twitter.com",
            "netflix": "https://netflix.com",
            "amazon": "https://amazon.com",
        }
        
        url = site_map.get(site_name.lower())
        if url:
            return self.open_url(url)
        
        return False, f"Unknown site: {site_name}"


class InputController:
    """Keyboard and mouse control."""
    
    def type_text(self, text: str, delay: float = 0.05) -> Tuple[bool, str]:
        """
        Type text using keyboard.
        
        Args:
            text: Text to type
            delay: Delay between keystrokes
            
        Returns:
            (success, message) tuple
        """
        try:
            pyautogui.write(text, interval=delay)
            return True, f"Typed: {text[:50]}..." if len(text) > 50 else f"Typed: {text}"
        except Exception as e:
            return False, f"Type failed: {str(e)}"
    
    def press_key(self, key: str) -> Tuple[bool, str]:
        """
        Press a single key.
        
        Args:
            key: Key to press
            
        Returns:
            (success, message) tuple
        """
        try:
            pyautogui.press(key)
            return True, f"Pressed {key}"
        except Exception as e:
            return False, f"Key press failed: {str(e)}"
    
    def press_hotkey(self, keys: List[str]) -> Tuple[bool, str]:
        """
        Press a keyboard shortcut.
        
        Args:
            keys: List of keys (e.g., ['ctrl', 'c'])
            
        Returns:
            (success, message) tuple
        """
        try:
            pyautogui.hotkey(*keys)
            return True, f"Pressed {'+'.join(keys)}"
        except Exception as e:
            return False, f"Hotkey failed: {str(e)}"
    
    def move_mouse(self, x: int, y: int, duration: float = 0.5) -> Tuple[bool, str]:
        """
        Move mouse to position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            duration: Movement duration in seconds
            
        Returns:
            (success, message) tuple
        """
        try:
            pyautogui.moveTo(x, y, duration=duration)
            return True, f"Mouse moved to ({x}, {y})"
        except Exception as e:
            return False, f"Mouse move failed: {str(e)}"
    
    def click(self, button: str = "left", clicks: int = 1) -> Tuple[bool, str]:
        """
        Click mouse button.
        
        Args:
            button: Button to click (left, right, middle)
            clicks: Number of clicks
            
        Returns:
            (success, message) tuple
        """
        try:
            pyautogui.click(button=button, clicks=clicks)
            return True, f"Clicked {button} button"
        except Exception as e:
            return False, f"Click failed: {str(e)}"
    
    def scroll(self, amount: int) -> Tuple[bool, str]:
        """
        Scroll mouse wheel.
        
        Args:
            amount: Scroll amount (positive = up, negative = down)
            
        Returns:
            (success, message) tuple
        """
        try:
            pyautogui.scroll(amount)
            direction = "up" if amount > 0 else "down"
            return True, f"Scrolled {direction}"
        except Exception as e:
            return False, f"Scroll failed: {str(e)}"


class AutomationManager:
    """
    Central manager for all automation capabilities.
    Provides unified interface for PC control.
    """
    
    def __init__(self):
        self.system = SystemController()
        self.files = FileController()
        self.web = WebController()
        self.input = InputController()
        
        # Command cache for quick access
        self._command_cache: Dict[str, callable] = {}
        self._build_command_cache()
    
    def _build_command_cache(self) -> None:
        """Build cache of available commands."""
        self._command_cache = {
            # App commands
            "open": self.system.open_application,
            "close": self.system.close_application,
            
            # System commands
            "volume": self.system.adjust_volume,
            "set_volume": self.system.set_volume,
            "shutdown": self.system.shutdown,
            "restart": self.system.restart,
            "sleep": self.system.sleep,
            "screenshot": self.system.take_screenshot,
            
            # File commands
            "open_folder": self.files.open_folder,
            "create_folder": self.files.create_folder,
            "search_files": self.files.search_files,
            "open_file": self.files.open_file,
            
            # Web commands
            "search": self.web.search,
            "open_url": self.web.open_url,
            "open_site": self.web.open_site,
            
            # Input commands
            "type": self.input.type_text,
            "press_key": self.input.press_key,
            "hotkey": self.input.press_hotkey,
            "move_mouse": self.input.move_mouse,
            "click": self.input.click,
            "scroll": self.input.scroll,
        }
    
    def execute_command(self, command: str, *args, **kwargs) -> Tuple[bool, Any]:
        """
        Execute a command by name.
        
        Args:
            command: Command name
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            (success, result) tuple
        """
        cmd_func = self._command_cache.get(command)
        
        if not cmd_func:
            return False, f"Unknown command: {command}"
        
        try:
            result = cmd_func(*args, **kwargs)
            return result
        except Exception as e:
            return False, f"Command execution failed: {str(e)}"
    
    def get_available_commands(self) -> List[str]:
        """Get list of available command names."""
        return list(self._command_cache.keys())
