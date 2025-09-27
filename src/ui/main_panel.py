"""
Main Panel Component
Displays notes editor, timer interface, and settings
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QTextEdit,
    QLineEdit, QLabel, QPushButton, QProgressBar, QSpinBox,
    QCheckBox, QComboBox, QFileDialog, QSlider, QGroupBox,
    QFormLayout, QMessageBox, QDialog, QDialogButtonBox, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QUrl
from PyQt6.QtGui import QFont, QTextCharFormat, QTextCursor, QAction, QDesktopServices

from utils.notifications import show_timer_notification


class NoteEditor(QWidget):
    """Note editing interface"""
    
    note_updated = pyqtSignal()
    
    def __init__(self, data_handler, parent=None):
        super().__init__(parent)
        self.data_handler = data_handler
        self.current_note = None
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.save_note)
        self.auto_save_timer.setSingleShot(True)
        
        self.setup_ui()
        self.apply_styles()
    
    def setup_ui(self):
        """Setup the note editor UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Title editor
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Untitled")
        self.title_edit.textChanged.connect(self.on_content_changed)
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setWeight(QFont.Weight.Bold)
        self.title_edit.setFont(title_font)
        layout.addWidget(self.title_edit)
        
        # Content editor
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("Start writing...")
        self.content_edit.textChanged.connect(self.on_content_changed)
        content_font = QFont()
        content_font.setPointSize(12)
        self.content_edit.setFont(content_font)
        layout.addWidget(self.content_edit)
        
        # Status bar
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.status_label)
    
    def apply_styles(self):
        """Apply enhanced dark mode styling to the note editor"""
        style = """
        NoteEditor {
            background-color: #1a1a1a;
        }
        
        QLineEdit {
            background-color: #1a1a1a;
            border: none;
            border-bottom: 2px solid transparent;
            color: #ffffff;
            padding: 12px 0px;
            font-weight: bold;
        }
        
        QLineEdit:focus {
            background-color: #1a1a1a;
            border-bottom: 2px solid #2383e2;
        }
        
        QLineEdit::placeholder {
            color: #666666;
        }
        
        QTextEdit {
            background-color: #1a1a1a;
            border: none;
            color: #ffffff;
            selection-background-color: #2383e2;
            selection-color: white;
            line-height: 1.6;
        }
        
        QTextEdit:focus {
            background-color: #1a1a1a;
            border: none;
        }
        
        QTextEdit::placeholder {
            color: #666666;
        }
        
        QLabel {
            color: #888888;
            font-size: 11px;
            background-color: transparent;
        }
        """
        self.setStyleSheet(style)
    
    def load_note(self, note_data: dict):
        """Load a note for editing"""
        self.current_note = note_data
        
        # Block signals to avoid triggering auto-save during load
        self.title_edit.blockSignals(True)
        self.content_edit.blockSignals(True)
        
        self.title_edit.setText(note_data.get("title", ""))
        self.content_edit.setText(note_data.get("content", ""))
        
        # Re-enable signals
        self.title_edit.blockSignals(False)
        self.content_edit.blockSignals(False)
        
        # Focus on content if title is empty, otherwise focus on title
        if not note_data.get("title", ""):
            self.title_edit.setFocus()
        else:
            self.content_edit.setFocus()
        
        self.update_status()
    
    def on_content_changed(self):
        """Handle content changes"""
        if self.current_note:
            # Start/restart auto-save timer
            self.auto_save_timer.start(2000)  # Auto-save after 2 seconds of inactivity
            self.status_label.setText("Unsaved changes...")
    
    def save_note(self):
        """Save the current note"""
        if not self.current_note:
            return
        
        title = self.title_edit.text().strip() or "Untitled"
        content = self.content_edit.toPlainText()
        
        success = self.data_handler.update_note(
            self.current_note["id"], 
            title=title, 
            content=content
        )
        
        if success:
            self.current_note["title"] = title
            self.current_note["content"] = content
            self.note_updated.emit()
            self.update_status()
        
        return success
    
    def update_status(self):
        """Update the status display"""
        if self.current_note:
            word_count = len(self.content_edit.toPlainText().split())
            char_count = len(self.content_edit.toPlainText())
            self.status_label.setText(f"Saved • {word_count} words, {char_count} characters")
        else:
            self.status_label.setText("")
    
    def save_current_data(self):
        """Force save current data"""
        if self.auto_save_timer.isActive():
            self.auto_save_timer.stop()
            self.save_note()


