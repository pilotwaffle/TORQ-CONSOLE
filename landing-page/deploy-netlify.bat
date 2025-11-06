@echo off
REM TORQ-CONSOLE Landing Page - Netlify Deployment Script
REM This script automates deployment to Netlify

echo.
echo ========================================
echo  TORQ-CONSOLE Landing Page Deployment
echo  Target: Netlify
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

REM Check if Netlify CLI is installed
where netlify >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Netlify CLI not found!
    echo Installing Netlify CLI...
    npm install -g netlify-cli
    echo.
)

REM Login to Netlify
echo Please login to Netlify...
netlify login
echo.

REM Initialize Netlify project
echo Initializing Netlify project...
netlify init
echo.

REM Deploy to production
echo Deploying to production...
netlify deploy --prod --dir=.
echo.

echo ========================================
echo  Deployment complete!
echo ========================================
echo.
echo Your site is now live on Netlify!
echo Check the URL provided above.
echo.
pause
