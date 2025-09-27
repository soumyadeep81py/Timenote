"""
Windows Integration Features
Provides Windows-specific functionality like startup registration and system tray integration
"""

import os
import sys
import winreg
from typing import Optional, Tuple, Dict, Any
import subprocess

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMessageBox


class WindowsStartupManager(QObject):
    """Manages Windows startup registration"""
    
    # Signals
    startup_changed = pyqtSignal(bool)  # Emitted when startup status changes
    
    def __init__(self, app_name: str = "Timenote", app_path: str = None):
        super().__init__()
        self.app_name = app_name
        self.app_path = app_path or sys.executable
        self.registry_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
    
    def is_startup_enabled(self) -> bool:
        """Check if application is set to start with Windows"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key, 0, winreg.KEY_READ) as key:
                try:
                    value, _ = winreg.QueryValueEx(key, self.app_name)
                    # Check if the path matches (roughly)
                    return self.app_path.lower() in value.lower()
                except FileNotFoundError:
                    return False
        except Exception as e:
            print(f"Error checking startup status: {e}")
            return False
    
    def enable_startup(self) -> bool:
        """Enable application to start with Windows"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key, 0, winreg.KEY_SET_VALUE) as key:
                # Create command line with proper arguments
                if sys.executable.endswith("python.exe"):
                    # Running from Python interpreter
                    script_path = os.path.abspath(sys.argv[0])
                    command = f'"{sys.executable}" "{script_path}"'
                else:
                    # Running from compiled executable
                    command = f'"{self.app_path}"'
                
                winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, command)
                self.startup_changed.emit(True)
                return True
        except Exception as e:
            print(f"Error enabling startup: {e}")
            return False
    
    def disable_startup(self) -> bool:
        """Disable application from starting with Windows"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key, 0, winreg.KEY_SET_VALUE) as key:
                try:
                    winreg.DeleteValue(key, self.app_name)
                    self.startup_changed.emit(False)
                    return True
                except FileNotFoundError:
                    # Already disabled
                    return True
        except Exception as e:
            print(f"Error disabling startup: {e}")
            return False
    
    def toggle_startup(self) -> bool:
        """Toggle startup status"""
        if self.is_startup_enabled():
            return self.disable_startup()
        else:
            return self.enable_startup()
    
    def get_startup_command(self) -> Optional[str]:
        """Get the current startup command"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key, 0, winreg.KEY_READ) as key:
                try:
                    value, _ = winreg.QueryValueEx(key, self.app_name)
                    return value
                except FileNotFoundError:
                    return None
        except Exception:
            return None


class WindowsFileAssociations:
    """Manages Windows file associations"""
    
    @staticmethod
    def register_file_association(extension: str, app_name: str, app_path: str, description: str = None) -> bool:
        """Register file association for the application"""
        try:
            if not extension.startswith('.'):
                extension = '.' + extension
            
            # Create file type key
            file_type_key = f"{app_name}{extension.upper()}File"
            
            # Register extension
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{extension}") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, file_type_key)
            
            # Register file type
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{file_type_key}") as key:
                if description:
                    winreg.SetValue(key, "", winreg.REG_SZ, description)
                
                # Set command for opening files
                with winreg.CreateKey(key, "shell\\open\\command") as cmd_key:
                    command = f'"{app_path}" "%1"'
                    winreg.SetValue(cmd_key, "", winreg.REG_SZ, command)
            
            return True
        except Exception as e:
            print(f"Error registering file association: {e}")
            return False
    
    @staticmethod
    def unregister_file_association(extension: str, app_name: str) -> bool:
        """Unregister file association"""
        try:
            if not extension.startswith('.'):
                extension = '.' + extension
            
            file_type_key = f"{app_name}{extension.upper()}File"
            
            # Remove extension key
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{extension}")
            except FileNotFoundError:
                pass
            
            # Remove file type key
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{file_type_key}\\shell\\open\\command")
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{file_type_key}\\shell\\open")
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{file_type_key}\\shell")
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{file_type_key}")
            except FileNotFoundError:
                pass
            
            return True
        except Exception as e:
            print(f"Error unregistering file association: {e}")
            return False


