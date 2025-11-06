@echo off
REM TORQ-CONSOLE Landing Page - GitHub Pages Deployment Script
REM This script automates deployment to GitHub Pages

echo.
echo ========================================
echo  TORQ-CONSOLE Landing Page Deployment
echo  Target: GitHub Pages
echo ========================================
echo.

REM Get repository URL from user
set /p REPO_URL="Enter your GitHub repository URL (e.g., https://github.com/username/repo.git): "

if "%REPO_URL%"=="" (
    echo Error: Repository URL is required!
    pause
    exit /b 1
)

REM Initialize git if needed
if not exist .git (
    echo Initializing Git repository...
    git init
    echo.
)

REM Add all files
echo Adding files to git...
git add .
echo.

REM Commit
echo Committing files...
git commit -m "Deploy TORQ-CONSOLE Phase 5 landing page"
echo.

REM Set branch to main
echo Setting branch to main...
git branch -M main
echo.

REM Add remote origin
echo Adding remote origin...
git remote remove origin 2>nul
git remote add origin %REPO_URL%
echo.

REM Push to GitHub
echo Pushing to GitHub...
git push -u origin main --force
echo.

echo ========================================
echo  Deployment complete!
echo ========================================
echo.
echo Next steps:
echo 1. Go to your GitHub repository settings
echo 2. Navigate to "Settings" ^> "Pages"
echo 3. Under "Source", select:
echo    - Branch: main
echo    - Folder: / (root)
echo 4. Click "Save"
echo 5. Wait 2-3 minutes for deployment
echo.
echo Your site will be available at:
echo https://USERNAME.github.io/REPOSITORY-NAME/
echo.
pause
