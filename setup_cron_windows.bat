@echo off
REM Windows Task Scheduler Setup for Reminder System

echo 🕐 Setting up Windows Task Scheduler for reminder system...

REM Check if the application is running
echo Checking if the application is running...
curl -s http://localhost:8000/ > nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Application is running on localhost:8000
) else (
    echo ❌ Application is not running on localhost:8000
    echo Please start the application first with: python -m uvicorn api.index:app --host 0.0.0.0 --port 8000
    pause
    exit /b 1
)

REM Test the endpoint
echo Testing the reminder endpoint...
curl -X POST http://localhost:8000/api/run-reminders
echo.

REM Create a batch file to run the reminder
echo Creating batch file...
echo curl -X POST http://localhost:8000/api/run-reminders > run_reminders.bat
echo echo Reminder executed at %%date%% %%time%% >> run_reminders.bat

REM Create task using schtasks command
echo Creating Windows Task Scheduler task...
schtasks /create /tn "SalonReminder" /tr "%CD%\run_reminders.bat" /sc daily /st 09:00 /f

if %errorlevel% equ 0 (
    echo ✅ Windows Task Scheduler task created successfully!
    echo 📅 Task will run daily at 9:00 AM
    echo.
    echo 📋 Useful commands:
    echo   View tasks: schtasks /query /tn "SalonReminder"
    echo   Delete task: schtasks /delete /tn "SalonReminder" /f
    echo   Run task now: schtasks /run /tn "SalonReminder"
    echo.
    echo ⚠️  Note: The task will only run reminders at 9:00 AM Tokyo time
    echo    You can disable the Python scheduler by setting REMINDER_SCHEDULER_ENABLED=false
) else (
    echo ❌ Failed to create Windows Task Scheduler task
    echo Make sure you're running as Administrator
)

pause
