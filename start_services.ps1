# AI-Powered Customer Support Agent - Service Startup Script
# This script ensures all required services are running before starting the Flask app

Write-Host "Starting AI-Powered Customer Support Agent Services..." -ForegroundColor Green

# Function to check if Docker is running
function Test-DockerRunning {
    try {
        docker version *> $null
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

# Function to check if a service is running
function Test-ServiceRunning {
    param($ServiceName, $Port)
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue -InformationLevel Quiet
        return $connection.TcpTestSucceeded
    }
    catch {
        return $false
    }
}

# Function to check if container exists
function Test-ContainerExists {
    param($ContainerName)
    try {
        $result = docker ps -a --filter "name=$ContainerName" --format "{{.Names}}" 2>$null
        return $result -eq $ContainerName
    }
    catch {
        return $false
    }
}

# Function to start or create container
function Start-DockerContainer {
    param($ContainerName, $ImageName, $Ports, $ServiceName)

    Write-Host "Managing $ServiceName container..." -ForegroundColor Yellow

    if (Test-ContainerExists $ContainerName) {
        Write-Host "Starting existing $ContainerName container..." -ForegroundColor Cyan
        docker start $ContainerName
        if ($LASTEXITCODE -eq 0) {
            Write-Host "$ServiceName container started successfully" -ForegroundColor Green
        } else {
            Write-Host "Failed to start existing container, removing and recreating..." -ForegroundColor Yellow
            docker rm -f $ContainerName 2>$null
            Write-Host "Creating new $ContainerName container..." -ForegroundColor Cyan
            Invoke-Expression "docker run -d --name $ContainerName $Ports $ImageName"
            if ($LASTEXITCODE -eq 0) {
                Write-Host "$ServiceName container created and started successfully" -ForegroundColor Green
            } else {
                throw "Failed to create $ServiceName container"
            }
        }
    } else {
        Write-Host "Creating new $ContainerName container..." -ForegroundColor Cyan
        Invoke-Expression "docker run -d --name $ContainerName $Ports $ImageName"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "$ServiceName container created and started successfully" -ForegroundColor Green
        } else {
            throw "Failed to create $ServiceName container"
        }
    }
}

# Check Docker availability
Write-Host "Checking Docker availability..." -ForegroundColor Yellow
if (-not (Test-DockerRunning)) {
    Write-Host "ERROR: Docker is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "Docker is running" -ForegroundColor Green

# Start Redis container
Write-Host ""
Write-Host "Setting up Redis service..." -ForegroundColor Yellow
try {
    Start-DockerContainer -ContainerName "redis-server" -ImageName "redis:latest" -Ports "-p 6379:6379" -ServiceName "Redis"

    # Wait and verify Redis is responding
    Write-Host "Waiting for Redis to be ready..." -ForegroundColor Yellow
    $timeout = 30
    $elapsed = 0
    while (-not (Test-ServiceRunning "Redis" 6379) -and $elapsed -lt $timeout) {
        Start-Sleep -Seconds 2
        $elapsed += 2
        Write-Host "." -NoNewline -ForegroundColor Yellow
    }
    Write-Host ""

    if (Test-ServiceRunning "Redis" 6379) {
        Write-Host "Redis is ready and responding on port 6379" -ForegroundColor Green
    } else {
        throw "Redis failed to become ready within $timeout seconds"
    }
}
catch {
    Write-Host "ERROR with Redis: $_" -ForegroundColor Red
    exit 1
}

# Start Qdrant container
Write-Host ""
Write-Host "Setting up Qdrant service..." -ForegroundColor Yellow
try {
    Start-DockerContainer -ContainerName "qdrant-server" -ImageName "qdrant/qdrant" -Ports "-p 6333:6333 -p 6334:6334" -ServiceName "Qdrant"

    # Wait and verify Qdrant is responding
    Write-Host "Waiting for Qdrant to be ready..." -ForegroundColor Yellow
    $timeout = 45
    $elapsed = 0
    while (-not (Test-ServiceRunning "Qdrant" 6333) -and $elapsed -lt $timeout) {
        Start-Sleep -Seconds 3
        $elapsed += 3
        Write-Host "." -NoNewline -ForegroundColor Yellow
    }
    Write-Host ""

    if (Test-ServiceRunning "Qdrant" 6333) {
        Write-Host "Qdrant is ready and responding on port 6333" -ForegroundColor Green
    } else {
        throw "Qdrant failed to become ready within $timeout seconds"
    }
}
catch {
    Write-Host "ERROR with Qdrant: $_" -ForegroundColor Red
    exit 1
}

# Display service status
Write-Host ""
Write-Host "Service Status Summary:" -ForegroundColor Cyan
docker ps --filter "name=redis-server" --filter "name=qdrant-server" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

Write-Host ""
Write-Host "All services are ready! Starting Flask application..." -ForegroundColor Green
Write-Host "Application will be available at: http://localhost:5000" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the application" -ForegroundColor Yellow

# Start Flask application
try {
    # Check if run.py exists, otherwise use app.py directly
    if (Test-Path "flask_app/run.py") {
        python flask_app/run.py
    } elseif (Test-Path "flask_app/app.py") {
        python flask_app/app.py
    } else {
        throw "Neither flask_app/run.py nor flask_app/app.py found!"
    }
}
catch {
    Write-Host ""
    Write-Host "ERROR starting Flask app: $_" -ForegroundColor Red
    Write-Host "Try running manually: python flask_app/app.py" -ForegroundColor Yellow
    exit 1
}

# Cleanup instructions
Write-Host ""
Write-Host "Application stopped." -ForegroundColor Yellow
Write-Host "To stop all services, run: docker stop redis-server qdrant-server" -ForegroundColor Cyan
