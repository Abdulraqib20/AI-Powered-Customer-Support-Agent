# AI-Powered Customer Support Agent - Service Stop Script
# This script stops all Docker containers used by the Flask app

Write-Host "Stopping AI-Powered Customer Support Agent Services..." -ForegroundColor Yellow

# Function to stop container if it exists
function Stop-DockerContainer {
    param($ContainerName, $ServiceName)

    try {
        $result = docker ps --filter "name=$ContainerName" --format "{{.Names}}" 2>$null
        if ($result -eq $ContainerName) {
            Write-Host "Stopping $ServiceName container..." -ForegroundColor Yellow
            docker stop $ContainerName
            if ($LASTEXITCODE -eq 0) {
                Write-Host "$ServiceName stopped successfully" -ForegroundColor Green
            } else {
                Write-Host "Failed to stop $ServiceName gracefully" -ForegroundColor Yellow
            }
        } else {
            Write-Host "$ServiceName container not running" -ForegroundColor Cyan
        }
    }
    catch {
        Write-Host "Error stopping ${ServiceName}: $_" -ForegroundColor Red
    }
}

# Stop services
Stop-DockerContainer -ContainerName "redis-server" -ServiceName "Redis"
Stop-DockerContainer -ContainerName "qdrant-server" -ServiceName "Qdrant"

Write-Host ""
Write-Host "Final Status:" -ForegroundColor Cyan
docker ps --filter "name=redis-server" --filter "name=qdrant-server" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

Write-Host ""
Write-Host "All services stopped." -ForegroundColor Green
Write-Host "To remove containers completely, run: docker rm redis-server qdrant-server" -ForegroundColor Cyan
Write-Host "To start services again, run: .\start_services.ps1" -ForegroundColor Cyan
