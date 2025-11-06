# PowerShell script to run Prince Flowers + Llama + Azure Research Test

Write-Host "====================================================================`n" -ForegroundColor Green
Write-Host "PRINCE FLOWERS + LLAMA + AZURE RESEARCH TEST`n" -ForegroundColor Yellow
Write-Host "====================================================================`n" -ForegroundColor Green

Set-Location E:\TORQ-CONSOLE

$pythonExe = "C:\Users\asdasd\AppData\Local\Programs\Python\Python313\python.exe"

if (-not (Test-Path $pythonExe)) {
    $pythonExe = "C:\Users\asdasd\AppData\Local\Programs\Python\Python312\python.exe"
}

if (-not (Test-Path $pythonExe)) {
    Write-Host "ERROR: Python not found" -ForegroundColor Red
    exit 1
}

Write-Host "Using Python: $pythonExe`n" -ForegroundColor Cyan

# Run the test
& $pythonExe run_azure_test_simple.py

$exitCode = $LASTEXITCODE
Write-Host "`n====================================================================`n" -ForegroundColor Green

if ($exitCode -eq 0) {
    Write-Host "TEST COMPLETED SUCCESSFULLY" -ForegroundColor Green
} else {
    Write-Host "TEST FAILED WITH EXIT CODE: $exitCode" -ForegroundColor Red
}

Write-Host "====================================================================`n" -ForegroundColor Green

exit $exitCode
