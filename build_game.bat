@echo off
REM Shape-Game - Build Executable
REM This script creates a standalone .exe file using PyInstaller
REM Build Version: 2.0.0 - With hexagon enemies and updated progression

setlocal enabledelayedexpansion

REM Use the Python executable we found earlier
set PYTHON_EXE=C:/Users/alexj/AppData/Local/Python/pythoncore-3.14-64/python.exe

echo Installing PyInstaller...
"%PYTHON_EXE%" -m pip install --upgrade pyinstaller

echo.
echo Cleaning old builds...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist shape-game.spec del shape-game.spec

echo.
echo Building executable...
REM PyInstaller with all necessary modules from refactored structure
"%PYTHON_EXE%" -m PyInstaller --onefile --windowed --name "shape-game" ^
    --icon=NONE ^
    --add-data "sounds;sounds" ^
    --hidden-import=entities ^
    --hidden-import=collision ^
    --hidden-import=menus ^
    --hidden-import=audio ^
    --hidden-import=constants ^
    --hidden-import=utils ^
    --distpath=dist ^
    --workpath=build ^
    --specpath=. ^
    top_down_game.py

echo.
if exist dist\shape-game.exe (
    echo.
    echo ========================================
    echo Build complete! (v2.0.0)
    echo Your game is in: dist\shape-game.exe
    echo ========================================
) else (
    echo.
    echo Build failed. Check the output above for errors.
)
echo.
pause