"""
Notes Feature
Provides note management functionality with auto-save and search
"""

import os
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal, QTimer


class NotesManager(QObject):
    """Manages notes functionality including creation, editing, deletion, and search"""
    
    # Signals
    note_created = pyqtSignal(dict)  # Emitted when a new note is created
    note_updated = pyqtSignal(dict)  # Emitted when a note is updated
    note_deleted = pyqtSignal(str)   # Emitted when a note is deleted (note_id)
    notes_reloaded = pyqtSignal(list) # Emitted when notes are reloaded
    
    def __init__(self, data_handler):
        super().__init__()
        self.data_handler = data_handler
        self._notes_cache = []
        self._last_search_results = []
        
        # Auto-save timer for batch operations
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._perform_auto_save)
        self.auto_save_timer.setSingleShot(True)
        
        # Load initial notes
        self.reload_notes()
    
    def create_note(self, title: str = "New Note", content: str = "") -> Dict[str, Any]:
        """Create a new note"""
        # Generate unique ID based on timestamp and title
        note_id = f"note_{int(datetime.now().timestamp() * 1000)}_{hash(title) % 1000000}"
        
        note = self.data_handler.add_note(title, content, note_id)
        
        if note:
            self._notes_cache.append(note)
            self.note_created.emit(note)
            return note
        
        return {}
    
    def get_note(self, note_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific note by ID"""
        for note in self._notes_cache:
            if note["id"] == note_id:
                return note
        
        # If not in cache, try to load from storage
        all_notes = self.data_handler.load_notes()
        for note in all_notes:
            if note["id"] == note_id:
                return note
        
        return None
    
    def update_note(self, note_id: str, title: str = None, content: str = None, auto_save: bool = True) -> bool:
        """Update a note's title and/or content"""
        # Update in cache first
        note_updated = False
        for note in self._notes_cache:
            if note["id"] == note_id:
                if title is not None:
                    note["title"] = title
                if content is not None:
                    note["content"] = content
                note["modified"] = datetime.now().isoformat()
                note_updated = True
                break
        
        if not note_updated:
            return False
        
        # Save to storage
        success = self.data_handler.update_note(note_id, title, content)
        
        if success:
            updated_note = self.get_note(note_id)
            if updated_note:
                self.note_updated.emit(updated_note)
            
            # Schedule auto-save if enabled
            if auto_save:
                self._schedule_auto_save()
        
        return success
    
    def delete_note(self, note_id: str) -> bool:
        """Delete a note"""
        # Remove from cache
        self._notes_cache = [note for note in self._notes_cache if note["id"] != note_id]
        
        # Delete from storage
        success = self.data_handler.delete_note(note_id)
        
        if success:
            self.note_deleted.emit(note_id)
        
        return success
    
    def duplicate_note(self, note_id: str) -> Optional[Dict[str, Any]]:
        """Duplicate an existing note"""
        original_note = self.get_note(note_id)
        if not original_note:
            return None
        
        # Create duplicate with modified title
        duplicate_title = f"{original_note['title']} (Copy)"
        duplicate_content = original_note['content']
        
        return self.create_note(duplicate_title, duplicate_content)
    
    def get_all_notes(self, reload_from_storage: bool = False) -> List[Dict[str, Any]]:
        """Get all notes, optionally reloading from storage"""
        if reload_from_storage:
            self.reload_notes()
        
        return self._notes_cache.copy()
    
    def reload_notes(self):
        """Reload all notes from storage"""
        self._notes_cache = self.data_handler.load_notes()
        self.notes_reloaded.emit(self._notes_cache.copy())
    
    def search_notes(self, query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Search notes by title and content"""
        if not query.strip():
            self._last_search_results = self._notes_cache.copy()
            return self._last_search_results
        
        query = query.strip()
        if not case_sensitive:
            query = query.lower()
        
        results = []
        
        for note in self._notes_cache:
            title = note.get("title", "")
            content = note.get("content", "")
            
            if not case_sensitive:
                title = title.lower()
                content = content.lower()
            
            # Search in title and content
            if query in title or query in content:
                # Add relevance score for sorting
                score = 0
                if query in title:
                    score += 10  # Title matches are more relevant
                if query in content:
                    score += content.count(query)  # Multiple matches increase relevance
                
                note_copy = note.copy()
                note_copy["_search_score"] = score
                results.append(note_copy)
        
        # Sort by relevance (score) and then by modification date
        results.sort(key=lambda x: (x["_search_score"], x.get("modified", "")), reverse=True)
        
        # Remove search score from results
        for note in results:
            note.pop("_search_score", None)
        
        self._last_search_results = results
        return results
    
    def get_notes_by_date_range(self, start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
        """Get notes created within a date range"""
        filtered_notes = []
        
        for note in self._notes_cache:
            created_str = note.get("created", "")
            if not created_str:
                continue
            
            try:
                created_date = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                
                # Check date range
                if start_date and created_date < start_date:
                    continue
                if end_date and created_date > end_date:
                    continue
                
                filtered_notes.append(note)
            except (ValueError, TypeError):
                continue  # Skip notes with invalid date formats
        
        return filtered_notes
    
    def get_notes_statistics(self) -> Dict[str, Any]:
        """Get statistics about the notes collection"""
        total_notes = len(self._notes_cache)
        total_words = 0
        total_characters = 0
        
        for note in self._notes_cache:
            content = note.get("content", "")
            total_words += len(content.split())
            total_characters += len(content)
        
        # Find most recent and oldest notes
        if self._notes_cache:
            sorted_notes = sorted(self._notes_cache, key=lambda x: x.get("modified", ""))
            oldest_note = sorted_notes[0] if sorted_notes else None
            newest_note = sorted_notes[-1] if sorted_notes else None
        else:
            oldest_note = newest_note = None
        
        return {
            "total_notes": total_notes,
            "total_words": total_words,
            "total_characters": total_characters,
            "average_words_per_note": total_words / total_notes if total_notes > 0 else 0,
            "oldest_note": oldest_note,
            "newest_note": newest_note
        }
    
    def export_notes_to_text(self, file_path: str, include_metadata: bool = True) -> bool:
        """Export all notes to a text file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("Notion App Notes Export\n")
                f.write("=" * 50 + "\n\n")
                
                for i, note in enumerate(self._notes_cache, 1):
                    f.write(f"Note #{i}: {note.get('title', 'Untitled')}\n")
                    f.write("-" * 30 + "\n")
                    
                    if include_metadata:
                        f.write(f"Created: {note.get('created', 'Unknown')}\n")
                        f.write(f"Modified: {note.get('modified', 'Unknown')}\n")
                        f.write(f"ID: {note.get('id', 'Unknown')}\n\n")
                    
                    f.write(note.get('content', ''))
                    f.write("\n\n" + "=" * 50 + "\n\n")
            
            return True
        except (IOError, OSError, PermissionError) as e:
            print(f"Error exporting notes: {e}")
            return False
    
    def import_notes_from_text(self, file_path: str) -> int:
        """Import notes from a text file (simple format)"""
        imported_count = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple import: split by double newlines and treat each section as a note
            sections = content.split('\n\n')
            
            for section in sections:
                section = section.strip()
                if not section or len(section) < 10:  # Skip very short sections
                    continue
                
                # Try to extract title from first line
                lines = section.split('\n')
                title = lines[0].strip() if lines else "Imported Note"
                content_text = '\n'.join(lines[1:]).strip() if len(lines) > 1 else section
                
                # Create note
                if self.create_note(title, content_text):
                    imported_count += 1
            
        except (IOError, OSError, PermissionError) as e:
            print(f"Error importing notes: {e}")
        
        return imported_count
    
    def get_notes_by_word_count(self, min_words: int = 0, max_words: int = None) -> List[Dict[str, Any]]:
        """Get notes filtered by word count"""
        filtered_notes = []
        
        for note in self._notes_cache:
            content = note.get("content", "")
            word_count = len(content.split())
            
            if word_count < min_words:
                continue
            if max_words is not None and word_count > max_words:
                continue
            
            note_copy = note.copy()
            note_copy["_word_count"] = word_count
            filtered_notes.append(note_copy)
        
        # Sort by word count
        filtered_notes.sort(key=lambda x: x["_word_count"], reverse=True)
        
        # Remove word count from results
        for note in filtered_notes:
            note.pop("_word_count", None)
        
        return filtered_notes
    
    def _schedule_auto_save(self):
        """Schedule an auto-save operation"""
        self.auto_save_timer.start(5000)  # Auto-save after 5 seconds of inactivity
    
    def _perform_auto_save(self):
        """Perform auto-save operation"""
        # This could be used for batch operations or cleanup
        pass
    
    def cleanup_empty_notes(self) -> int:
        """Remove notes that have no title and no content"""
        deleted_count = 0
        notes_to_delete = []
        
        for note in self._notes_cache:
            title = note.get("title", "").strip()
            content = note.get("content", "").strip()
            
            if not title and not content:
                notes_to_delete.append(note["id"])
        
        for note_id in notes_to_delete:
            if self.delete_note(note_id):
                deleted_count += 1
        
        return deleted_count
    
    def get_recent_notes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most recently modified notes"""
        sorted_notes = sorted(
            self._notes_cache, 
            key=lambda x: x.get("modified", ""), 
            reverse=True
        )
        
        return sorted_notes[:limit]
    
    def get_note_preview(self, note_id: str, max_chars: int = 200) -> str:
        """Get a preview of a note's content"""
        note = self.get_note(note_id)
        if not note:
            return ""
        
        content = note.get("content", "").strip()
        if len(content) <= max_chars:
            return content
        
        # Find a good breaking point (end of sentence or word)
        preview = content[:max_chars]
        
        # Try to break at sentence end
        last_sentence_end = max(preview.rfind('.'), preview.rfind('!'), preview.rfind('?'))
        if last_sentence_end > max_chars // 2:
            return preview[:last_sentence_end + 1]
        
        # Fall back to word boundary
        last_space = preview.rfind(' ')
        if last_space > max_chars // 2:
            return preview[:last_space] + "..."
        
        return preview + "..."
