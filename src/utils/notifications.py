"""
Notification and Sound Alert System
Handles Windows notifications and sound alerts for timer/alarm completions
"""

import os
import threading
import winsound
from typing import Optional, Dict, Any

try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    notification = None


class NotificationManager:
    """Manages system notifications and sound alerts"""
    
    def __init__(self, app_name: str = "Timenote"):
        self.app_name = app_name
        self.icon_path = self._get_icon_path()
        self.default_sound_path = self._get_default_sound_path()
        self.sound_enabled = True
        self.notification_enabled = True
        
    def _get_icon_path(self) -> str:
        """Get path to application icon for notifications"""
        # Try to find icon in assets folder
        base_dir = os.path.dirname(os.path.dirname(__file__))
        icon_path = os.path.join(base_dir, "assets", "icon.ico")
        
        if os.path.exists(icon_path):
            return icon_path
        
        # Fallback to default Windows icon
        return ""
    
    def _get_default_sound_path(self) -> str:
        """Get path to default alarm sound"""
        # Try to find custom alarm sound in assets folder
        base_dir = os.path.dirname(os.path.dirname(__file__))
        sound_path = os.path.join(base_dir, "assets", "alarm.mp3")
        
        if os.path.exists(sound_path):
            return sound_path
        
        # No default custom sound
        return ""
    
    def show_timer_finished_notification(self, timer_data: Dict[str, Any]) -> bool:
        """Show notification when a timer finishes"""
        if not self.notification_enabled or not PLYER_AVAILABLE:
            return False
        
        timer_name = timer_data.get("name", "Timer")
        duration = timer_data.get("duration", 0)
        
        # Format duration for display
        hours, remainder = divmod(duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            duration_str = f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            duration_str = f"{minutes}m {seconds}s"
        else:
            duration_str = f"{seconds}s"
        
        title = f"⏰ {timer_name} Finished!"
        message = f"Your {duration_str} timer has completed."
        
        try:
            notification.notify(
                title=title,
                message=message,
                app_name=self.app_name,
                app_icon=self.icon_path,
                timeout=10,  # Show for 10 seconds
                ticker=timer_name
            )
            return True
        except Exception as e:
            print(f"Failed to show notification: {e}")
            return False
    
    def show_alarm_notification(self, alarm_data: Dict[str, Any]) -> bool:
        """Show notification when an alarm triggers"""
        if not self.notification_enabled or not PLYER_AVAILABLE:
            return False
        
        alarm_name = alarm_data.get("name", "Alarm")
        alarm_time = alarm_data.get("time", "")
        
        title = f"🔔 {alarm_name}"
        message = f"Alarm set for {alarm_time}"
        
        try:
            notification.notify(
                title=title,
                message=message,
                app_name=self.app_name,
                app_icon=self.icon_path,
                timeout=15,  # Show for 15 seconds for alarms
                ticker=alarm_name
            )
            return True
        except Exception as e:
            print(f"Failed to show alarm notification: {e}")
            return False
    
    def play_timer_sound(self, sound_file: Optional[str] = None, volume: float = 0.8) -> bool:
        """Play sound alert when timer finishes"""
        if not self.sound_enabled:
            return False
        
        def play_sound():
            try:
                # Determine which sound file to use
                target_sound = sound_file or self.default_sound_path
                
                if target_sound and os.path.exists(target_sound):
                    # Play custom sound file (MP3 or WAV)
                    if target_sound.lower().endswith('.mp3'):
                        # For MP3 files, use PlaySound with SND_FILENAME
                        winsound.PlaySound(target_sound, winsound.SND_FILENAME | winsound.SND_ASYNC)
                    else:
                        # For WAV files, use standard PlaySound
                        winsound.PlaySound(target_sound, winsound.SND_FILENAME | winsound.SND_ASYNC)
                else:
                    # Play system notification sound
                    winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC)
                return True
            except Exception as e:
                print(f"Failed to play sound: {e}")
                # Fallback to simple beep
                try:
                    winsound.Beep(800, 500)  # 800Hz for 500ms
                    return True
                except Exception:
                    return False
        
        # Play sound in separate thread to avoid blocking UI
        sound_thread = threading.Thread(target=play_sound, daemon=True)
        sound_thread.start()
        return True
    
    def play_alarm_sound(self, sound_file: Optional[str] = None, volume: float = 0.8, repeat_count: int = 3) -> bool:
        """Play alarm sound (repeated for more attention)"""
        if not self.sound_enabled:
            return False
        
        def play_alarm():
            try:
                # Determine which sound file to use
                target_sound = sound_file or self.default_sound_path
                
                for _ in range(repeat_count):
                    if target_sound and os.path.exists(target_sound):
                        # Play custom sound file
                        if target_sound.lower().endswith('.mp3'):
                            # For MP3 files, use PlaySound with SND_FILENAME
                            winsound.PlaySound(target_sound, winsound.SND_FILENAME)
                        else:
                            # For WAV files, use standard PlaySound
                            winsound.PlaySound(target_sound, winsound.SND_FILENAME)
                    else:
                        # Play system alarm sound
                        winsound.PlaySound("SystemHand", winsound.SND_ALIAS)
                    
                    # Short pause between repeats
                    import time
                    time.sleep(0.5)
                return True
            except Exception as e:
                print(f"Failed to play alarm sound: {e}")
                # Fallback to beep sequence
                try:
                    for _ in range(repeat_count):
                        winsound.Beep(1000, 300)  # 1000Hz for 300ms
                        import time
                        time.sleep(0.2)
                    return True
                except Exception:
                    return False
        
        # Play alarm in separate thread
        alarm_thread = threading.Thread(target=play_alarm, daemon=True)
        alarm_thread.start()
        return True
    
    def set_notification_enabled(self, enabled: bool):
        """Enable or disable notifications"""
        self.notification_enabled = enabled
    
    def set_sound_enabled(self, enabled: bool):
        """Enable or disable sound alerts"""
        self.sound_enabled = enabled
    
    def is_notification_available(self) -> bool:
        """Check if notifications are available on this system"""
        return PLYER_AVAILABLE
    
    def test_notification(self) -> bool:
        """Test notification system"""
        if not PLYER_AVAILABLE:
            return False
        
        try:
            notification.notify(
                title="Timenote Test",
                message="Notification system is working!",
                app_name=self.app_name,
                app_icon=self.icon_path,
                timeout=5
            )
            return True
        except Exception as e:
            print(f"Notification test failed: {e}")
            return False
    
    def test_sound(self, sound_file: Optional[str] = None) -> bool:
        """Test sound system"""
        return self.play_timer_sound(sound_file)


# Global instance for easy access
notification_manager = NotificationManager()


def show_timer_notification(timer_data: Dict[str, Any], sound_file: Optional[str] = None, volume: float = 0.8):
    """Convenience function to show timer finished notification with sound"""
    notification_manager.show_timer_finished_notification(timer_data)
    notification_manager.play_timer_sound(sound_file, volume)


def show_alarm_notification(alarm_data: Dict[str, Any], sound_file: Optional[str] = None, volume: float = 0.8):
    """Convenience function to show alarm notification with sound"""
    notification_manager.show_alarm_notification(alarm_data)
    notification_manager.play_alarm_sound(sound_file, volume)
