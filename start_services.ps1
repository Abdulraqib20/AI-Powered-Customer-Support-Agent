# AI-Powered Customer Support Agent - Service Startup Script
# This script ensures all required services are running before starting the Flask app

Write-Host "🚀 Starting AI-Powered Customer Support Agent Services..." -ForegroundColor Green

# Function to check if a service is running
function Test-ServiceRunning {
    param($ServiceName, $Port)
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue
        return $connection.TcpTestSucceeded
    }
    catch {
        return $false
    }
}

# Check and start Redis
Write-Host "📦 Checking Redis service..." -ForegroundColor Yellow
if (Test-ServiceRunning "Redis" 6379) {
    Write-Host "✅ Redis is already running on port 6379" -ForegroundColor Green
} else {
    Write-Host "🔄 Starting Redis container..." -ForegroundColor Yellow
    try {
        # Try to start existing container first
        docker start redis-server 2>$null
        if ($LASTEXITCODE -ne 0) {
            # If no existing container, create new one
            docker run -d --name redis-server -p 6379:6379 redis:latest
        }
        Start-Sleep -Seconds 3
        if (Test-ServiceRunning "Redis" 6379) {
            Write-Host "✅ Redis started successfully" -ForegroundColor Green
        } else {
            Write-Host "❌ Failed to start Redis" -ForegroundColor Red
            exit 1
        }
    }
    catch {
        Write-Host "❌ Error starting Redis: $_" -ForegroundColor Red
        exit 1
    }
}

# Check Qdrant
Write-Host "📦 Checking Qdrant service..." -ForegroundColor Yellow
if (Test-ServiceRunning "Qdrant" 6333) {
    Write-Host "✅ Qdrant is already running on port 6333" -ForegroundColor Green
} else {
    Write-Host "🔄 Starting Qdrant container..." -ForegroundColor Yellow
    try {
        # Try to start existing container first
        docker start $(docker ps -aq --filter "ancestor=qdrant/qdrant") 2>$null
        if ($LASTEXITCODE -ne 0) {
            # If no existing container, create new one
            docker run -d -p 6333:6333 -p 6334:6334 qdrant/qdrant
        }
        Start-Sleep -Seconds 5
        if (Test-ServiceRunning "Qdrant" 6333) {
            Write-Host "✅ Qdrant started successfully" -ForegroundColor Green
        } else {
            Write-Host "❌ Failed to start Qdrant" -ForegroundColor Red
            exit 1
        }
    }
    catch {
        Write-Host "❌ Error starting Qdrant: $_" -ForegroundColor Red
        exit 1
    }
}

# Start Flask application
Write-Host "🌐 Starting Flask application..." -ForegroundColor Yellow
Write-Host "📍 Application will be available at: http://localhost:5000" -ForegroundColor Cyan
Write-Host "🔧 Press Ctrl+C to stop the application" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Blue

try {
    python flask_app/run.py
}
catch {
    Write-Host "❌ Error starting Flask app: $_" -ForegroundColor Red
    exit 1
}