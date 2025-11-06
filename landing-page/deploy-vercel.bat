@echo off
REM TORQ-CONSOLE Landing Page - Vercel Deployment Script
REM This script automates deployment to Vercel

echo.
echo ========================================
echo  TORQ-CONSOLE Landing Page Deployment
echo  Target: Vercel
echo ========================================
echo.

REM Check if git is initialized
if not exist .git (
    echo Initializing Git repository...
    git init
    git add .
    git commit -m "Initial commit: TORQ-CONSOLE Phase 5 landing page"
    echo.
)

REM Check if Vercel CLI is installed
where vercel >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Vercel CLI not found!
    echo Installing Vercel CLI...
    npm install -g vercel
    echo.
)

REM Login to Vercel
echo Please login to Vercel...
vercel login
echo.

REM Deploy to Vercel
echo Deploying to Vercel...
vercel

echo.
echo ========================================
echo  Preview deployment complete!
echo ========================================
echo.
echo To deploy to production, run:
echo   vercel --prod
echo.
pause