class TimerWidget(QWidget):
    """Individual timer display widget"""
    
    timer_updated = pyqtSignal()
    alarm_triggered = pyqtSignal(dict)
    timer_deleted = pyqtSignal(str)  # Emits timer ID when deleted
    
    def __init__(self, timer_data: dict, data_handler, parent=None):
        super().__init__(parent)
        self.timer_data = timer_data
        self.data_handler = data_handler
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_countdown)
        
        self.setup_ui()
        self.apply_styles()
        self.update_display()
        
        # Start timer if it's active
        if self.timer_data.get("is_active", False):
            self.update_timer.start(1000)
    
    def setup_ui(self):
        """Setup the timer widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Timer name
        self.name_label = QLabel(self.timer_data.get("name", "Timer"))
        name_font = QFont()
        name_font.setPointSize(16)
        name_font.setWeight(QFont.Weight.Bold)
        self.name_label.setFont(name_font)
        layout.addWidget(self.name_label)
        
        # Time display
        self.time_label = QLabel()
        time_font = QFont()
        time_font.setPointSize(24)
        time_font.setWeight(QFont.Weight.Bold)
        self.time_label.setFont(time_font)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.time_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximum(self.timer_data.get("duration", 1))
        layout.addWidget(self.progress_bar)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_pause_btn = QPushButton()
        self.start_pause_btn.clicked.connect(self.toggle_timer)
        button_layout.addWidget(self.start_pause_btn)
        
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset_timer)
        button_layout.addWidget(self.reset_btn)
        
        self.renew_btn = QPushButton("Renew")
        self.renew_btn.clicked.connect(self.renew_timer)
        button_layout.addWidget(self.renew_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_timer)
        self.delete_btn.setObjectName("deleteButton")
        button_layout.addWidget(self.delete_btn)
        
        layout.addLayout(button_layout)
        
        # Enable context menu for right-click functionality
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def apply_styles(self):
        """Apply dark theme styling to the timer widget"""
        style = """
        TimerWidget {
            background-color: #2f2f2f;
            border: 1px solid #3f3f3f;
            border-radius: 8px;
            margin: 8px;
        }
        
        QLabel {
            color: #e9e9e7;
            background-color: transparent;
        }
        
        QProgressBar {
            border: 1px solid #3f3f3f;
            border-radius: 4px;
            background-color: #1f1f1f;
            height: 8px;
            text-align: center;
        }
        
        QProgressBar::chunk {
            background-color: #4a9eff;
            border-radius: 4px;
        }
        
        QPushButton {
            background-color: #2f2f2f;
            border: 1px solid #3f3f3f;
            border-radius: 6px;
            padding: 8px 16px;
            color: #e9e9e7;
            font-weight: 500;
            min-width: 70px;
        }
        
        QPushButton:hover {
            background-color: #3f3f3f;
            border-color: #4f4f4f;
        }
        
        QPushButton:pressed {
            background-color: #1f1f1f;
        }
        
        QPushButton:disabled {
            background-color: #1a1a1a;
            color: #666666;
            border-color: #2a2a2a;
        }
        """
        self.setStyleSheet(style)
    
    def update_display(self):
        """Update the timer display"""
        remaining = self.timer_data.get("remaining", 0)
        duration = self.timer_data.get("duration", 1)
        is_active = self.timer_data.get("is_active", False)
        is_paused = self.timer_data.get("is_paused", False)
        
        # Format time display
        hours, remainder = divmod(remaining, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            time_str = f"{minutes:02d}:{seconds:02d}"
        
        self.time_label.setText(time_str)
        self.progress_bar.setValue(duration - remaining)
        
        # Update button text
        if is_active:
            self.start_pause_btn.setText("Pause")
        elif is_paused:
            self.start_pause_btn.setText("Resume")
        else:
            self.start_pause_btn.setText("Start")
    
    def toggle_timer(self):
        """Start, pause, or resume timer"""
        is_active = self.timer_data.get("is_active", False)
        is_paused = self.timer_data.get("is_paused", False)
        
        if is_active:
            # Pause timer
            self.timer_data["is_active"] = False
            self.timer_data["is_paused"] = True
            self.update_timer.stop()
        elif is_paused:
            # Resume timer
            self.timer_data["is_active"] = True
            self.timer_data["is_paused"] = False
            self.update_timer.start(1000)
        else:
            # Start timer
            self.timer_data["is_active"] = True
            self.timer_data["is_paused"] = False
            self.timer_data["started"] = QTimer().remainingTime()
            self.update_timer.start(1000)
        
        self.data_handler.update_timer(self.timer_data["id"], **self.timer_data)
        self.update_display()
        self.timer_updated.emit()
    
    def reset_timer(self):
        """Reset timer to original duration"""
        self.timer_data["remaining"] = self.timer_data["duration"]
        self.timer_data["is_active"] = False
        self.timer_data["is_paused"] = False
        self.timer_data["started"] = None
        self.update_timer.stop()
        
        self.data_handler.update_timer(self.timer_data["id"], **self.timer_data)
        self.update_display()
        self.timer_updated.emit()
    
    def renew_timer(self):
        """Renew timer (reset and start)"""
        self.reset_timer()
        self.toggle_timer()
    
    def update_countdown(self):
        """Update countdown every second"""
        remaining = self.timer_data.get("remaining", 0)
        
        if remaining <= 0:
            # Timer finished
            self.timer_data["remaining"] = 0
            self.timer_data["is_active"] = False
            self.timer_data["is_paused"] = False
            self.update_timer.stop()
            
            self.alarm_triggered.emit(self.timer_data)
        else:
            # Decrease remaining time
            self.timer_data["remaining"] = remaining - 1
        
        self.data_handler.update_timer(self.timer_data["id"], **self.timer_data)
        self.update_display()
        self.timer_updated.emit()
    
    def delete_timer(self):
        """Delete this timer with confirmation"""
        timer_name = self.timer_data.get("name", "Timer")
        
        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "Delete Timer",
            f"Are you sure you want to delete '{timer_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Stop timer if running
            self.update_timer.stop()
            
            # Delete from storage
            success = self.data_handler.delete_timer(self.timer_data["id"])
            
            if success:
                self.timer_deleted.emit(self.timer_data["id"])
                self.timer_updated.emit()
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Failed to delete timer. Please try again.",
                    QMessageBox.StandardButton.Ok
                )
    
    def show_context_menu(self, position):
        """Show context menu for right-click actions"""
        menu = QMenu(self)
        
        # Timer actions
        if self.timer_data.get("is_active", False):
            pause_action = QAction("Pause Timer", self)
            pause_action.triggered.connect(self.toggle_timer)
            menu.addAction(pause_action)
        elif self.timer_data.get("is_paused", False):
            resume_action = QAction("Resume Timer", self)
            resume_action.triggered.connect(self.toggle_timer)
            menu.addAction(resume_action)
        else:
            start_action = QAction("Start Timer", self)
            start_action.triggered.connect(self.toggle_timer)
            menu.addAction(start_action)
        
        reset_action = QAction("Reset Timer", self)
        reset_action.triggered.connect(self.reset_timer)
        menu.addAction(reset_action)
        
        renew_action = QAction("Renew Timer", self)
        renew_action.triggered.connect(self.renew_timer)
        menu.addAction(renew_action)
        
        menu.addSeparator()
        
        # Delete action
        delete_action = QAction("Delete Timer", self)
        delete_action.triggered.connect(self.delete_timer)
        menu.addAction(delete_action)
        
        # Show menu at cursor position
        menu.exec(self.mapToGlobal(position))


class NewTimerDialog(QDialog):
    """Dialog for creating new timers"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Timer")
        self.setModal(True)
        self.setFixedSize(400, 300)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Timer name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Timer Name:"))
        self.name_edit = QLineEdit("Work Timer")
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # Duration settings
        duration_group = QGroupBox("Duration")
        duration_layout = QFormLayout(duration_group)
        
        self.hours_spin = QSpinBox()
        self.hours_spin.setRange(0, 23)
        duration_layout.addRow("Hours:", self.hours_spin)
        
        self.minutes_spin = QSpinBox()
        self.minutes_spin.setRange(0, 59)
        self.minutes_spin.setValue(25)  # Default 25 minutes
        duration_layout.addRow("Minutes:", self.minutes_spin)
        
        self.seconds_spin = QSpinBox()
        self.seconds_spin.setRange(0, 59)
        duration_layout.addRow("Seconds:", self.seconds_spin)
        
        layout.addWidget(duration_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_timer_data(self):
        """Get the timer configuration data"""
        name = self.name_edit.text().strip() or "Timer"
        duration = (
            self.hours_spin.value() * 3600 + 
            self.minutes_spin.value() * 60 + 
            self.seconds_spin.value()
        )
        
        return {
            "name": name,
            "duration": max(duration, 1)  # Minimum 1 second
        }


class TimerInterface(QWidget):
    """Timer management interface"""
    
    timer_updated = pyqtSignal()
    alarm_triggered = pyqtSignal(dict)
    
    def __init__(self, data_handler, parent=None):
        super().__init__(parent)
        self.data_handler = data_handler
        self.timer_widgets = []
        
        self.setup_ui()
        self.load_timers()
    
    def setup_ui(self):
        """Setup the timer interface UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header with new timer button
        header_layout = QHBoxLayout()
        title = QLabel("Timers")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setWeight(QFont.Weight.Bold)
        title.setFont(title_font)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        new_timer_btn = QPushButton("+ New Timer")
        new_timer_btn.clicked.connect(self.show_new_timer_dialog)
        header_layout.addWidget(new_timer_btn)
        
        layout.addLayout(header_layout)
        
        # Timer widgets container
        self.timers_layout = QVBoxLayout()
        layout.addLayout(self.timers_layout)
        
        layout.addStretch()
    
    def load_timers(self):
        """Load and display all timers"""
        # Clear existing widgets
        for widget in self.timer_widgets:
            widget.setParent(None)
        self.timer_widgets.clear()
        
        # Load timers from storage
        timers = self.data_handler.load_timers()
        
        for timer_data in timers:
            timer_widget = TimerWidget(timer_data, self.data_handler)
            timer_widget.timer_updated.connect(self.timer_updated.emit)
            timer_widget.alarm_triggered.connect(self.alarm_triggered.emit)
            timer_widget.timer_deleted.connect(self.on_timer_deleted)
            
            self.timer_widgets.append(timer_widget)
            self.timers_layout.addWidget(timer_widget)
    
    def show_new_timer_dialog(self):
        """Show dialog to create a new timer"""
        dialog = NewTimerDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            timer_data = dialog.get_timer_data()
            
            # Create new timer in storage
            new_timer = self.data_handler.add_timer(
                timer_data["name"], 
                timer_data["duration"]
            )
            
            # Refresh display
            self.load_timers()
            self.timer_updated.emit()
    
    def on_timer_deleted(self, timer_id: str):
        """Handle timer deletion by refreshing the display"""
        self.load_timers()
        self.timer_updated.emit()
    
    def load_timer(self, timer_data: dict):
        """Load a specific timer for viewing"""
        # This method is called when a timer is selected from sidebar
        # For now, we just refresh to show all timers
        self.load_timers()


class SettingsInterface(QWidget):
    """Settings interface"""
    
    def __init__(self, data_handler, parent=None):
        super().__init__(parent)
        self.data_handler = data_handler
        self.config = data_handler.load_config()
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Setup the settings interface UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Title
        title = QLabel("Settings")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setWeight(QFont.Weight.Bold)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Settings sections
        self.setup_startup_settings(layout)
        self.setup_appearance_settings(layout)
        self.setup_alarm_settings(layout)
        self.setup_about_section(layout)
        
        layout.addStretch()
    
    def setup_startup_settings(self, parent_layout):
        """Setup startup settings section"""
        group = QGroupBox("Startup")
        layout = QFormLayout(group)
        
        self.auto_start_cb = QCheckBox("Start with Windows")
        self.auto_start_cb.stateChanged.connect(self.save_settings)
        layout.addRow(self.auto_start_cb)
        
        self.minimize_to_tray_cb = QCheckBox("Minimize to system tray")
        self.minimize_to_tray_cb.stateChanged.connect(self.save_settings)
        layout.addRow(self.minimize_to_tray_cb)
        
        parent_layout.addWidget(group)
    
    def setup_appearance_settings(self, parent_layout):
        """Setup appearance settings section"""
        group = QGroupBox("Appearance")
        layout = QFormLayout(group)
        
        # Theme info (read-only)
        theme_label = QLabel("Dark Mode (Always On)")
        layout.addRow("Theme:", theme_label)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.valueChanged.connect(self.save_settings)
        layout.addRow("Font Size:", self.font_size_spin)
        
        parent_layout.addWidget(group)
    
    def setup_alarm_settings(self, parent_layout):
        """Setup alarm settings section"""
        group = QGroupBox("Alarms")
        layout = QFormLayout(group)
        
        # Sound file selection
        sound_layout = QHBoxLayout()
        self.sound_file_edit = QLineEdit()
        sound_layout.addWidget(self.sound_file_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_sound_file)
        sound_layout.addWidget(browse_btn)
        
        layout.addRow("Alarm Sound:", sound_layout)
        
        # Volume slider
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.valueChanged.connect(self.save_settings)
        layout.addRow("Volume:", self.volume_slider)
        
        # Snooze duration
        self.snooze_spin = QSpinBox()
        self.snooze_spin.setRange(1, 60)
        self.snooze_spin.setSuffix(" minutes")
        self.snooze_spin.valueChanged.connect(self.save_settings)
        layout.addRow("Snooze Duration:", self.snooze_spin)
        
        parent_layout.addWidget(group)
    
    def load_settings(self):
        """Load settings from config"""
        # Startup settings
        startup_config = self.config.get("startup", {})
        self.auto_start_cb.setChecked(startup_config.get("auto_start", False))
        self.minimize_to_tray_cb.setChecked(startup_config.get("minimize_to_tray", True))
        
        # UI settings
        ui_config = self.config.get("ui", {})
        self.font_size_spin.setValue(ui_config.get("font_size", 12))
        
        # Alarm settings
        alarm_config = self.config.get("alarm", {})
        self.sound_file_edit.setText(alarm_config.get("sound_file", ""))
        self.volume_slider.setValue(int(alarm_config.get("volume", 0.8) * 100))
        self.snooze_spin.setValue(alarm_config.get("snooze_duration", 300) // 60)
    
    def save_settings(self):
        """Save settings to config"""
        # Update startup settings
        self.data_handler.update_config("startup", "auto_start", self.auto_start_cb.isChecked())
        self.data_handler.update_config("startup", "minimize_to_tray", self.minimize_to_tray_cb.isChecked())
        
        # Update UI settings (always dark mode)
        self.data_handler.update_config("ui", "theme", "dark")
        self.data_handler.update_config("ui", "font_size", self.font_size_spin.value())
        
        # Update alarm settings
        self.data_handler.update_config("alarm", "sound_file", self.sound_file_edit.text())
        self.data_handler.update_config("alarm", "volume", self.volume_slider.value() / 100.0)
        self.data_handler.update_config("alarm", "snooze_duration", self.snooze_spin.value() * 60)
    
    def browse_sound_file(self):
        """Browse for alarm sound file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Alarm Sound", 
            "", 
            "Audio Files (*.wav *.mp3 *.ogg);;All Files (*)"
        )
        
        if file_path:
            self.sound_file_edit.setText(file_path)
            self.save_settings()
    
    def setup_about_section(self, parent_layout):
        """Setup about section with credits and GitHub link"""
        group = QGroupBox("About Timenote")
        layout = QFormLayout(group)
        
        # App info
        version_label = QLabel("Version 1.0.0")
        layout.addRow("Version:", version_label)
        
        author_label = QLabel("Created by Soumyadeep Ghosh")
        layout.addRow("Author:", author_label)
        
        # GitHub link button
        github_btn = QPushButton("View on GitHub")
        github_btn.clicked.connect(self.open_github)
        layout.addRow("Source Code:", github_btn)
        
        # About button
        about_btn = QPushButton("About...")
        about_btn.clicked.connect(self.show_about_dialog)
        layout.addRow("More Info:", about_btn)
        
        parent_layout.addWidget(group)
    
    def open_github(self):
        """Open GitHub repository in default browser"""
        github_url = "https://github.com/LEG1ON/timenote"  # Replace with your actual GitHub URL
        QDesktopServices.openUrl(QUrl(github_url))
    
    def show_about_dialog(self):
        """Show about dialog with full credits"""
        dialog = AboutDialog(self)
        dialog.exec()


