"""
Alarm System
Provides alarm functionality with sound playback, Windows notifications, and snooze options
"""

import os
import sys
import time
import threading
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread
from PyQt6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtGui import QFont, QIcon

# Import Windows-specific modules
try:
    import winsound
    WINSOUND_AVAILABLE = True
except ImportError:
    WINSOUND_AVAILABLE = False

try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


class AlarmSound:
    """Sound playback for alarms"""
    
    def __init__(self):
        self.is_playing = False
        self.stop_requested = False
        self.sound_thread = None
        
        # Initialize pygame mixer if available
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
                self.pygame_initialized = True
            except pygame.error:
                self.pygame_initialized = False
        else:
            self.pygame_initialized = False
    
    def play_sound(self, sound_file: str, volume: float = 0.8, loop: bool = True) -> bool:
        """Play alarm sound"""
        if self.is_playing:
            return False
        
        if not sound_file or not os.path.exists(sound_file):
            # Use default system sound
            return self._play_system_sound(loop)
        
        # Try to play custom sound file
        if self.pygame_initialized:
            return self._play_with_pygame(sound_file, volume, loop)
        elif WINSOUND_AVAILABLE and sound_file.endswith('.wav'):
            return self._play_with_winsound(sound_file, loop)
        else:
            return self._play_system_sound(loop)
    
    def stop_sound(self):
        """Stop playing alarm sound"""
        self.stop_requested = True
        
        if self.pygame_initialized:
            pygame.mixer.music.stop()
        
        if WINSOUND_AVAILABLE:
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
            except:
                pass
        
        self.is_playing = False
    
    def _play_with_pygame(self, sound_file: str, volume: float, loop: bool) -> bool:
        """Play sound using pygame"""
        try:
            pygame.mixer.music.load(sound_file)
            pygame.mixer.music.set_volume(volume)
            
            loops = -1 if loop else 0
            pygame.mixer.music.play(loops=loops)
            
            self.is_playing = True
            return True
        except pygame.error as e:
            print(f"Pygame sound error: {e}")
            return False
    
    def _play_with_winsound(self, sound_file: str, loop: bool) -> bool:
        """Play WAV sound using winsound"""
        try:
            flags = winsound.SND_FILENAME
            if loop:
                flags |= winsound.SND_LOOP | winsound.SND_ASYNC
            else:
                flags |= winsound.SND_ASYNC
            
            self.sound_thread = threading.Thread(
                target=self._winsound_worker, 
                args=(sound_file, flags, loop)
            )
            self.sound_thread.start()
            
            self.is_playing = True
            return True
        except Exception as e:
            print(f"Winsound error: {e}")
            return False
    
    def _winsound_worker(self, sound_file: str, flags: int, loop: bool):
        """Worker thread for winsound playback"""
        try:
            if loop:
                winsound.PlaySound(sound_file, flags)
            else:
                winsound.PlaySound(sound_file, flags)
                
            if not loop:
                self.is_playing = False
        except Exception as e:
            print(f"Winsound worker error: {e}")
            self.is_playing = False
    
    def _play_system_sound(self, loop: bool) -> bool:
        """Play default system alarm sound"""
        try:
            if WINSOUND_AVAILABLE:
                if loop:
                    # For looping, we need to use a separate thread
                    self.sound_thread = threading.Thread(
                        target=self._system_sound_loop
                    )
                    self.sound_thread.start()
                else:
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                
                self.is_playing = True
                return True
            else:
                # Fallback: system beep
                print("\a")  # ASCII bell character
                return True
        except Exception as e:
            print(f"System sound error: {e}")
            return False
    
    def _system_sound_loop(self):
        """Loop system sound until stopped"""
        while not self.stop_requested:
            try:
                if WINSOUND_AVAILABLE:
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                time.sleep(2)  # Wait 2 seconds between beeps
            except:
                break
        
        self.is_playing = False


