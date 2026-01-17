# 🚀 Quick Start Script

Write-Host "`n🎯 Cost-Quality Optimization System - Quick Start" -ForegroundColor Cyan
Write-Host "================================================`n" -ForegroundColor Cyan

# Check Python
Write-Host "🐍 Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "   ❌ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Check if venv exists
if (-Not (Test-Path "venv")) {
    Write-Host "`n📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "   ✅ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "`n✅ Virtual environment already exists" -ForegroundColor Green
}

# Activate venv
Write-Host "`n🔌 Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
Write-Host "   ✅ Virtual environment activated" -ForegroundColor Green

# Install dependencies
Write-Host "`n📥 Installing dependencies..." -ForegroundColor Yellow
pip install -q -r requirements.txt
Write-Host "   ✅ Dependencies installed" -ForegroundColor Green

# Check .env
if (-Not (Test-Path ".env")) {
    Write-Host "`n⚠️  .env file not found!" -ForegroundColor Red
    Write-Host "   Creating from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "`n   📝 Please edit .env and add your PORTKEY_API_KEY" -ForegroundColor Yellow
    Write-Host "   Get your key from: https://app.portkey.ai" -ForegroundColor Cyan
    
    $openEditor = Read-Host "`n   Open .env in notepad? (y/n)"
    if ($openEditor -eq "y") {
        notepad .env
    }
} else {
    Write-Host "`n✅ .env file exists" -ForegroundColor Green
}

# Test configuration
Write-Host "`n🧪 Testing Portkey configuration..." -ForegroundColor Yellow
$testResult = python tests/test_config.py 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Configuration valid!" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Configuration test failed" -ForegroundColor Red
    Write-Host "   Please check your PORTKEY_API_KEY in .env" -ForegroundColor Yellow
}

Write-Host "`n" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "🎉 Setup Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. 🧪 Run tests: python tests/simple_test.py" -ForegroundColor White
Write-Host "  2. 🚀 Run demo: python main.py" -ForegroundColor White
Write-Host "  3. ♾️  Run continuous: python continuous_mode.py" -ForegroundColor White
Write-Host "`nHappy optimizing! 🎯`n" -ForegroundColor Cyan
