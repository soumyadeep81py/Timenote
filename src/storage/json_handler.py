"""
JSON Handler for persistent storage
Handles reading and writing of notes, timers, and configuration data
"""

import json
import os
from typing import Any, Dict, List, Optional
from datetime import datetime

class JSONHandler:
    """Handles JSON file operations for the application"""
    
    def __init__(self, data_dir: str = None):
        """Initialize the JSON handler with data directory"""
        if data_dir is None:
            # Use app data directory in user's home folder
            app_data_dir = os.path.join(os.path.expanduser("~"), "Timenote")
            os.makedirs(app_data_dir, exist_ok=True)
            self.data_dir = app_data_dir
        else:
            self.data_dir = data_dir
            os.makedirs(self.data_dir, exist_ok=True)
        
        # File paths
        self.notes_file = os.path.join(self.data_dir, "notes.json")
        self.timers_file = os.path.join(self.data_dir, "timers.json")
        self.config_file = os.path.join(self.data_dir, "config.json")
    
    def read_json_file(self, filepath: str) -> Dict[str, Any]:
        """Read and parse a JSON file"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
            print(f"Error reading {filepath}: {e}")
            return {}
    
    def write_json_file(self, filepath: str, data: Dict[str, Any]) -> bool:
        """Write data to a JSON file"""
        try:
            # Create backup if file exists
            if os.path.exists(filepath):
                backup_path = filepath + ".backup"
                try:
                    os.rename(filepath, backup_path)
                except OSError:
                    pass  # Backup failed, continue anyway
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            # Remove backup if write was successful
            backup_path = filepath + ".backup"
            if os.path.exists(backup_path):
                try:
                    os.remove(backup_path)
                except OSError:
                    pass  # Backup removal failed, not critical
            
            return True
        except (PermissionError, OSError) as e:
            print(f"Error writing {filepath}: {e}")
            return False
    
    # Notes management
    def load_notes(self) -> List[Dict[str, Any]]:
        """Load all notes from storage"""
        data = self.read_json_file(self.notes_file)
        return data.get("notes", [])
    
    def save_notes(self, notes: List[Dict[str, Any]]) -> bool:
        """Save notes to storage"""
        data = {
            "notes": notes,
            "last_updated": datetime.now().isoformat()
        }
        return self.write_json_file(self.notes_file, data)
    
    def add_note(self, title: str, content: str, note_id: str = None) -> Dict[str, Any]:
        """Add a new note"""
        if note_id is None:
            note_id = str(hash(f"{title}_{datetime.now().isoformat()}"))
        
        note = {
            "id": note_id,
            "title": title,
            "content": content,
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat()
        }
        
        notes = self.load_notes()
        notes.append(note)
        self.save_notes(notes)
        return note
    
    def update_note(self, note_id: str, title: str = None, content: str = None) -> bool:
        """Update an existing note"""
        notes = self.load_notes()
        for note in notes:
            if note["id"] == note_id:
                if title is not None:
                    note["title"] = title
                if content is not None:
                    note["content"] = content
                note["modified"] = datetime.now().isoformat()
                return self.save_notes(notes)
        return False
    
    def delete_note(self, note_id: str) -> bool:
        """Delete a note"""
        notes = self.load_notes()
        notes = [note for note in notes if note["id"] != note_id]
        return self.save_notes(notes)
    
    # Timer management
    def load_timers(self) -> List[Dict[str, Any]]:
        """Load all active timers from storage"""
        data = self.read_json_file(self.timers_file)
        return data.get("timers", [])
    
    def save_timers(self, timers: List[Dict[str, Any]]) -> bool:
        """Save timers to storage"""
        data = {
            "timers": timers,
            "last_updated": datetime.now().isoformat()
        }
        return self.write_json_file(self.timers_file, data)
    
    def add_timer(self, name: str, duration: int, timer_id: str = None) -> Dict[str, Any]:
        """Add a new timer"""
        if timer_id is None:
            timer_id = str(hash(f"{name}_{datetime.now().isoformat()}"))
        
        timer = {
            "id": timer_id,
            "name": name,
            "duration": duration,  # in seconds
            "remaining": duration,
            "created": datetime.now().isoformat(),
            "started": None,
            "is_active": False,
            "is_paused": False
        }
        
        timers = self.load_timers()
        timers.append(timer)
        self.save_timers(timers)
        return timer
    
    def update_timer(self, timer_id: str, **kwargs) -> bool:
        """Update timer properties"""
        timers = self.load_timers()
        for timer in timers:
            if timer["id"] == timer_id:
                for key, value in kwargs.items():
                    if key in timer:
                        timer[key] = value
                return self.save_timers(timers)
        return False
    
    def delete_timer(self, timer_id: str) -> bool:
        """Delete a timer"""
        timers = self.load_timers()
        timers = [timer for timer in timers if timer["id"] != timer_id]
        return self.save_timers(timers)
    
    # Configuration management
    def load_config(self) -> Dict[str, Any]:
        """Load application configuration"""
        default_config = {
            "window": {
                "width": 1200,
                "height": 800,
                "x": 100,
                "y": 100
            },
            "alarm": {
                "sound_file": "default_alarm.wav",
                "volume": 0.8,
                "snooze_duration": 300  # 5 minutes in seconds
            },
            "startup": {
                "auto_start": False,
                "minimize_to_tray": True
            },
            "ui": {
                "theme": "light",
                "font_size": 12,
                "sidebar_width": 250
            }
        }
        
        config = self.read_json_file(self.config_file)
        # Merge with defaults to ensure all keys exist
        for key, value in default_config.items():
            if key not in config:
                config[key] = value
            elif isinstance(value, dict):
                for subkey, subvalue in value.items():
                    if subkey not in config[key]:
                        config[key][subkey] = subvalue
        
        return config
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save application configuration"""
        return self.write_json_file(self.config_file, config)
    
    def update_config(self, section: str, key: str, value: Any) -> bool:
        """Update a specific configuration value"""
        config = self.load_config()
        if section not in config:
            config[section] = {}
        config[section][key] = value
        return self.save_config(config)
    
    def get_data_dir(self) -> str:
        """Get the data directory path"""
        return self.data_dir
