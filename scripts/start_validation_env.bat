@echo off
REM ============================================================================
REM Phase 5.1 Validation — Local PostgreSQL Startup
REM ============================================================================
REM
REM This script starts a local PostgreSQL container for validation.
REM
REM Usage: scripts\start_validation_env.bat
REM ============================================================================

echo ==========================================
echo TORQ Console — Validation Environment
echo ==========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running.
    echo Please start Docker Desktop and run this script again.
    pause
    exit /b 1
)

echo [1/5] Checking for existing validation container...
docker ps -a --filter "name=torq_validation_db" --format "{{.Names}}" | findstr "torq_validation_db" >nul
if %errorlevel% equ 0 (
    echo Found existing container. Removing...
    docker rm -f torq_validation_db torq_pgadmin 2>nul
)

echo [2/5] Starting PostgreSQL container...
docker-compose -f docker\docker-compose.validation.yml up -d

if %errorlevel% neq 0 (
    echo [ERROR] Failed to start containers.
    pause
    exit /b 1
)

echo [3/5] Waiting for PostgreSQL to be ready...
:waitloop
timeout /t 2 /nobreak >nul
docker exec torq_validation_db pg_isready -U postgres >nul 2>&1
if %errorlevel% neq 0 goto waitloop
echo PostgreSQL is ready!

echo [4/5] Creating validation database if not exists...
docker exec -i torq_validation_db psql -U postgres -c "SELECT 'Database already exists' FROM pg_database WHERE datname='torq_validation';" | findstr "1 row" >nul
if %errorlevel% neq 0 (
    docker exec -i torq_validation_db psql -U postgres -c "CREATE DATABASE torq_validation;"
    echo Database created.
) else (
    echo Database already exists.
)

echo [5/5] Setting up validation schema...
echo Applying migrations...

REM Apply migrations in order
for %%f in (migrations\*.sql) do (
    echo   Applying %%~nxf...
    docker exec -i torq_validation_db psql -U postgres -d torq_validation < "%%f" >nul 2>&1
    if %errorlevel% neq 0 (
        echo   [WARNING] Migration %%~nxf had issues
    )
)

echo.
echo ==========================================
echo Validation Environment Ready!
echo ==========================================
echo.
echo Database Connection:
echo   Host: localhost
echo   Port: 5433
echo   Database: torq_validation
echo   User: postgres
echo   Password: postgres
echo.
echo pgAdmin available at: http://localhost:5050
echo   Email: admin@torq.local
echo   Password: admin
echo.
echo Next steps:
echo   1. Update .env.validation with DATABASE_URL
echo   2. Load environment: load-env .env.validation
echo   3. Run: python scripts\run_validation.py baseline
echo   4. Run: python scripts\run_validation.py reset
echo   5. Start backend: python -m torq_console.cli server
echo.
pause
