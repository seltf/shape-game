@echo off
REM Top Down Game - Build Executable
REM This script creates a standalone .exe file

setlocal enabledelayedexpansion

REM Use the Python executable we found earlier
set PYTHON_EXE=C:/Users/alexj/AppData/Local/Python/pythoncore-3.14-64/python.exe

echo Installing PyInstaller...
"%PYTHON_EXE%" -m pip install --upgrade pyinstaller

echo.
echo Cleaning old builds...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist TopDownGame.spec del TopDownGame.spec

echo.
echo Building executable...
"%PYTHON_EXE%" -m PyInstaller --onefile --windowed --name "yoyo-game" ^
    --icon=NONE ^
    --distpath=dist ^
    --workpath=build ^
    --specpath=. ^
    top_down_game.py

echo.
if exist dist\TopDownGame.exe (
    echo.
    echo ========================================
    echo Build complete!
    echo Your game is in: dist\TopDownGame.exe
    echo ========================================
) else (
    echo.
    echo Build failed. Check the output above for errors.
)
echo.
pause
