"""
Main Window with Notion-like UI
Provides the main application interface with sidebar and main panel
"""

import os
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QSplitter, QFrame, QLabel, QPushButton, QToolBar,
    QSystemTrayIcon, QMenu, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QAction, QFont, QPixmap

from storage import JSONHandler
from .sidebar import Sidebar
from .main_panel import MainPanel
from .toolbar import NotionToolbar
from utils.notifications import show_timer_notification


class MainWindow(QMainWindow):
    """Main application window with Notion-like interface"""
    
    # Signals
    note_selected = pyqtSignal(dict)
    timer_selected = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        
        # Initialize data handler
        self.data_handler = JSONHandler()
        
        # Load configuration
        self.config = self.data_handler.load_config()
        
        # Initialize UI components
        self.sidebar = None
        self.main_panel = None
        self.toolbar = None
        self.system_tray = None
        
        # Setup UI
        self.setup_ui()
        self.setup_system_tray()
        self.setup_connections()
        self.load_window_state()
        
        # Auto-save timer
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.start(30000)  # Auto-save every 30 seconds
    
    def setup_ui(self):
        """Setup the main user interface"""
        self.setWindowTitle("Timenote")
        self.setMinimumSize(800, 600)
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create and setup toolbar
        self.toolbar = NotionToolbar(self)
        main_layout.addWidget(self.toolbar)
        
        # Create splitter for sidebar and main content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Create sidebar
        self.sidebar = Sidebar(self.data_handler)
        self.sidebar.setMaximumWidth(300)
        self.sidebar.setMinimumWidth(200)
        splitter.addWidget(self.sidebar)
        
        # Create main panel
        self.main_panel = MainPanel(self.data_handler)
        splitter.addWidget(self.main_panel)
        
        # Set splitter proportions
        sidebar_width = self.config.get("ui", {}).get("sidebar_width", 250)
        splitter.setSizes([sidebar_width, 950])
        
        # Apply styling
        self.apply_styles()
    
    def setup_system_tray(self):
        """Setup system tray icon and menu"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        
        # Create system tray icon
        self.system_tray = QSystemTrayIcon(self)
        
        # Set icon (use default if custom icon not available)
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icon.ico")
        if os.path.exists(icon_path):
            self.system_tray.setIcon(QIcon(icon_path))
        else:
            # Use application icon or default
            self.system_tray.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))
        
        # Create tray menu
        tray_menu = QMenu()
        
        # Quick actions
        new_note_action = QAction("New Note", self)
        new_note_action.triggered.connect(self.toolbar.new_note_clicked)
        tray_menu.addAction(new_note_action)
        
        new_timer_action = QAction("Start Timer", self)
        new_timer_action.triggered.connect(self.toolbar.new_timer_clicked)
        tray_menu.addAction(new_timer_action)
        
        tray_menu.addSeparator()
        
        # Show/Hide window
        show_action = QAction("Show Window", self)
        show_action.triggered.connect(self.show_window)
        tray_menu.addAction(show_action)
        
        # Exit
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(exit_action)
        
        self.system_tray.setContextMenu(tray_menu)
        self.system_tray.activated.connect(self.tray_icon_activated)
        
        # Show tray icon
        self.system_tray.show()
        self.system_tray.showMessage(
            "Timenote",
            "Application is running in the system tray",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )
    
    def setup_connections(self):
        """Setup signal connections between components"""
        # Toolbar connections
        self.toolbar.new_note_requested.connect(self.create_new_note)
        self.toolbar.new_timer_requested.connect(self.create_new_timer)
        
        # Sidebar connections
        self.sidebar.note_selected.connect(self.main_panel.load_note)
        self.sidebar.timer_selected.connect(self.main_panel.load_timer)
        self.sidebar.section_changed.connect(self.main_panel.change_section)
        
        # Main panel connections
        self.main_panel.note_updated.connect(self.sidebar.refresh_notes)
        self.main_panel.timer_updated.connect(self.sidebar.refresh_timers)
        self.main_panel.alarm_triggered.connect(self.on_timer_finished)
    
    def apply_styles(self):
        """Apply Notion-like dark theme styling to the interface"""
        font_size = self.config.get("ui", {}).get("font_size", 12)
        
        # Always use dark theme - Notion-like dark mode
        style = f"""
        QMainWindow {{
            background-color: #191919;
            color: #e9e9e7;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: {font_size}px;
        }}
        
        QSplitter::handle {{
            background-color: #2f2f2f;
            width: 1px;
        }}
        
        QFrame {{
            border: none;
            background-color: #191919;
        }}
        
        QPushButton {{
            background-color: #2f2f2f;
            border: 1px solid #3f3f3f;
            border-radius: 6px;
            padding: 8px 12px;
            color: #e9e9e7;
            font-weight: 500;
            transition: all 0.2s ease;
        }}
        
        QPushButton:hover {{
            background-color: #3f3f3f;
            border-color: #4f4f4f;
        }}
        
        QPushButton:pressed {{
            background-color: #1f1f1f;
        }}
        
        QPushButton:disabled {{
            background-color: #1a1a1a;
            color: #666666;
            border-color: #2a2a2a;
        }}
        
        QTextEdit, QLineEdit, QPlainTextEdit {{
            background-color: #2f2f2f;
            border: 1px solid #3f3f3f;
            border-radius: 6px;
            padding: 8px;
            color: #e9e9e7;
            selection-background-color: #4a4a4a;
        }}
        
        QTextEdit:focus, QLineEdit:focus, QPlainTextEdit:focus {{
            border-color: #5a5a5a;
        }}
        
        QLabel {{
            color: #ffffff;
            background-color: transparent;
            font-weight: 500;
        }}
        
        QLabel:hover {{
            color: #ffffff;
        }}
        
        QScrollBar:vertical {{
            background-color: #2a2a2a;
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: #4a4a4a;
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: #5a5a5a;
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollArea {{
            background-color: #191919;
            border: none;
        }}
        
        QListWidget {{
            background-color: #2a2a2a;
            border: 1px solid #3f3f3f;
            border-radius: 6px;
            color: #e9e9e7;
            outline: none;
        }}
        
        QListWidget::item {{
            padding: 8px;
            border-bottom: 1px solid #333333;
        }}
        
        QListWidget::item:selected {{
            background-color: #3f3f3f;
        }}
        
        QListWidget::item:hover {{
            background-color: #353535;
        }}
        """
        
        self.setStyleSheet(style)
    
    def create_new_note(self):
        """Create a new note"""
        # Create new note in storage
        note = self.data_handler.add_note("New Note", "")
        
        # Refresh sidebar and select new note
        self.sidebar.refresh_notes()
        self.sidebar.select_note(note["id"])
        
        # Switch to notes section if not already there
        self.sidebar.set_active_section("notes")
    
    def create_new_timer(self):
        """Create a new timer"""
        # Switch to timers section
        self.sidebar.set_active_section("timers")
        
        # Show timer creation in main panel
        self.main_panel.show_new_timer_dialog()
    
    def on_timer_finished(self, timer_data: dict):
        """Handle timer finished - show notification and sound"""
        # Get alarm settings from config
        alarm_config = self.config.get("alarm", {})
        sound_file = alarm_config.get("sound_file", "")
        volume = alarm_config.get("volume", 0.8)
        
        # Show notification with sound
        show_timer_notification(timer_data, sound_file, volume)
        
        # Also show tray notification for extra attention when window is minimized
        if self.system_tray and not self.isVisible():
            timer_name = timer_data.get("name", "Timer")
            self.system_tray.showMessage(
                "Timer Finished!",
                f"{timer_name} has completed.",
                QSystemTrayIcon.MessageIcon.Information,
                10000  # Show for 10 seconds
            )
    
    def load_window_state(self):
        """Load window position and size from config"""
        window_config = self.config.get("window", {})
        
        # Set window geometry
        self.resize(window_config.get("width", 1200), window_config.get("height", 800))
        self.move(window_config.get("x", 100), window_config.get("y", 100))
    
    def save_window_state(self):
        """Save window position and size to config"""
        geometry = self.geometry()
        self.data_handler.update_config("window", "width", geometry.width())
        self.data_handler.update_config("window", "height", geometry.height())
        self.data_handler.update_config("window", "x", geometry.x())
        self.data_handler.update_config("window", "y", geometry.y())
    
    def auto_save(self):
        """Perform auto-save of current data"""
        if self.main_panel:
            self.main_panel.save_current_data()
    
    def tray_icon_activated(self, reason):
        """Handle system tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show_window()
    
    def show_window(self):
        """Show and raise the main window"""
        self.show()
        self.raise_()
        self.activateWindow()
    
    def quit_application(self):
        """Quit the application completely"""
        self.auto_save()
        self.save_window_state()
        QApplication.instance().quit()
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.system_tray and self.system_tray.isVisible():
            # Minimize to tray instead of closing
            if self.config.get("startup", {}).get("minimize_to_tray", True):
                self.hide()
                event.ignore()
                return
        
        # Save state and exit
        self.auto_save()
        self.save_window_state()
        event.accept()
    
    def changeEvent(self, event):
        """Handle window state changes"""
        if (event.type() == event.Type.WindowStateChange and 
            self.isMinimized() and 
            self.system_tray and 
            self.config.get("startup", {}).get("minimize_to_tray", True)):
            self.hide()
            event.ignore()
        else:
            super().changeEvent(event)
