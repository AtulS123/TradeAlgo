# TradeAlgo Daily Data Update Task
# This batch file runs the daily data updater

@echo off
cd /d "C:\Users\atuls\Startup\TradeAlgo"
call venv\Scripts\activate.bat
python scripts\daily_updater.py
pause