class WindowsShellIntegration:
    """Manages Windows shell integration"""
    
    @staticmethod
    def add_to_context_menu(menu_name: str, command: str, app_path: str, file_types: list = None) -> bool:
        """Add application to Windows context menu"""
        try:
            if file_types is None:
                file_types = ["*"]
            
            for file_type in file_types:
                if file_type == "*":
                    # Add to all files context menu
                    key_path = "Software\\Classes\\*\\shell"
                else:
                    # Add to specific file type context menu
                    if not file_type.startswith('.'):
                        file_type = '.' + file_type
                    key_path = f"Software\\Classes\\{file_type}\\shell"
                
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{key_path}\\{menu_name}") as key:
                    winreg.SetValue(key, "", winreg.REG_SZ, menu_name)
                    
                    with winreg.CreateKey(key, "command") as cmd_key:
                        full_command = f'"{app_path}" {command} "%1"'
                        winreg.SetValue(cmd_key, "", winreg.REG_SZ, full_command)
            
            return True
        except Exception as e:
            print(f"Error adding context menu: {e}")
            return False
    
    @staticmethod
    def remove_from_context_menu(menu_name: str, file_types: list = None) -> bool:
        """Remove application from Windows context menu"""
        try:
            if file_types is None:
                file_types = ["*"]
            
            for file_type in file_types:
                if file_type == "*":
                    key_path = "Software\\Classes\\*\\shell"
                else:
                    if not file_type.startswith('.'):
                        file_type = '.' + file_type
                    key_path = f"Software\\Classes\\{file_type}\\shell"
                
                try:
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"{key_path}\\{menu_name}\\command")
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"{key_path}\\{menu_name}")
                except FileNotFoundError:
                    pass
            
            return True
        except Exception as e:
            print(f"Error removing context menu: {e}")
            return False