class WindowsNotification:
    """Windows notification system"""
    
    @staticmethod
    def show_notification(title: str, message: str, duration: int = 10, icon_path: str = None) -> bool:
        """Show Windows toast notification"""
        try:
            # Try plyer first (cross-platform)
            if PLYER_AVAILABLE:
                notification.notify(
                    title=title,
                    message=message,
                    timeout=duration,
                    app_icon=icon_path
                )
                return True
        except Exception as e:
            print(f"Plyer notification error: {e}")
        
        try:
            # Try win10toast for Windows 10+ toast notifications
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(
                title,
                message,
                duration=duration,
                icon_path=icon_path,
                threaded=True
            )
            return True
        except ImportError:
            print("win10toast not available")
        except Exception as e:
            print(f"Win10toast error: {e}")
        
        # Fallback to message box if no other options work
        return False
    
    @staticmethod
    def show_message_box(title: str, message: str, icon=None) -> bool:
        """Show message box as fallback notification"""
        try:
            msg_box = QMessageBox()
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.setIcon(icon or QMessageBox.Icon.Information)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.show()
            return True
        except Exception as e:
            print(f"Message box error: {e}")
            return False


class AlarmDialog(QDialog):
    """Alarm notification dialog with snooze and stop options"""
    
    snoozed = pyqtSignal(int)  # Emitted when alarm is snoozed (snooze_minutes)
    stopped = pyqtSignal()     # Emitted when alarm is stopped
    
    def __init__(self, timer_name: str, snooze_duration: int = 5, parent=None):
        super().__init__(parent)
        self.timer_name = timer_name
        self.snooze_duration = snooze_duration
        
        self.setWindowTitle("Timenote - Timer Finished!")
        self.setModal(True)
        self.setFixedSize(400, 200)
        self.setup_ui()
        
        # Keep dialog on top
        self.setWindowFlags(self.windowFlags() | self.windowType().WindowStaysOnTopHint)
        
        # Auto-close timer (optional)
        self.auto_close_timer = QTimer()
        self.auto_close_timer.timeout.connect(self.auto_snooze)
        # Uncomment to enable auto-snooze after 30 seconds
        # self.auto_close_timer.start(30000)
    
    def setup_ui(self):
        """Setup the alarm dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Title
        title_label = QLabel("⏰ Timenote - Timer Finished!")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setWeight(QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(self.alignment().AlignCenter)
        layout.addWidget(title_label)
        
        # Timer name
        name_label = QLabel(f'"{self.timer_name}" has finished')
        name_font = QFont()
        name_font.setPointSize(12)
        name_label.setFont(name_font)
        name_label.setAlignment(self.alignment().AlignCenter)
        layout.addWidget(name_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Snooze button
        snooze_btn = QPushButton(f"Snooze ({self.snooze_duration}min)")
        snooze_btn.clicked.connect(self.snooze_alarm)
        snooze_btn.setDefault(True)  # Default action
        button_layout.addWidget(snooze_btn)
        
        # Stop button
        stop_btn = QPushButton("Stop")
        stop_btn.clicked.connect(self.stop_alarm)
        button_layout.addWidget(stop_btn)
        
        layout.addLayout(button_layout)
        
        # Apply styling
        self.setStyleSheet("""
        QDialog {
            background-color: #ffffff;
            color: #37352f;
        }
        
        QLabel {
            color: #37352f;
        }
        
        QPushButton {
            background-color: #2383e2;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 12px 24px;
            font-weight: 500;
            min-width: 100px;
        }
        
        QPushButton:hover {
            background-color: #1a6bb8;
        }
        
        QPushButton:pressed {
            background-color: #0d5aa3;
        }
        """)
    
    def snooze_alarm(self):
        """Handle snooze action"""
        self.auto_close_timer.stop()
        self.snoozed.emit(self.snooze_duration)
        self.accept()
    
    def stop_alarm(self):
        """Handle stop action"""
        self.auto_close_timer.stop()
        self.stopped.emit()
        self.accept()
    
    def auto_snooze(self):
        """Auto-snooze if user doesn't respond"""
        self.snooze_alarm()
    
    def closeEvent(self, event):
        """Handle dialog close event"""
        self.auto_close_timer.stop()
        self.stopped.emit()
        event.accept()


