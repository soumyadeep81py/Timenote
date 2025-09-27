"""
Timer Feature
Provides countdown timer functionality with persistence and multiple timers support
"""

import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal, QTimer


class TimerState:
    """Constants for timer states"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"


class CountdownTimer(QObject):
    """Individual countdown timer with persistence"""
    
    # Signals
    tick = pyqtSignal(int)  # Emitted every second with remaining time
    finished = pyqtSignal()  # Emitted when timer reaches zero
    started = pyqtSignal()   # Emitted when timer starts
    paused = pyqtSignal()    # Emitted when timer is paused
    resumed = pyqtSignal()   # Emitted when timer is resumed
    stopped = pyqtSignal()   # Emitted when timer is stopped/reset
    
    def __init__(self, timer_id: str, name: str, duration: int, data_handler):
        super().__init__()
        self.timer_id = timer_id
        self.name = name
        self.original_duration = duration  # in seconds
        self.remaining_time = duration
        self.data_handler = data_handler
        
        self.state = TimerState.STOPPED
        self.start_timestamp = None
        self.pause_timestamp = None
        
        # Qt timer for updates
        self.qt_timer = QTimer()
        self.qt_timer.timeout.connect(self._update_countdown)
        
        # Load persisted state
        self._load_state()
    
    def start(self) -> bool:
        """Start the timer"""
        if self.state == TimerState.RUNNING:
            return False
        
        if self.remaining_time <= 0:
            self.remaining_time = self.original_duration
        
        self.state = TimerState.RUNNING
        self.start_timestamp = time.time()
        self.pause_timestamp = None
        
        self.qt_timer.start(1000)  # Update every second
        self._save_state()
        self.started.emit()
        return True
    
    def pause(self) -> bool:
        """Pause the timer"""
        if self.state != TimerState.RUNNING:
            return False
        
        self.state = TimerState.PAUSED
        self.pause_timestamp = time.time()
        
        self.qt_timer.stop()
        self._save_state()
        self.paused.emit()
        return True
    
    def resume(self) -> bool:
        """Resume the paused timer"""
        if self.state != TimerState.PAUSED:
            return False
        
        if self.pause_timestamp and self.start_timestamp:
            # Adjust start timestamp to account for pause duration
            pause_duration = time.time() - self.pause_timestamp
            self.start_timestamp += pause_duration
        
        self.state = TimerState.RUNNING
        self.pause_timestamp = None
        
        self.qt_timer.start(1000)
        self._save_state()
        self.resumed.emit()
        return True
    
    def stop(self) -> bool:
        """Stop and reset the timer"""
        self.state = TimerState.STOPPED
        self.qt_timer.stop()
        self.remaining_time = self.original_duration
        self.start_timestamp = None
        self.pause_timestamp = None
        
        self._save_state()
        self.stopped.emit()
        return True
    
    def reset(self) -> bool:
        """Reset timer to original duration"""
        was_running = self.state == TimerState.RUNNING
        
        self.stop()
        
        if was_running:
            self.start()
        
        return True
    
    def add_time(self, seconds: int) -> bool:
        """Add time to the timer"""
        if seconds <= 0:
            return False
        
        self.remaining_time += seconds
        self.original_duration += seconds
        self._save_state()
        return True
    
    def set_duration(self, seconds: int) -> bool:
        """Set a new duration for the timer"""
        if seconds <= 0:
            return False
        
        was_running = self.state == TimerState.RUNNING
        self.stop()
        
        self.original_duration = seconds
        self.remaining_time = seconds
        
        if was_running:
            self.start()
        
        self._save_state()
        return True
    
    def get_progress(self) -> float:
        """Get progress as percentage (0.0 to 1.0)"""
        if self.original_duration <= 0:
            return 1.0
        
        elapsed = self.original_duration - self.remaining_time
        return min(elapsed / self.original_duration, 1.0)
    
    def get_state_info(self) -> Dict[str, Any]:
        """Get current timer state information"""
        return {
            "id": self.timer_id,
            "name": self.name,
            "duration": self.original_duration,
            "remaining": self.remaining_time,
            "state": self.state,
            "progress": self.get_progress(),
            "started": self.start_timestamp,
            "paused": self.pause_timestamp,
            "is_running": self.state == TimerState.RUNNING,
            "is_paused": self.state == TimerState.PAUSED,
            "is_finished": self.state == TimerState.FINISHED
        }
    
    def _update_countdown(self):
        """Update countdown timer"""
        if self.state != TimerState.RUNNING or not self.start_timestamp:
            return
        
        elapsed = time.time() - self.start_timestamp
        self.remaining_time = max(0, self.original_duration - int(elapsed))
        
        self.tick.emit(self.remaining_time)
        
        if self.remaining_time <= 0:
            self.state = TimerState.FINISHED
            self.qt_timer.stop()
            self._save_state()
            self.finished.emit()
    
    def _save_state(self):
        """Save current state to persistent storage"""
        state_data = {
            "name": self.name,
            "duration": self.original_duration,
            "remaining": self.remaining_time,
            "state": self.state,
            "start_timestamp": self.start_timestamp,
            "pause_timestamp": self.pause_timestamp,
            "is_active": self.state == TimerState.RUNNING,
            "is_paused": self.state == TimerState.PAUSED
        }
        
        self.data_handler.update_timer(self.timer_id, **state_data)
    
    def _load_state(self):
        """Load state from persistent storage"""
        timers = self.data_handler.load_timers()
        
        for timer_data in timers:
            if timer_data.get("id") == self.timer_id:
                self.name = timer_data.get("name", self.name)
                self.original_duration = timer_data.get("duration", self.original_duration)
                self.remaining_time = timer_data.get("remaining", self.remaining_time)
                self.start_timestamp = timer_data.get("start_timestamp")
                self.pause_timestamp = timer_data.get("pause_timestamp")
                
                # Determine state
                if timer_data.get("is_active", False):
                    self.state = TimerState.RUNNING
                    
                    # Check if timer should have finished while app was closed
                    if self.start_timestamp:
                        elapsed = time.time() - self.start_timestamp
                        self.remaining_time = max(0, self.original_duration - int(elapsed))
                        
                        if self.remaining_time <= 0:
                            self.state = TimerState.FINISHED
                        else:
                            # Resume the timer
                            self.qt_timer.start(1000)
                    
                elif timer_data.get("is_paused", False):
                    self.state = TimerState.PAUSED
                elif self.remaining_time <= 0:
                    self.state = TimerState.FINISHED
                else:
                    self.state = TimerState.STOPPED
                
                break


class TimerManager(QObject):
    """Manages multiple countdown timers"""
    
    # Signals
    timer_added = pyqtSignal(str)      # Emitted when a timer is added (timer_id)
    timer_removed = pyqtSignal(str)    # Emitted when a timer is removed (timer_id)
    timer_finished = pyqtSignal(str, dict)  # Emitted when a timer finishes (timer_id, timer_data)
    timers_updated = pyqtSignal()      # Emitted when timer list is updated
    
    def __init__(self, data_handler):
        super().__init__()
        self.data_handler = data_handler
        self.timers: Dict[str, CountdownTimer] = {}
        
        # Load existing timers
        self._load_existing_timers()
        
        # Cleanup timer for finished timers
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self._cleanup_finished_timers)
        self.cleanup_timer.start(60000)  # Cleanup every minute
    
    def create_timer(self, name: str, duration: int) -> Optional[str]:
        """Create a new timer"""
        if duration <= 0:
            return None
        
        # Create timer in storage first
        timer_data = self.data_handler.add_timer(name, duration)
        if not timer_data:
            return None
        
        timer_id = timer_data["id"]
        
        # Create timer object
        timer = CountdownTimer(timer_id, name, duration, self.data_handler)
        
        # Connect signals
        timer.finished.connect(lambda: self._on_timer_finished(timer_id))
        timer.tick.connect(lambda remaining: self._on_timer_tick(timer_id, remaining))
        
        self.timers[timer_id] = timer
        self.timer_added.emit(timer_id)
        self.timers_updated.emit()
        
        return timer_id
    
    def get_timer(self, timer_id: str) -> Optional[CountdownTimer]:
        """Get a timer by ID"""
        return self.timers.get(timer_id)
    
    def remove_timer(self, timer_id: str) -> bool:
        """Remove a timer"""
        if timer_id not in self.timers:
            return False
        
        # Stop timer if running
        timer = self.timers[timer_id]
        timer.stop()
        
        # Remove from storage
        self.data_handler.delete_timer(timer_id)
        
        # Remove from memory
        del self.timers[timer_id]
        
        self.timer_removed.emit(timer_id)
        self.timers_updated.emit()
        return True
    
    def get_all_timers(self) -> List[CountdownTimer]:
        """Get all timers"""
        return list(self.timers.values())
    
    def get_running_timers(self) -> List[CountdownTimer]:
        """Get all currently running timers"""
        return [timer for timer in self.timers.values() if timer.state == TimerState.RUNNING]
    
    def get_finished_timers(self) -> List[CountdownTimer]:
        """Get all finished timers"""
        return [timer for timer in self.timers.values() if timer.state == TimerState.FINISHED]
    
    def start_timer(self, timer_id: str) -> bool:
        """Start a specific timer"""
        timer = self.timers.get(timer_id)
        if timer:
            return timer.start()
        return False
    
    def pause_timer(self, timer_id: str) -> bool:
        """Pause a specific timer"""
        timer = self.timers.get(timer_id)
        if timer:
            return timer.pause()
        return False
    
    def resume_timer(self, timer_id: str) -> bool:
        """Resume a specific timer"""
        timer = self.timers.get(timer_id)
        if timer:
            return timer.resume()
        return False
    
    def stop_timer(self, timer_id: str) -> bool:
        """Stop a specific timer"""
        timer = self.timers.get(timer_id)
        if timer:
            return timer.stop()
        return False
    
    def reset_timer(self, timer_id: str) -> bool:
        """Reset a specific timer"""
        timer = self.timers.get(timer_id)
        if timer:
            return timer.reset()
        return False
    
    def renew_timer(self, timer_id: str) -> bool:
        """Renew a timer (reset and start)"""
        timer = self.timers.get(timer_id)
        if timer:
            timer.reset()
            return timer.start()
        return False
    
    def add_time_to_timer(self, timer_id: str, seconds: int) -> bool:
        """Add time to a specific timer"""
        timer = self.timers.get(timer_id)
        if timer:
            return timer.add_time(seconds)
        return False
    
    def set_timer_duration(self, timer_id: str, seconds: int) -> bool:
        """Set duration for a specific timer"""
        timer = self.timers.get(timer_id)
        if timer:
            return timer.set_duration(seconds)
        return False
    
    def pause_all_timers(self) -> int:
        """Pause all running timers"""
        paused_count = 0
        for timer in self.timers.values():
            if timer.state == TimerState.RUNNING and timer.pause():
                paused_count += 1
        return paused_count
    
    def resume_all_timers(self) -> int:
        """Resume all paused timers"""
        resumed_count = 0
        for timer in self.timers.values():
            if timer.state == TimerState.PAUSED and timer.resume():
                resumed_count += 1
        return resumed_count
    
    def stop_all_timers(self) -> int:
        """Stop all active timers"""
        stopped_count = 0
        for timer in self.timers.values():
            if timer.state in [TimerState.RUNNING, TimerState.PAUSED] and timer.stop():
                stopped_count += 1
        return stopped_count
    
    def get_timer_statistics(self) -> Dict[str, Any]:
        """Get statistics about timers"""
        total_timers = len(self.timers)
        running_count = len(self.get_running_timers())
        paused_count = len([t for t in self.timers.values() if t.state == TimerState.PAUSED])
        finished_count = len(self.get_finished_timers())
        stopped_count = total_timers - running_count - paused_count - finished_count
        
        # Calculate total time
        total_duration = sum(timer.original_duration for timer in self.timers.values())
        total_remaining = sum(timer.remaining_time for timer in self.timers.values())
        total_elapsed = total_duration - total_remaining
        
        return {
            "total_timers": total_timers,
            "running_timers": running_count,
            "paused_timers": paused_count,
            "finished_timers": finished_count,
            "stopped_timers": stopped_count,
            "total_duration_seconds": total_duration,
            "total_elapsed_seconds": total_elapsed,
            "total_remaining_seconds": total_remaining
        }
    
    def create_preset_timer(self, preset_name: str) -> Optional[str]:
        """Create a timer from common presets"""
        presets = {
            "pomodoro": {"name": "Pomodoro Timer", "duration": 25 * 60},  # 25 minutes
            "short_break": {"name": "Short Break", "duration": 5 * 60},    # 5 minutes
            "long_break": {"name": "Long Break", "duration": 15 * 60},     # 15 minutes
            "work_hour": {"name": "Work Hour", "duration": 60 * 60},       # 1 hour
            "half_hour": {"name": "Half Hour", "duration": 30 * 60},       # 30 minutes
            "quick_timer": {"name": "Quick Timer", "duration": 10 * 60},   # 10 minutes
            "meditation": {"name": "Meditation", "duration": 20 * 60},     # 20 minutes
            "exercise": {"name": "Exercise", "duration": 45 * 60},         # 45 minutes
        }
        
        preset = presets.get(preset_name.lower())
        if preset:
            return self.create_timer(preset["name"], preset["duration"])
        
        return None
    
    def export_timers_data(self) -> Dict[str, Any]:
        """Export all timer data for backup"""
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "timers": []
        }
        
        for timer in self.timers.values():
            export_data["timers"].append(timer.get_state_info())
        
        return export_data
    
    def _load_existing_timers(self):
        """Load existing timers from storage"""
        timer_data_list = self.data_handler.load_timers()
        
        for timer_data in timer_data_list:
            timer_id = timer_data.get("id")
            name = timer_data.get("name", "Timer")
            duration = timer_data.get("duration", 300)  # Default 5 minutes
            
            if timer_id:
                timer = CountdownTimer(timer_id, name, duration, self.data_handler)
                timer.finished.connect(lambda tid=timer_id: self._on_timer_finished(tid))
                timer.tick.connect(lambda remaining, tid=timer_id: self._on_timer_tick(tid, remaining))
                
                self.timers[timer_id] = timer
    
    def _on_timer_finished(self, timer_id: str):
        """Handle timer finished event"""
        timer = self.timers.get(timer_id)
        if timer:
            timer_data = timer.get_state_info()
            self.timer_finished.emit(timer_id, timer_data)
    
    def _on_timer_tick(self, timer_id: str, remaining: int):
        """Handle timer tick event"""
        # Could be used for notifications at specific intervals
        pass
    
    def _cleanup_finished_timers(self):
        """Clean up old finished timers (optional)"""
        # Remove finished timers that are older than 24 hours
        cutoff_time = time.time() - (24 * 60 * 60)  # 24 hours ago
        
        timers_to_remove = []
        for timer_id, timer in self.timers.items():
            if (timer.state == TimerState.FINISHED and 
                timer.start_timestamp and 
                timer.start_timestamp < cutoff_time):
                timers_to_remove.append(timer_id)
        
        for timer_id in timers_to_remove:
            self.remove_timer(timer_id)


def format_time(seconds: int) -> str:
    """Format seconds into HH:MM:SS or MM:SS format"""
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"


def parse_time_string(time_str: str) -> int:
    """Parse time string like '1h 30m 45s' or '25:30' into seconds"""
    time_str = time_str.strip().lower()
    
    # Handle HH:MM:SS or MM:SS format
    if ':' in time_str:
        parts = time_str.split(':')
        if len(parts) == 2:  # MM:SS
            try:
                minutes, seconds = map(int, parts)
                return minutes * 60 + seconds
            except ValueError:
                return 0
        elif len(parts) == 3:  # HH:MM:SS
            try:
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
            except ValueError:
                return 0
    
    # Handle text format like '1h 30m 45s'
    total_seconds = 0
    import re
    
    # Find hours
    hours_match = re.search(r'(\d+)\s*h', time_str)
    if hours_match:
        total_seconds += int(hours_match.group(1)) * 3600
    
    # Find minutes
    minutes_match = re.search(r'(\d+)\s*m', time_str)
    if minutes_match:
        total_seconds += int(minutes_match.group(1)) * 60
    
    # Find seconds
    seconds_match = re.search(r'(\d+)\s*s', time_str)
    if seconds_match:
        total_seconds += int(seconds_match.group(1))
    
    # If no units found, assume it's just seconds
    if total_seconds == 0:
        try:
            total_seconds = int(time_str)
        except ValueError:
            pass
    
    return max(0, total_seconds)
