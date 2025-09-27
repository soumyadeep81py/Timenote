"""
Sidebar Component
Provides navigation and lists for notes, timers, and settings
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QListWidget, QListWidgetItem, QFrame, QScrollArea,
    QMenu, QMessageBox, QLineEdit, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QAction


class SidebarSection(QFrame):
    """Individual section in the sidebar (Notes, Timers, Settings)"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.is_expanded = True
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the section UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)
        
        # Section header
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(8, 4, 8, 4)
        
        self.toggle_btn = QPushButton("▼" if self.is_expanded else "▶")
        self.toggle_btn.setMaximumWidth(20)
        self.toggle_btn.setMaximumHeight(20)
        self.toggle_btn.clicked.connect(self.toggle_section)
        header_layout.addWidget(self.toggle_btn)
        
        self.title_label = QLabel(self.title)
        title_font = QFont()
        title_font.setWeight(QFont.Weight.Bold)
        title_font.setPointSize(11)
        self.title_label.setFont(title_font)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Content area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.content_widget)
    
    def toggle_section(self):
        """Toggle section expanded/collapsed"""
        self.is_expanded = not self.is_expanded
        self.content_widget.setVisible(self.is_expanded)
        self.toggle_btn.setText("▼" if self.is_expanded else "▶")
    
    def add_widget(self, widget):
        """Add a widget to the content area"""
        self.content_layout.addWidget(widget)


class NoteListItem(QListWidgetItem):
    """Custom list item for notes"""
    
    def __init__(self, note_data: dict):
        super().__init__()
        self.note_data = note_data
        self.update_display()
    
    def update_display(self):
        """Update the display text based on note data"""
        title = self.note_data.get("title", "Untitled")
        if len(title) > 30:
            title = title[:27] + "..."
        self.setText(title)
        self.setToolTip(self.note_data.get("content", "")[:100] + "..." 
                       if len(self.note_data.get("content", "")) > 100 
                       else self.note_data.get("content", ""))