class AlarmManager(QObject):
    """Manages alarm notifications for timers"""
    
    # Signals
    alarm_triggered = pyqtSignal(str, dict)  # Emitted when alarm starts (timer_id, timer_data)
    alarm_snoozed = pyqtSignal(str, int)     # Emitted when alarm is snoozed (timer_id, minutes)
    alarm_stopped = pyqtSignal(str)          # Emitted when alarm is stopped (timer_id)
    
    def __init__(self, data_handler, parent=None):
        super().__init__(parent)
        self.data_handler = data_handler
        self.config = data_handler.load_config()
        
        # Sound and notification systems
        self.sound_player = AlarmSound()
        self.notification_system = WindowsNotification()
        
        # Track active alarms
        self.active_alarms: Dict[str, Dict[str, Any]] = {}
        self.alarm_dialogs: Dict[str, AlarmDialog] = {}
        
        # Snooze timers
        self.snooze_timers: Dict[str, QTimer] = {}
    
    def trigger_alarm(self, timer_id: str, timer_data: Dict[str, Any]):
        """Trigger an alarm for a finished timer"""
        if timer_id in self.active_alarms:
            # Alarm already active for this timer
            return
        
        timer_name = timer_data.get("name", "Timer")
        
        # Store alarm info
        self.active_alarms[timer_id] = {
            "timer_data": timer_data,
            "start_time": datetime.now(),
            "is_snoozed": False
        }
        
        # Play sound
        self._play_alarm_sound()
        
        # Show notification
        self._show_notification(timer_name)
        
        # Show dialog
        self._show_alarm_dialog(timer_id, timer_name)
        
        self.alarm_triggered.emit(timer_id, timer_data)
    
    def snooze_alarm(self, timer_id: str, minutes: int = None):
        """Snooze an active alarm"""
        if timer_id not in self.active_alarms:
            return
        
        if minutes is None:
            minutes = self.config.get("alarm", {}).get("snooze_duration", 300) // 60
        
        # Stop current alarm
        self.stop_alarm(timer_id)
        
        # Mark as snoozed
        self.active_alarms[timer_id]["is_snoozed"] = True
        
        # Create snooze timer
        snooze_timer = QTimer()
        snooze_timer.timeout.connect(lambda: self._resume_from_snooze(timer_id))
        snooze_timer.setSingleShot(True)
        snooze_timer.start(minutes * 60 * 1000)  # Convert to milliseconds
        
        self.snooze_timers[timer_id] = snooze_timer
        
        self.alarm_snoozed.emit(timer_id, minutes)
    
    def stop_alarm(self, timer_id: str):
        """Stop an active alarm"""
        if timer_id not in self.active_alarms:
            return
        
        # Stop sound
        self.sound_player.stop_sound()
        
        # Close dialog if open
        if timer_id in self.alarm_dialogs:
            dialog = self.alarm_dialogs[timer_id]
            dialog.close()
            del self.alarm_dialogs[timer_id]
        
        # Cancel snooze timer if exists
        if timer_id in self.snooze_timers:
            self.snooze_timers[timer_id].stop()
            del self.snooze_timers[timer_id]
        
        # Remove from active alarms
        del self.active_alarms[timer_id]
        
        self.alarm_stopped.emit(timer_id)
    
    def stop_all_alarms(self):
        """Stop all active alarms"""
        for timer_id in list(self.active_alarms.keys()):
            self.stop_alarm(timer_id)
    
    def get_active_alarms(self) -> Dict[str, Dict[str, Any]]:
        """Get all active alarms"""
        return self.active_alarms.copy()
    
    def is_alarm_active(self, timer_id: str) -> bool:
        """Check if alarm is active for a timer"""
        return timer_id in self.active_alarms
    
    def update_config(self, config: Dict[str, Any]):
        """Update alarm configuration"""
        self.config = config
    
    def _play_alarm_sound(self):
        """Play the configured alarm sound"""
        alarm_config = self.config.get("alarm", {})
        sound_file = alarm_config.get("sound_file", "")
        volume = alarm_config.get("volume", 0.8)
        
        # Get default sound file if not specified
        if not sound_file:
            sound_file = self._get_default_sound_file()
        
        success = self.sound_player.play_sound(sound_file, volume, loop=True)
        
        if not success:
            print("Failed to play alarm sound")
    
    def _show_notification(self, timer_name: str):
        """Show Windows notification"""
        title = "Timer Finished!"
        message = f'"{timer_name}" has finished'
        
        # Try to get app icon
        icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "app_icon.ico")
        if not os.path.exists(icon_path):
            icon_path = None
        
        success = self.notification_system.show_notification(
            title, message, duration=10, icon_path=icon_path
        )
        
        if not success:
            # Fallback to message box
            self.notification_system.show_message_box(title, message)
    
    def _show_alarm_dialog(self, timer_id: str, timer_name: str):
        """Show alarm dialog with snooze/stop options"""
        snooze_duration = self.config.get("alarm", {}).get("snooze_duration", 300) // 60
        
        dialog = AlarmDialog(timer_name, snooze_duration)
        
        # Connect signals
        dialog.snoozed.connect(lambda minutes: self.snooze_alarm(timer_id, minutes))
        dialog.stopped.connect(lambda: self.stop_alarm(timer_id))
        
        # Store dialog reference
        self.alarm_dialogs[timer_id] = dialog
        
        # Show dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
    
    def _resume_from_snooze(self, timer_id: str):
        """Resume alarm after snooze period"""
        if timer_id not in self.active_alarms:
            return
        
        # Remove from snooze timers
        if timer_id in self.snooze_timers:
            del self.snooze_timers[timer_id]
        
        # Get timer data
        alarm_info = self.active_alarms[timer_id]
        timer_data = alarm_info["timer_data"]
        timer_name = timer_data.get("name", "Timer")
        
        # Mark as no longer snoozed
        alarm_info["is_snoozed"] = False
        
        # Re-trigger alarm
        self._play_alarm_sound()
        self._show_notification(f"{timer_name} (Snoozed)")
        self._show_alarm_dialog(timer_id, timer_name)
    
    def _get_default_sound_file(self) -> str:
        """Get default alarm sound file"""
        # Look for default sound files in assets folder
        assets_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
        
        default_sounds = [
            "default_alarm.wav",
            "alarm.wav",
            "notification.wav",
            "beep.wav"
        ]
        
        for sound_file in default_sounds:
            full_path = os.path.join(assets_dir, sound_file)
            if os.path.exists(full_path):
                return full_path
        
        return ""  # No default sound found
    
    def test_alarm(self) -> bool:
        """Test alarm sound and notification"""
        try:
            # Test notification
            success = self._show_notification("Test Alarm")
            
            # Test sound (play for 2 seconds)
            sound_success = self._play_alarm_sound()
            
            if sound_success:
                # Stop sound after 2 seconds
                QTimer.singleShot(2000, self.sound_player.stop_sound)
            
            return success or sound_success
        except Exception as e:
            print(f"Alarm test failed: {e}")
            return False


def create_default_alarm_sound():
    """Create a default alarm sound file if none exists"""
    try:
        assets_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
        os.makedirs(assets_dir, exist_ok=True)
        
        default_sound_path = os.path.join(assets_dir, "default_alarm.wav")
        
        if os.path.exists(default_sound_path):
            return default_sound_path
        
        # Generate a simple beep sound using winsound if available
        if WINSOUND_AVAILABLE:
            # We can't create a WAV file easily, so just return empty
            # The system will use the built-in sound
            return ""
        
        return ""
    except Exception as e:
        print(f"Failed to create default alarm sound: {e}")
        return ""


# Test if Windows notifications are working
def test_windows_notifications():
    """Test function to check if Windows notifications work"""
    notifier = WindowsNotification()
    return notifier.show_notification("Test", "This is a test notification")


if __name__ == "__main__":
    # Quick test of alarm functionality
    print("Testing alarm components...")
    
    # Test notification
    if test_windows_notifications():
        print("✓ Windows notifications working")
    else:
        print("✗ Windows notifications not working")
    
    # Test sound
    sound_player = AlarmSound()
    if sound_player._play_system_sound(False):
        print("✓ Sound playback working")
    else:
        print("✗ Sound playback not working")
