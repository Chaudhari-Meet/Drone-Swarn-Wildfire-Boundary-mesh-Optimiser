# 🌍 Auto-Start Server with Cloudflare Tunnel
# This gives you an instant public URL to share with anyone!

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Wildfire Server - Public URL Generator" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if cloudflared exists
if (-Not (Test-Path ".\cloudflared.exe")) {
    Write-Host "[1/3] Downloading Cloudflare Tunnel..." -ForegroundColor Yellow
    try {
        Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile "cloudflared.exe"
        Write-Host "      Downloaded successfully!" -ForegroundColor Green
    } catch {
        Write-Host "      Failed to download. Please check internet connection." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit
    }
} else {
    Write-Host "[✓] Cloudflare Tunnel already downloaded" -ForegroundColor Green
}

Write-Host ""
Write-Host "[2/3] Starting Flask server..." -ForegroundColor Yellow

# Check if server already running
$portInUse = netstat -an | Select-String ":5000.*LISTENING"
if ($portInUse) {
    Write-Host "      Server already running on port 5000!" -ForegroundColor Green
} else {
    # Start Flask server in background
    $flaskProcess = Start-Process python -ArgumentList "app.py" -PassThru -WindowStyle Minimized
    Write-Host "      Server started (PID: $($flaskProcess.Id))" -ForegroundColor Green
    Write-Host "      Waiting for server to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
}

Write-Host ""
Write-Host "[3/3] Creating public tunnel..." -ForegroundColor Yellow
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  🌍 YOUR SERVER IS NOW PUBLIC!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Look for the URL below that starts with:" -ForegroundColor Yellow
Write-Host "  https://xxxxx.trycloudflare.com" -ForegroundColor Cyan
Write-Host ""
Write-Host "COPY that URL and send it to your friend!" -ForegroundColor Green
Write-Host ""
Write-Host "Press CTRL+C to stop the tunnel." -ForegroundColor Red
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Start cloudflare tunnel (this will block and show the URL)
.\cloudflared.exe tunnel --url http://localhost:5000

# Cleanup on exit (if we get here)
Write-Host ""
Write-Host "Tunnel stopped." -ForegroundColor Yellow
Write-Host "Server is still running locally on http://localhost:5000" -ForegroundColor Green