class WindowsEnvironment:
    """Windows environment utilities"""
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get Windows system information"""
        info = {}
        
        try:
            # Get Windows version
            import platform
            info["platform"] = platform.platform()
            info["version"] = platform.version()
            info["architecture"] = platform.architecture()
            info["machine"] = platform.machine()
            info["processor"] = platform.processor()
            
            # Get user directories
            info["user_profile"] = os.environ.get("USERPROFILE", "")
            info["app_data"] = os.environ.get("APPDATA", "")
            info["local_app_data"] = os.environ.get("LOCALAPPDATA", "")
            info["program_files"] = os.environ.get("PROGRAMFILES", "")
            info["temp_dir"] = os.environ.get("TEMP", "")
            
        except Exception as e:
            print(f"Error getting system info: {e}")
        
        return info
    
    @staticmethod
    def is_admin() -> bool:
        """Check if running with administrator privileges"""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    
    @staticmethod
    def request_admin_privileges() -> bool:
        """Request administrator privileges (requires restart)"""
        try:
            import ctypes
            if ctypes.windll.shell32.IsUserAnAdmin():
                return True
            else:
                # Re-run the program with admin rights
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1
                )
                return False
        except Exception as e:
            print(f"Error requesting admin privileges: {e}")
            return False
    
    @staticmethod
    def get_installed_programs() -> list:
        """Get list of installed programs"""
        programs = []
        
        try:
            # Check both 32-bit and 64-bit program locations
            uninstall_keys = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
            ]
            
            for key_path in uninstall_keys:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                with winreg.OpenKey(key, subkey_name) as subkey:
                                    try:
                                        name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                                        version, _ = winreg.QueryValueEx(subkey, "DisplayVersion")
                                        programs.append({"name": name, "version": version})
                                    except FileNotFoundError:
                                        pass
                            except Exception:
                                continue
                except Exception:
                    continue
        except Exception as e:
            print(f"Error getting installed programs: {e}")
        
        return programs


class WindowsNotificationManager:
    """Enhanced Windows notification management"""
    
    @staticmethod
    def is_focus_assist_on() -> bool:
        """Check if Windows Focus Assist (Do Not Disturb) is enabled"""
        try:
            # This is a simplified check - actual implementation would need to check
            # Windows registry or use Windows APIs
            return False
        except Exception:
            return False
    
    @staticmethod
    def show_action_center_notification(title: str, content: str, actions: list = None) -> bool:
        """Show notification in Windows Action Center with custom actions"""
        try:
            # This would require Windows Toast Notification APIs
            # For now, fall back to basic notification
            from features.alarm import WindowsNotification
            return WindowsNotification.show_notification(title, content)
        except Exception as e:
            print(f"Error showing action center notification: {e}")
            return False


class WindowsPowerManagement:
    """Windows power management utilities"""
    
    @staticmethod
    def prevent_sleep() -> bool:
        """Prevent Windows from going to sleep"""
        try:
            import ctypes
            from ctypes import wintypes
            
            # SetThreadExecutionState flags
            ES_CONTINUOUS = 0x80000000
            ES_SYSTEM_REQUIRED = 0x00000001
            ES_DISPLAY_REQUIRED = 0x00000002
            
            result = ctypes.windll.kernel32.SetThreadExecutionState(
                ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
            )
            return result != 0
        except Exception as e:
            print(f"Error preventing sleep: {e}")
            return False
    
    @staticmethod
    def allow_sleep() -> bool:
        """Allow Windows to go to sleep normally"""
        try:
            import ctypes
            
            ES_CONTINUOUS = 0x80000000
            result = ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
            return result != 0
        except Exception as e:
            print(f"Error allowing sleep: {e}")
            return False


class WindowsIntegrationManager(QObject):
    """Main manager for Windows integration features"""
    
    def __init__(self, app_name: str = "Timenote", app_path: str = None):
        super().__init__()
        self.app_name = app_name
        self.app_path = app_path or sys.executable
        
        # Initialize managers
        self.startup_manager = WindowsStartupManager(app_name, app_path)
        self.file_associations = WindowsFileAssociations()
        self.shell_integration = WindowsShellIntegration()
        self.environment = WindowsEnvironment()
        self.notifications = WindowsNotificationManager()
        self.power = WindowsPowerManagement()
    
    def setup_windows_integration(self, config: Dict[str, Any]) -> Dict[str, bool]:
        """Setup all Windows integration features based on config"""
        results = {}
        
        try:
            # Handle startup registration
            startup_enabled = config.get("startup", {}).get("auto_start", False)
            if startup_enabled and not self.startup_manager.is_startup_enabled():
                results["startup_enabled"] = self.startup_manager.enable_startup()
            elif not startup_enabled and self.startup_manager.is_startup_enabled():
                results["startup_disabled"] = self.startup_manager.disable_startup()
            
            # Handle file associations (optional)
            if config.get("file_associations", {}).get("enable", False):
                extensions = config["file_associations"].get("extensions", [".txt"])
                for ext in extensions:
                    success = self.file_associations.register_file_association(
                        ext, self.app_name, self.app_path, f"{self.app_name} Document"
                    )
                    results[f"file_association_{ext}"] = success
            
            # Handle context menu integration (optional)
            if config.get("context_menu", {}).get("enable", False):
                success = self.shell_integration.add_to_context_menu(
                    f"Open with {self.app_name}",
                    "--file",
                    self.app_path,
                    [".txt", ".md"]
                )
                results["context_menu"] = success
            
        except Exception as e:
            print(f"Error setting up Windows integration: {e}")
            results["error"] = str(e)
        
        return results
    
    def cleanup_windows_integration(self) -> Dict[str, bool]:
        """Remove all Windows integration features"""
        results = {}
        
        try:
            # Remove startup
            results["startup_removed"] = self.startup_manager.disable_startup()
            
            # Remove file associations
            extensions = [".txt", ".md", ".json"]
            for ext in extensions:
                success = self.file_associations.unregister_file_association(ext, self.app_name)
                results[f"file_association_removed_{ext}"] = success
            
            # Remove context menu
            results["context_menu_removed"] = self.shell_integration.remove_from_context_menu(
                f"Open with {self.app_name}",
                ["*", ".txt", ".md"]
            )
            
        except Exception as e:
            print(f"Error cleaning up Windows integration: {e}")
            results["error"] = str(e)
        
        return results
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get current Windows integration status"""
        return {
            "startup_enabled": self.startup_manager.is_startup_enabled(),
            "startup_command": self.startup_manager.get_startup_command(),
            "is_admin": self.environment.is_admin(),
            "system_info": self.environment.get_system_info(),
            "focus_assist_on": self.notifications.is_focus_assist_on()
        }
