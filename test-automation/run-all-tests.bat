@echo off
REM Test Execution Script for Windows
REM Run this script to execute all verification tests

echo ==================================
echo Hotel Booking Platform - Phase 7: Verification
echo ==================================
echo.

echo Step 1: Installing Backend Test Dependencies
cd dev
pip install -r tests\requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install backend dependencies
    exit /b 1
)
echo Backend dependencies installed
echo.

echo Step 2: Running Backend API Tests
pytest tests\ -v --tb=short --color=yes
set BACKEND_EXIT_CODE=%ERRORLEVEL%
echo.

echo Step 3: Installing Frontend Test Dependencies
cd ..\test-automation
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install frontend dependencies
    exit /b 1
)
echo Frontend dependencies installed
echo.

echo Step 4: Installing Playwright Browsers
call npx playwright install --with-deps
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install Playwright browsers
    exit /b 1
)
echo Playwright browsers installed
echo.

echo Step 5: Starting Backend Services (in background)
echo Note: This assumes services are already running or using in-memory database
echo.

echo Step 6: Running Frontend E2E Tests
call npm test
set FRONTEND_EXIT_CODE=%ERRORLEVEL%
echo.

echo ==================================
echo Test Execution Summary
echo ==================================
if %BACKEND_EXIT_CODE% EQU 0 (
    echo Backend Tests: PASSED
) else (
    echo Backend Tests: FAILED
)

if %FRONTEND_EXIT_CODE% EQU 0 (
    echo Frontend Tests: PASSED
) else (
    echo Frontend Tests: FAILED
)
echo.

echo View detailed reports:
echo   - Backend: Check console output above
echo   - Frontend: npx playwright show-report
echo.

REM Exit with error if any tests failed
if %BACKEND_EXIT_CODE% NEQ 0 exit /b 1
if %FRONTEND_EXIT_CODE% NEQ 0 exit /b 1

exit /b 0
