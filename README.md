# Timenote Desktop App

A Windows desktop application for notes and time management, featuring a clean interface inspired by modern productivity apps. Built with PyQt6 and designed specifically for Windows with system integration features.

## 🚀 Quick Start

### Prerequisites
- Windows 10 or later
- Python 3.8+ (recommended: Python 3.9+)

### Installation & Running

1. **Clone or download** the project files
2. **Open Command Prompt or PowerShell** in the project directory
3. **Install dependencies:**
   ```cmd
   pip install -r requirements.txt
   ```
4. **Run the application:**
   ```cmd
   python main.py
   ```

### Create Windows Executable

```cmd
pip install PyInstaller
pyinstaller --onefile --windowed --name="Timenote" --add-data "assets;assets" --paths src src\main.py
```

Find your executable in the `dist` folder.

## ✨ Features

### Core Functionality
- 📝 **Note Taking**: Clean note editor with auto-save functionality
- ⏲️ **Multiple Timers**: Countdown timers with visual progress indicators
- 🔔 **Smart Alarms**: Audio alerts with snooze/stop options
- 💾 **JSON Storage**: All data stored in JSON files (no database required)
- 🔄 **Persistence**: Notes and timers restored on app restart

### Windows Integration
- 🏠 **System Tray**: Minimize to tray with quick actions
- 🔔 **Windows Notifications**: Native toast notifications
- 🚀 **Startup Option**: Start automatically with Windows
- 💻 **Windows-Only**: Designed specifically for Windows

### User Interface
- 🎨 **Clean Design**: Modern minimalist interface
- 📱 **Responsive Layout**: Sidebar with Notes, Timers, and Settings
- ⚡ **Smooth Interactions**: Intuitive and fast user experience
- 🎯 **Focus Mode**: Distraction-free writing and timing

## 📁 Project Structure

```
timenote/
├── main.py                 # Application launcher
├── requirements.txt        # Python dependencies
├── LICENSE                 # MIT license
├── src/                    # Source code
│   ├── main.py             # Application entry point
│   ├── ui/                 # User interface components
│   │   ├── main_window.py  # Main application window
│   │   ├── sidebar.py      # Navigation sidebar
│   │   ├── main_panel.py   # Content area
│   │   └── toolbar.py      # Action toolbar
│   ├── features/           # Core functionality
│   │   ├── notes.py        # Note management
│   │   ├── timer.py        # Timer functionality
│   │   ├── alarm.py        # Alarm system
│   │   └── windows_integration.py # Windows-specific features
│   ├── storage/            # Data persistence
│   │   └── json_handler.py # JSON file operations
│   └── utils/              # Utility functions
│       └── notifications.py # Desktop notifications
├── assets/                 # Resources (icons, sounds)
│   ├── alarm.mp3           # Custom alarm sound
│   └── icon.ico            # App icon (optional)
├── scripts/                # Build and utility scripts
│   └── build_exe.bat       # Executable build script
└── docs/                   # Documentation
    ├── BUILD_INSTRUCTIONS.md # Development setup
    ├── PACKAGING_GUIDE.md  # Executable creation guide
    └── GITHUB_UPLOAD.md    # GitHub upload instructions
```

## 🛠️ Development

### Setting up Development Environment

```cmd
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development tools
pip install black flake8 pytest
```

### Key Dependencies

- **PyQt6**: GUI framework
- **plyer**: Cross-platform notifications (optional)
- **pygame**: Audio playback for alarms (optional)
- **win10toast**: Windows 10+ toast notifications (optional)

## 📋 Usage Guide

### Notes
1. Click **"+ New Note"** or use the toolbar
2. Edit title and content directly
3. Notes auto-save every 2 seconds
4. Right-click notes for context menu options

### Timers  
1. Click **"⏲ Start Timer"** or use sidebar
2. Set duration (hours, minutes, seconds)
3. Start/pause/reset as needed
4. Timers persist between app restarts

### Settings
- **Startup**: Configure auto-start with Windows
- **Appearance**: Theme and font size options  
- **Alarms**: Sound file, volume, and snooze settings

### System Tray
- Minimize app to system tray
- Right-click tray icon for quick actions
- Double-click to restore window

## 🔧 Building for Distribution

See [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) for comprehensive packaging instructions including:

- Creating standalone executables
- Windows installer creation
- Portable version setup
- Troubleshooting common issues

### Quick Build Commands

```cmd
# Basic executable (from root directory)
python scripts/build_exe.bat

# Manual build
pyinstaller --onefile --windowed --name="Timenote" --add-data "assets;assets" --paths src src\main.py

# GUI builder tool  
pip install auto-py-to-exe
auto-py-to-exe
```

## 🐛 Troubleshooting

### Common Issues

**App won't start:**
- Ensure Python 3.8+ is installed
- Install PyQt6: `pip install PyQt6`
- Check console output for error messages

**Executable fails:**
- Include all dependencies in PyInstaller build
- Use `--console` flag to see error messages
- Add missing modules to hidden imports

**Notifications not working:**
- Install optional packages: `pip install plyer win10toast`
- Check Windows notification settings

### Debug Mode

Run with console output visible:
```cmd
pyinstaller --onefile --console --name="Timenote-Debug" main.py
```

## 🎯 Features Roadmap

### Implemented ✅
- Note creation, editing, and deletion
- Multiple countdown timers
- Audio alarms with snooze
- Windows notifications
- System tray integration
- Auto-save functionality
- Windows startup registration
- JSON-based persistence

### Planned 📋
- [ ] Rich text formatting
- [ ] File import/export
- [ ] Keyboard shortcuts
- [ ] Theme customization
- [ ] Search functionality
- [ ] Backup/restore
- [ ] Plugin system
- [ ] File associations

## 📄 License

This project is provided as-is for educational and personal use.

##  Acknowledgments
- Built with [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)
- Uses [PyInstaller](https://www.pyinstaller.org/) for packaging

---

**Note**: This application is designed specifically for Windows and includes Windows-specific integrations. For the best experience, use Windows 10 or later.

