@echo off
REM Weekly Music Scout Ingestion Script
REM This script runs the RSS ingestion process and logs the results

echo ========================================
echo Music Scout Weekly Ingestion
echo Started: %date% %time%
echo ========================================

REM Change to project directory
cd /d "C:\Users\rafae\Projects\personal-music-tracker"

REM Activate virtual environment if you have one (uncomment if needed)
REM call venv\Scripts\activate

REM Run ingestion
echo.
echo Running ingestion...
python -m src.music_scout.cli.ingest ingest

REM Check if ingestion succeeded
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo SUCCESS: Ingestion completed
    echo Ended: %date% %time%
    echo ========================================
) else (
    echo.
    echo ========================================
    echo ERROR: Ingestion failed with code %ERRORLEVEL%
    echo Ended: %date% %time%
    echo ========================================
)

REM Keep window open if run manually (comment out for scheduled task)
REM pause