class TimerListItem(QListWidgetItem):
    """Custom list item for timers"""
    
    def __init__(self, timer_data: dict):
        super().__init__()
        self.timer_data = timer_data
        self.update_display()
    
    def update_display(self):
        """Update the display text based on timer data"""
        name = self.timer_data.get("name", "Timer")
        remaining = self.timer_data.get("remaining", 0)
        duration = self.timer_data.get("duration", 0)
        
        # Format time display
        hours, remainder = divmod(remaining, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            time_str = f"{minutes:02d}:{seconds:02d}"
        
        status = ""
        if self.timer_data.get("is_active", False):
            status = " ⏵"
        elif self.timer_data.get("is_paused", False):
            status = " ⏸"
        
        self.setText(f"{name} - {time_str}{status}")




class Sidebar(QWidget):
    """Main sidebar widget with navigation and content lists"""
    
    # Signals
    note_selected = pyqtSignal(dict)
    timer_selected = pyqtSignal(dict)
    section_changed = pyqtSignal(str)
    
    def __init__(self, data_handler, parent=None):
        super().__init__(parent)
        self.data_handler = data_handler
        self.active_section = "notes"
        self.current_note_id = None
        self.current_timer_id = None
        
        self.setup_ui()
        self.apply_styles()
        self.load_data()
        
        # Update timer every second for active timers
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_timer_displays)
        self.update_timer.start(1000)
    
    def setup_ui(self):
        """Setup the sidebar UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Scroll area for the content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(scroll)
        
        # Main content widget
        content_widget = QWidget()
        scroll.setWidget(content_widget)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(12)
        
        # Notes section
        self.notes_section = SidebarSection("📝 Notes")
        self.notes_list = QListWidget()
        self.notes_list.itemClicked.connect(self.on_note_selected)
        self.notes_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.notes_list.customContextMenuRequested.connect(self.show_note_context_menu)
        self.notes_section.add_widget(self.notes_list)
        content_layout.addWidget(self.notes_section)
        
        # Timers section
        self.timers_section = SidebarSection("⏲ Timers")
        
        # Timer creation buttons
        timer_buttons_widget = QWidget()
        timer_buttons_layout = QVBoxLayout(timer_buttons_widget)
        timer_buttons_layout.setContentsMargins(0, 0, 0, 8)
        timer_buttons_layout.setSpacing(4)
        
        # Quick timer buttons
        quick_timer_layout = QHBoxLayout()
        
        pomodoro_btn = QPushButton("🍅 25min")
        pomodoro_btn.setToolTip("Start 25-minute Pomodoro timer")
        pomodoro_btn.clicked.connect(lambda: self.create_quick_timer("Pomodoro", 25 * 60))
        quick_timer_layout.addWidget(pomodoro_btn)
        
        break_btn = QPushButton("☕ 5min")
        break_btn.setToolTip("Start 5-minute break timer")
        break_btn.clicked.connect(lambda: self.create_quick_timer("Break", 5 * 60))
        quick_timer_layout.addWidget(break_btn)
        
        timer_buttons_layout.addLayout(quick_timer_layout)
        
        # New custom timer button
        new_timer_btn = QPushButton("+ New Timer")
        new_timer_btn.setToolTip("Create custom timer")
        new_timer_btn.clicked.connect(self.create_custom_timer)
        new_timer_btn.setObjectName("primaryButton")
        timer_buttons_layout.addWidget(new_timer_btn)
        
        self.timers_section.add_widget(timer_buttons_widget)
        
        # Timer list
        self.timers_list = QListWidget()
        self.timers_list.itemClicked.connect(self.on_timer_selected)
        self.timers_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.timers_list.customContextMenuRequested.connect(self.show_timer_context_menu)
        self.timers_section.add_widget(self.timers_list)
        content_layout.addWidget(self.timers_section)
        
        # Settings section
        self.settings_section = SidebarSection("⚙ Settings")
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        
        # Settings buttons
        startup_btn = QPushButton("Startup Settings")
        startup_btn.clicked.connect(lambda: self.section_changed.emit("startup"))
        settings_layout.addWidget(startup_btn)
        
        appearance_btn = QPushButton("Appearance")
        appearance_btn.clicked.connect(lambda: self.section_changed.emit("appearance"))
        settings_layout.addWidget(appearance_btn)
        
        alarm_btn = QPushButton("Alarm Settings")
        alarm_btn.clicked.connect(lambda: self.section_changed.emit("alarm"))
        settings_layout.addWidget(alarm_btn)
        
        self.settings_section.add_widget(settings_widget)
        content_layout.addWidget(self.settings_section)
        
        content_layout.addStretch()
    
    def apply_styles(self):
        """Apply Notion-like styling to the sidebar"""
        style = """
        Sidebar {
            background-color: #1a1a1a;
            border-right: 1px solid #3f3f3f;
        }
        
        SidebarSection {
            background-color: transparent;
            border: none;
        }
        
        QLabel {
            color: #ffffff;
            font-weight: bold;
        }
        
        QLabel:hover {
            color: #ffffff;
            text-shadow: 0 0 10px rgba(255, 255, 255, 0.7);
        }
        
        QPushButton {
            background-color: transparent;
            border: none;
            border-radius: 4px;
            padding: 4px 8px;
            color: #ffffff;
            text-align: left;
            font-size: 11px;
            font-weight: 500;
        }
        
        QPushButton:hover {
            background-color: #3f3f3f;
            color: #ffffff;
            text-shadow: 0 0 8px rgba(255, 255, 255, 0.5);
        }
        
        QListWidget {
            background-color: transparent;
            border: none;
            outline: none;
        }
        
        QListWidget::item {
            background-color: transparent;
            border: none;
            border-radius: 4px;
            padding: 8px;
            margin: 1px;
            color: #ffffff;
            font-weight: 500;
        }
        
        QListWidget::item:hover {
            background-color: #3f3f3f;
            color: #ffffff;
            text-shadow: 0 0 6px rgba(255, 255, 255, 0.4);
        }
        
        QListWidget::item:selected {
            background-color: #2383e2;
            color: white;
        }
        
        QScrollArea {
            border: none;
            background-color: transparent;
        }
        
        QScrollBar:vertical {
            border: none;
            background-color: #f7f7f5;
            width: 8px;
            border-radius: 4px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #d1d1d1;
            border-radius: 4px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #a8a8a8;
        }
        """
        self.setStyleSheet(style)
    
    def load_data(self):
        """Load notes and timers from storage"""
        self.refresh_notes()
        self.refresh_timers()
    
    def refresh_notes(self):
        """Refresh the notes list"""
        self.notes_list.clear()
        notes = self.data_handler.load_notes()
        
        # Sort notes by modified date (most recent first)
        notes.sort(key=lambda x: x.get("modified", ""), reverse=True)
        
        for note in notes:
            item = NoteListItem(note)
            self.notes_list.addItem(item)
    
    def refresh_timers(self):
        """Refresh the timers list"""
        self.timers_list.clear()
        timers = self.data_handler.load_timers()
        
        # Sort timers by creation date (most recent first)
        timers.sort(key=lambda x: x.get("created", ""), reverse=True)
        
        for timer in timers:
            item = TimerListItem(timer)
            self.timers_list.addItem(item)
    
    
    def update_timer_displays(self):
        """Update timer display text for active timers"""
        for i in range(self.timers_list.count()):
            item = self.timers_list.item(i)
            if isinstance(item, TimerListItem):
                item.update_display()
    
    def on_note_selected(self, item):
        """Handle note selection"""
        if isinstance(item, NoteListItem):
            self.current_note_id = item.note_data["id"]
            self.note_selected.emit(item.note_data)
            self.set_active_section("notes")
    
    def on_timer_selected(self, item):
        """Handle timer selection"""
        if isinstance(item, TimerListItem):
            self.current_timer_id = item.timer_data["id"]
            self.timer_selected.emit(item.timer_data)
            self.set_active_section("timers")
    
    def show_note_context_menu(self, position):
        """Show context menu for notes"""
        item = self.notes_list.itemAt(position)
        if not isinstance(item, NoteListItem):
            return
        
        menu = QMenu(self)
        
        # Delete action
        delete_action = QAction("Delete Note", self)
        delete_action.triggered.connect(lambda: self.delete_note(item.note_data["id"]))
        menu.addAction(delete_action)
        
        # Duplicate action
        duplicate_action = QAction("Duplicate Note", self)
        duplicate_action.triggered.connect(lambda: self.duplicate_note(item.note_data))
        menu.addAction(duplicate_action)
        
        menu.exec(self.notes_list.mapToGlobal(position))
    
    def show_timer_context_menu(self, position):
        """Show context menu for timers"""
        item = self.timers_list.itemAt(position)
        if not isinstance(item, TimerListItem):
            return
        
        menu = QMenu(self)
        
        # Delete action
        delete_action = QAction("Delete Timer", self)
        delete_action.triggered.connect(lambda: self.delete_timer(item.timer_data["id"]))
        menu.addAction(delete_action)
        
        menu.exec(self.timers_list.mapToGlobal(position))
    
    def delete_note(self, note_id: str):
        """Delete a note with confirmation"""
        reply = QMessageBox.question(
            self, "Delete Note", 
            "Are you sure you want to delete this note?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.data_handler.delete_note(note_id)
            self.refresh_notes()
    
    def duplicate_note(self, note_data: dict):
        """Duplicate a note"""
        title = f"{note_data['title']} (Copy)"
        content = note_data['content']
        self.data_handler.add_note(title, content)
        self.refresh_notes()
    
    def delete_timer(self, timer_id: str):
        """Delete a timer with confirmation"""
        reply = QMessageBox.question(
            self, "Delete Timer", 
            "Are you sure you want to delete this timer?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.data_handler.delete_timer(timer_id)
            self.refresh_timers()
    
    def select_note(self, note_id: str):
        """Select a specific note by ID"""
        for i in range(self.notes_list.count()):
            item = self.notes_list.item(i)
            if isinstance(item, NoteListItem) and item.note_data["id"] == note_id:
                self.notes_list.setCurrentItem(item)
                self.on_note_selected(item)
                break
    
    def set_active_section(self, section: str):
        """Set the active section and emit signal"""
        self.active_section = section
        self.section_changed.emit(section)
    
    def get_active_section(self) -> str:
        """Get the currently active section"""
        return self.active_section
    
    def create_quick_timer(self, name: str, duration: int):
        """Create and start a quick timer (Pomodoro, Break, etc.)"""
        try:
            # Create the timer
            timer = self.data_handler.add_timer(name, duration)
            
            # Refresh the timer list to show the new timer
            self.refresh_timers()
            
            # Switch to timers section and emit signal
            self.set_active_section("timers")
            
            # Select the newly created timer
            if timer:
                for i in range(self.timers_list.count()):
                    item = self.timers_list.item(i)
                    if isinstance(item, TimerListItem) and item.timer_data["id"] == timer["id"]:
                        self.timers_list.setCurrentItem(item)
                        self.timer_selected.emit(timer)
                        break
        except Exception as e:
            print(f"Error creating quick timer: {e}")
            QMessageBox.warning(self, "Error", f"Failed to create timer: {str(e)}")
    
    
    def create_custom_timer(self):
        """Create a custom timer by switching to timer interface and showing new timer dialog"""
        # Switch to timers section first
        self.set_active_section("timers")
        
        # Import here to avoid circular imports
        from ui.main_panel import NewTimerDialog
        from PyQt6.QtWidgets import QDialog
        
        # Show the new timer dialog
        dialog = NewTimerDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            timer_data = dialog.get_timer_data()
            
            # Create new timer in storage
            timer = self.data_handler.add_timer(
                timer_data["name"], 
                timer_data["duration"]
            )
            
            # Refresh the timer list to show the new timer
            self.refresh_timers()
            
            # Select the newly created timer
            if timer:
                for i in range(self.timers_list.count()):
                    item = self.timers_list.item(i)
                    if isinstance(item, TimerListItem) and item.timer_data["id"] == timer["id"]:
                        self.timers_list.setCurrentItem(item)
                        self.timer_selected.emit(timer)
                        break
