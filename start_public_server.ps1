# Wildfire Drone System - Public Server Starter
# This script helps you make the server accessible from anywhere

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Wildfire Drone System - Public Access" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if ngrok exists
if (Test-Path ".\ngrok.exe") {
    Write-Host "[✓] ngrok found!" -ForegroundColor Green
} else {
    Write-Host "[!] ngrok not found. Installing..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please follow these steps:" -ForegroundColor Yellow
    Write-Host "1. Go to: https://ngrok.com/download" -ForegroundColor White
    Write-Host "2. Download ngrok for Windows" -ForegroundColor White
    Write-Host "3. Extract ngrok.exe to this folder: $PWD" -ForegroundColor White
    Write-Host "4. Sign up at https://ngrok.com/ (free)" -ForegroundColor White
    Write-Host "5. Copy your authtoken" -ForegroundColor White
    Write-Host "6. Run: .\ngrok.exe authtoken YOUR_TOKEN" -ForegroundColor White
    Write-Host "7. Run this script again" -ForegroundColor White
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit
}

# Start Flask server in background
Write-Host "[1] Starting Flask server..." -ForegroundColor Yellow
$flaskProcess = Start-Process python -ArgumentList "app.py" -PassThru -WindowStyle Minimized
Write-Host "[✓] Flask server started (PID: $($flaskProcess.Id))" -ForegroundColor Green

# Wait for Flask to start
Write-Host "[2] Waiting for server to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Start ngrok
Write-Host "[3] Starting ngrok tunnel..." -ForegroundColor Yellow
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Server is now PUBLIC!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "ngrok will now open. Look for the HTTPS URL!" -ForegroundColor Yellow
Write-Host "Share that URL with anyone to access your server." -ForegroundColor Yellow
Write-Host ""
Write-Host "Press CTRL+C to stop both servers." -ForegroundColor Red
Write-Host ""

# Start ngrok (this will block)
.\ngrok.exe http 5000

# Cleanup when ngrok stops
Write-Host ""
Write-Host "[!] Stopping Flask server..." -ForegroundColor Yellow
Stop-Process -Id $flaskProcess.Id -Force
Write-Host "[✓] All stopped. Goodbye!" -ForegroundColor Green
