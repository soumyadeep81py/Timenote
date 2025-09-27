#!/usr/bin/env python3
"""
Timenote Desktop App
A Windows desktop application for notes and time management
Built with PyQt6 and JSON storage
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

# Add the src directory to Python path
src_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(src_dir)

from ui.main_window import MainWindow

def main():
    """Main application entry point"""
    # Enable high DPI scaling (PyQt6 compatible)
    try:
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        # These attributes may not exist in newer PyQt6 versions
        pass
    
    app = QApplication(sys.argv)
    app.setApplicationName("Timenote")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Timenote")
    
    # Set application icon if available
    icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start the application event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
