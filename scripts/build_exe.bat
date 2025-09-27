@echo off
echo Building Timenote executable...
echo.

REM Change to project root directory
cd /d "%~dp0.."

REM Clean previous builds
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del "*.spec"

REM Build executable
pyinstaller --onefile --windowed --name "Timenote" --add-data "assets;assets" --hidden-import plyer.platforms.win.notification --paths src src\main.py

echo.
if exist "dist\Timenote.exe" (
    echo Build successful! Executable created at: dist\Timenote.exe
    dir dist\Timenote.exe
) else (
    echo Build failed!
)

pause