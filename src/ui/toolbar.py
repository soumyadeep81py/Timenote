"""
Notion-like Toolbar
Provides quick access buttons for common actions
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QSpacerItem, 
    QSizePolicy, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QFont


class NotionToolbar(QWidget):
    """Minimalist toolbar with New Note, Start Timer, and Settings buttons"""
    
    # Signals
    new_note_requested = pyqtSignal()
    new_timer_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.apply_styles()
    
    def setup_ui(self):
        """Setup the toolbar UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)
        
        # App title/logo area
        title_label = QLabel("Timenote")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setWeight(QFont.Weight.Bold)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Spacer to push buttons to the right
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout.addItem(spacer)
        
        # Action buttons
        self.new_note_btn = QPushButton("+ New Note")
        self.new_note_btn.clicked.connect(self.new_note_clicked)
        layout.addWidget(self.new_note_btn)
        
        self.new_timer_btn = QPushButton("⏲ Start Timer")
        self.new_timer_btn.clicked.connect(self.new_timer_clicked)
        layout.addWidget(self.new_timer_btn)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setMaximumHeight(20)
        layout.addWidget(separator)
        
        self.settings_btn = QPushButton("⚙ Settings")
        self.settings_btn.clicked.connect(self.settings_clicked)
        layout.addWidget(self.settings_btn)
    
    def apply_styles(self):
        """Apply Notion-like styling to the toolbar"""
        style = """
        NotionToolbar {
            background-color: #ffffff;
            border-bottom: 1px solid #e9e9e7;
            min-height: 48px;
            max-height: 48px;
        }
        
        QLabel {
            color: #37352f;
            font-weight: bold;
        }
        
        QPushButton {
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 6px;
            padding: 6px 12px;
            color: #37352f;
            font-weight: 500;
            min-width: 80px;
        }
        
        QPushButton:hover {
            background-color: #f7f7f5;
            border-color: #e9e9e7;
        }
        
        QPushButton:pressed {
            background-color: #ededeb;
        }
        
        QFrame {
            color: #e9e9e7;
        }
        """
        self.setStyleSheet(style)
    
    def new_note_clicked(self):
        """Handle new note button click"""
        self.new_note_requested.emit()
    
    def new_timer_clicked(self):
        """Handle new timer button click"""
        self.new_timer_requested.emit()
    
    def settings_clicked(self):
        """Handle settings button click"""
        self.settings_requested.emit()
