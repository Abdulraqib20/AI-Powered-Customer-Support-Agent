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

# Function to check if ngrok is installed
function Test-NgrokInstalled {
    try {
        ngrok version *> $null
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

# Function to get ngrok public URL
function Get-NgrokPublicUrl {
    try {
        $maxAttempts = 10
        $attempt = 0

        while ($attempt -lt $maxAttempts) {
            try {
                $response = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -TimeoutSec 5
                foreach ($tunnel in $response.tunnels) {
                    if ($tunnel.config.addr -eq "http://localhost:5000" -and $tunnel.public_url.StartsWith("https://")) {
                        return $tunnel.public_url
                    }
                }
                Start-Sleep -Seconds 2
                $attempt++
            }
            catch {
                Start-Sleep -Seconds 2
                $attempt++
            }
        }
        return $null
    }
    catch {
        return $null
    }
}

# Function to start ngrok tunnel (intelligently reuses existing tunnel)
function Start-NgrokTunnel {
    param($Port = 5000)

    # First check if ngrok is already running with a tunnel for this port
    $existingUrl = Get-NgrokPublicUrl
    if ($existingUrl) {
        Write-Host "Found existing ngrok tunnel: $existingUrl" -ForegroundColor Green
        Write-Host "Reusing existing tunnel (no reconfiguration needed)" -ForegroundColor Cyan
        return $existingUrl
    }

    Write-Host "No existing ngrok tunnel found. Starting new tunnel for port $Port..." -ForegroundColor Yellow

    # Start ngrok in background
    Start-Process -FilePath "ngrok" -ArgumentList "http", $Port -WindowStyle Hidden

    # Wait for ngrok to initialize
    Start-Sleep -Seconds 5

    # Get the public URL
    $ngrokUrl = Get-NgrokPublicUrl
    if ($ngrokUrl) {
        Write-Host "New ngrok tunnel created: $ngrokUrl" -ForegroundColor Green
        Write-Host "You'll need to update your WhatsApp webhook URL in Meta Console" -ForegroundColor Yellow
    }
    return $ngrokUrl
}

# Function to display WhatsApp setup information
function Show-WhatsAppSetup {
    param($NgrokUrl, $IsNewTunnel = $false)

    if ($NgrokUrl) {
        $webhookUrl = "$NgrokUrl/webhook/whatsapp"
        Write-Host ""
        Write-Host "ngrok tunnel is active!" -ForegroundColor Green
        Write-Host "Your WhatsApp webhook URL: $webhookUrl" -ForegroundColor Cyan

        if ($IsNewTunnel) {
            Write-Host ""
            Write-Host "WhatsApp Business API Configuration (NEW TUNNEL):" -ForegroundColor Yellow
            Write-Host "   1. Go to: https://developers.facebook.com/apps/1297233261804334/whatsapp-business/wa-settings/?business_id=742368565213885&phone_number_id" -ForegroundColor White
            Write-Host "   2. Select your WhatsApp Business app" -ForegroundColor White
            Write-Host "   3. Go to WhatsApp > Configuration" -ForegroundColor White
            Write-Host "   4. Set webhook URL to: $webhookUrl" -ForegroundColor Cyan
            Write-Host "   5. Set verify token to: raqibtech_whatsapp_webhook_2024" -ForegroundColor Cyan
            Write-Host "   6. Subscribe to 'messages' webhook field" -ForegroundColor White
            Write-Host "   7. Add your phone number to the app for testing" -ForegroundColor White
        }
        else {
            Write-Host "Using existing tunnel - no reconfiguration needed!" -ForegroundColor Green
        }
        Write-Host ""
    }
    else {
        Write-Host "ngrok tunnel failed to start. WhatsApp webhook will not be accessible." -ForegroundColor Yellow
        Write-Host "   You can start ngrok manually: ngrok http 5000" -ForegroundColor White
    }
}

# Function to check if Redis is responding
function Test-RedisRunning {
    try {
        $result = docker exec redis-server redis-cli ping 2>$null
        return $result -eq "PONG"
    }
    catch {
        return $false
    }
}

# Function to check if Qdrant is responding
function Test-QdrantRunning {
    try {
        $null = Invoke-RestMethod -Uri "http://localhost:6333/collections" -Method GET -TimeoutSec 5 -ErrorAction SilentlyContinue
        return $true
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
        }
        else {
            Write-Host "Failed to start existing container, removing and recreating..." -ForegroundColor Yellow
            docker rm -f $ContainerName 2>$null
            Write-Host "Creating new $ContainerName container..." -ForegroundColor Cyan
            Invoke-Expression "docker run -d --name $ContainerName $Ports $ImageName"
            if ($LASTEXITCODE -eq 0) {
                Write-Host "$ServiceName container created and started successfully" -ForegroundColor Green
            }
            else {
                throw "Failed to create $ServiceName container"
            }
        }
    }
    else {
        Write-Host "Creating new $ContainerName container..." -ForegroundColor Cyan
        Invoke-Expression "docker run -d --name $ContainerName $Ports $ImageName"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "$ServiceName container created and started successfully" -ForegroundColor Green
        }
        else {
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

# Check ngrok availability
Write-Host ""
Write-Host "Checking ngrok availability..." -ForegroundColor Yellow
if (-not (Test-NgrokInstalled)) {
    Write-Host "WARNING: ngrok is not installed or not in PATH!" -ForegroundColor Red
    Write-Host "WhatsApp webhook will not be accessible from the internet." -ForegroundColor Yellow
    Write-Host "To install ngrok: winget install ngrok.ngrok" -ForegroundColor Cyan
    Write-Host "Continuing without ngrok..." -ForegroundColor Yellow
    $ngrokAvailable = $false
}
else {
    Write-Host "ngrok is available" -ForegroundColor Green
    $ngrokAvailable = $true
}

# Clean up old containers if they exist
Write-Host ""
Write-Host "Cleaning up old containers..." -ForegroundColor Yellow
docker rm -f redis-server qdrant-server 2>$null | Out-Null

# Start Redis container
Write-Host ""
Write-Host "Setting up Redis service..." -ForegroundColor Yellow
try {
    Start-DockerContainer -ContainerName "redis-server" -ImageName "redis:latest" -Ports "-p 6379:6379" -ServiceName "Redis"

    # Wait for container to be fully ready
    Write-Host "Waiting for Redis to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3

    # Wait and verify Redis is responding
    Write-Host "Checking Redis connectivity..." -ForegroundColor Yellow
    $timeout = 30
    $elapsed = 0
    $redisReady = $false

    while (-not $redisReady -and $elapsed -lt $timeout) {
        $redisReady = Test-RedisRunning
        if (-not $redisReady) {
            Start-Sleep -Seconds 2
            $elapsed += 2
            Write-Host "." -NoNewline -ForegroundColor Yellow
        }
    }
    Write-Host ""

    if ($redisReady) {
        Write-Host "Redis is ready and responding (PONG received)" -ForegroundColor Green
    }
    else {
        Write-Host "Trying alternative connectivity test..." -ForegroundColor Yellow
        # Fallback test using netstat
        $netstatResult = netstat -an | Select-String "6379.*LISTENING"
        if ($netstatResult) {
            Write-Host "Redis is listening on port 6379 (fallback test passed)" -ForegroundColor Green
        }
        else {
            throw "Redis failed to become ready within $timeout seconds"
        }
    }
}
catch {
    Write-Host "ERROR with Redis: $_" -ForegroundColor Red
    Write-Host "Checking Redis container logs..." -ForegroundColor Yellow
    docker logs redis-server --tail 10
    exit 1
}

# Start Qdrant container
Write-Host ""
Write-Host "Setting up Qdrant service..." -ForegroundColor Yellow
try {
    Start-DockerContainer -ContainerName "qdrant-server" -ImageName "qdrant/qdrant" -Ports "-p 6333:6333 -p 6334:6334" -ServiceName "Qdrant"

    # Wait for container to be fully ready
    Write-Host "Waiting for Qdrant to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5

    # Wait and verify Qdrant is responding
    Write-Host "Checking Qdrant connectivity..." -ForegroundColor Yellow
    $timeout = 45
    $elapsed = 0
    $qdrantReady = $false

    while (-not $qdrantReady -and $elapsed -lt $timeout) {
        $qdrantReady = Test-QdrantRunning
        if (-not $qdrantReady) {
            Start-Sleep -Seconds 3
            $elapsed += 3
            Write-Host "." -NoNewline -ForegroundColor Yellow
        }
    }
    Write-Host ""

    if ($qdrantReady) {
        Write-Host "Qdrant is ready and responding on port 6333" -ForegroundColor Green
    }
    else {
        Write-Host "Trying alternative connectivity test..." -ForegroundColor Yellow
        # Fallback test using netstat
        $netstatResult = netstat -an | Select-String "6333.*LISTENING"
        if ($netstatResult) {
            Write-Host "Qdrant is listening on port 6333 (fallback test passed)" -ForegroundColor Green
        }
        else {
            throw "Qdrant failed to become ready within $timeout seconds"
        }
    }
}
catch {
    Write-Host "ERROR with Qdrant: $_" -ForegroundColor Red
    Write-Host "Checking Qdrant container logs..." -ForegroundColor Yellow
    docker logs qdrant-server --tail 10
    exit 1
}

# Display service status
Write-Host ""
Write-Host "Service Status Summary:" -ForegroundColor Cyan
docker ps --filter "name=redis-server" --filter "name=qdrant-server" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Start ngrok tunnel if available
$ngrokUrl = $null
$isNewTunnel = $false
if ($ngrokAvailable) {
    Write-Host ""
    Write-Host "Setting up ngrok tunnel for WhatsApp webhook..." -ForegroundColor Yellow
    try {
        # Check if tunnel already exists before starting
        $existingUrl = Get-NgrokPublicUrl
        $ngrokUrl = Start-NgrokTunnel -Port 5000
        $isNewTunnel = ($null -eq $existingUrl -and $null -ne $ngrokUrl)

        if ($ngrokUrl) {
            Write-Host "ngrok tunnel ready: $ngrokUrl" -ForegroundColor Green
        }
        else {
            Write-Host "Failed to establish ngrok tunnel" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "ERROR starting ngrok: $_" -ForegroundColor Red
        Write-Host "Continuing without ngrok..." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "All services are ready! Starting Flask application..." -ForegroundColor Green
Write-Host "Application will be available at: http://localhost:5000" -ForegroundColor Cyan
if ($ngrokUrl) {
    Write-Host "Public URL (via ngrok): $ngrokUrl" -ForegroundColor Cyan
}
Write-Host "Press Ctrl+C to stop the application" -ForegroundColor Yellow

# Display WhatsApp setup information if ngrok is available
if ($ngrokUrl) {
    Show-WhatsAppSetup -NgrokUrl $ngrokUrl -IsNewTunnel $isNewTunnel
}

# Start Flask application
try {
    # Check if run.py exists, otherwise use app.py directly
    if (Test-Path "flask_app/run.py") {
        python flask_app/run.py
    }
    elseif (Test-Path "flask_app/app.py") {
        python flask_app/app.py
    }
    else {
        throw "Neither flask_app/run.py nor flask_app/app.py found!"
    }
}
catch {
    Write-Host ""
    Write-Host "ERROR starting Flask app: $_" -ForegroundColor Red
    Write-Host "Try running manually: python flask_app/app.py" -ForegroundColor Yellow
    exit 1
}
finally {
    # Note: We intentionally DON'T stop ngrok here to preserve the tunnel URL
    # This allows reusing the same webhook URL on next startup
    Write-Host ""
    Write-Host "ngrok tunnel left running to preserve webhook URL" -ForegroundColor Cyan
    Write-Host "   To stop ngrok manually: Get-Process ngrok | Stop-Process" -ForegroundColor Gray
}

# Cleanup instructions
Write-Host ""
Write-Host "Application stopped." -ForegroundColor Yellow
Write-Host "To stop Docker services: docker stop redis-server qdrant-server" -ForegroundColor Cyan
Write-Host "ngrok tunnel remains active (preserves webhook URL)" -ForegroundColor Cyan
Write-Host "   To stop ngrok: Get-Process ngrok | Stop-Process" -ForegroundColor Gray