class AboutDialog(QDialog):
    """About dialog with credits and information"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Timenote")
        self.setModal(True)
        self.setFixedSize(450, 350)
        self.setup_ui()
        self.apply_styles()
    
    def setup_ui(self):
        """Setup the about dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # App title and version
        title_label = QLabel("Timenote")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setWeight(QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        version_label = QLabel("Version 1.0.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)
        
        layout.addWidget(QLabel(""))  # Spacer
        
        # Description
        description = QLabel(
            "A clean, Notion-like note-taking and timer application.\n\n"
            "Features:\n"
            "• Note taking with auto-save\n"
            "• Multiple countdown timers\n"
            "• Dark theme interface\n"
            "• System tray integration\n"
            "• Desktop notifications\n"
            "• Sound alerts"
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(description)
        
        layout.addWidget(QLabel(""))  # Spacer
        
        # Credits
        credits_label = QLabel("Created by Soumyadeep Ghosh")
        credits_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(credits_label)
        
        # GitHub link
        github_btn = QPushButton("View on GitHub")
        github_btn.clicked.connect(self.open_github)
        layout.addWidget(github_btn)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setDefault(True)
        layout.addWidget(close_btn)
    
    def apply_styles(self):
        """Apply dark theme styling to the about dialog"""
        style = """
        AboutDialog {
            background-color: #191919;
            color: #e9e9e7;
        }
        
        QLabel {
            color: #e9e9e7;
            background-color: transparent;
        }
        
        QPushButton {
            background-color: #2f2f2f;
            border: 1px solid #3f3f3f;
            border-radius: 6px;
            padding: 8px 16px;
            color: #e9e9e7;
            font-weight: 500;
            min-height: 32px;
        }
        
        QPushButton:hover {
            background-color: #3f3f3f;
            border-color: #4f4f4f;
        }
        
        QPushButton:pressed {
            background-color: #1f1f1f;
        }
        
        QPushButton:default {
            background-color: #4a9eff;
            border-color: #4a9eff;
        }
        
        QPushButton:default:hover {
            background-color: #3a8eef;
            border-color: #3a8eef;
        }
        """
        self.setStyleSheet(style)
    
    def open_github(self):
        """Open GitHub repository in default browser"""
        github_url = "https://github.com/LEG1ON/timenote"  # Replace with your actual GitHub URL
        QDesktopServices.openUrl(QUrl(github_url))


class MainPanel(QStackedWidget):
    """Main content panel that switches between notes, timers, and settings"""
    
    note_updated = pyqtSignal()
    timer_updated = pyqtSignal()
    alarm_triggered = pyqtSignal(dict)
    
    def __init__(self, data_handler, parent=None):
        super().__init__(parent)
        self.data_handler = data_handler
        
        self.setup_ui()
        self.apply_styles()
    
    def setup_ui(self):
        """Setup the main panel UI"""
        # Note editor
        self.note_editor = NoteEditor(self.data_handler)
        self.note_editor.note_updated.connect(self.note_updated.emit)
        self.addWidget(self.note_editor)
        
        # Timer interface
        self.timer_interface = TimerInterface(self.data_handler)
        self.timer_interface.timer_updated.connect(self.timer_updated.emit)
        self.timer_interface.alarm_triggered.connect(self.alarm_triggered.emit)
        self.addWidget(self.timer_interface)
        
        # Settings interface
        self.settings_interface = SettingsInterface(self.data_handler)
        self.addWidget(self.settings_interface)
        
        # Welcome screen (default)
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        welcome_label = QLabel("Welcome to Timenote")
        welcome_font = QFont()
        welcome_font.setPointSize(24)
        welcome_font.setWeight(QFont.Weight.Bold)
        welcome_label.setFont(welcome_font)
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(welcome_label)
        
        subtitle_label = QLabel("Your notes and timers in one place")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(subtitle_label)
        
        self.addWidget(welcome_widget)
        
        # Show welcome screen initially
        self.setCurrentWidget(welcome_widget)
    
    def apply_styles(self):
        """Apply dark theme styling to the main panel"""
        style = """
        MainPanel {
            background-color: #1a1a1a;
        }
        
        QStackedWidget {
            background-color: #1a1a1a;
        }
        
        QWidget {
            background-color: #1a1a1a;
        }
        
        QLabel {
            color: #ffffff;
            background-color: transparent;
        }
        
        QLabel:hover {
            color: #ffffff;
        }
        """
        self.setStyleSheet(style)
    
    def load_note(self, note_data: dict):
        """Load a note for editing"""
        self.note_editor.load_note(note_data)
        self.setCurrentWidget(self.note_editor)
    
    def load_timer(self, timer_data: dict):
        """Load a timer for viewing"""
        self.timer_interface.load_timer(timer_data)
        self.setCurrentWidget(self.timer_interface)
    
    def change_section(self, section: str):
        """Change to a specific section"""
        if section == "notes":
            self.setCurrentWidget(self.note_editor)
        elif section == "timers":
            self.setCurrentWidget(self.timer_interface)
        elif section in ["startup", "appearance", "alarm", "settings"]:
            self.setCurrentWidget(self.settings_interface)
    
    def show_new_timer_dialog(self):
        """Show new timer dialog"""
        self.timer_interface.show_new_timer_dialog()
        self.setCurrentWidget(self.timer_interface)
    
    def save_current_data(self):
        """Save current data"""
        if self.currentWidget() == self.note_editor:
            self.note_editor.save_current_data()
