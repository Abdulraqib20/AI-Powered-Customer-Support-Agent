#!/bin/bash

# AI-Powered Customer Support Agent - Service Startup Script (macOS/Linux)
# This script ensures all required services are running before starting the Flask app

echo "Starting AI-Powered Customer Support Agent Services..."

# Function to check if Docker is running
check_docker_running() {
    if docker version >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to check if ngrok is installed
check_ngrok_installed() {
    if command -v ngrok >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to check if ngrok is authenticated (has authtoken)
check_ngrok_authenticated() {
    # Prefer checking config file presence and authtoken entry
    local mac_cfg="$HOME/Library/Application Support/ngrok/ngrok.yml"
    local xdg_cfg="$HOME/.config/ngrok/ngrok.yml"

    if [ -f "$mac_cfg" ] && grep -Eq "authtoken:\s*\S+" "$mac_cfg" 2>/dev/null; then
        return 0
    fi
    if [ -f "$xdg_cfg" ] && grep -Eq "authtoken:\s*\S+" "$xdg_cfg" 2>/dev/null; then
        return 0
    fi

    # As a fallback, if ngrok config check returns success and printing authtoken yields a non-empty single token
    if ngrok config check >/dev/null 2>&1; then
        local printed
        printed=$(ngrok config get authtoken 2>/dev/null | head -n1)
        if echo "$printed" | grep -Eq '^[A-Za-z0-9_-]{20,}$'; then
            return 0
        fi
    fi

    return 1
}

# Function to find available port
find_available_port() {
    local start_port=${1:-5000}
    local port=$start_port

    while [ $port -lt $((start_port + 10)) ]; do
        if ! lsof -i :$port >/dev/null 2>&1; then
            echo $port
            return 0
        fi
        port=$((port + 1))
    done
    return 1
}

# Function to get ngrok public URL
get_ngrok_public_url() {
    local port=${1:-5000}
    local max_attempts=12
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://127.0.0.1:4040/api/tunnels >/dev/null 2>&1; then
            local response=$(curl -s http://127.0.0.1:4040/api/tunnels)
            # Use jq if available, otherwise use grep/sed
            if command -v jq >/dev/null 2>&1; then
                local public_url=$(echo "$response" | jq -r ".tunnels[] | select(.config.addr == \"http://localhost:$port\" and (.public_url | startswith(\"https://\"))) | .public_url" 2>/dev/null | head -1)
            else
                # Fallback to grep/sed method with better regex
                local public_url=$(echo "$response" | grep -o '"public_url":"https://[^"]*"' | head -1 | sed 's/"public_url":"//g' | sed 's/"//g')
            fi

            if [ -n "$public_url" ] && [[ "$public_url" == https://* ]]; then
                echo "$public_url"
                return 0
            fi
        elif curl -s http://localhost:4040/api/tunnels >/dev/null 2>&1; then
            local response=$(curl -s http://localhost:4040/api/tunnels)
            if command -v jq >/dev/null 2>&1; then
                local public_url=$(echo "$response" | jq -r ".tunnels[] | select(.config.addr == \"http://localhost:$port\" and (.public_url | startswith(\"https://\"))) | .public_url" 2>/dev/null | head -1)
            else
                local public_url=$(echo "$response" | grep -o '"public_url":"https://[^"]*"' | head -1 | sed 's/"public_url":"//g' | sed 's/"//g')
            fi
            if [ -n "$public_url" ] && [[ "$public_url" == https://* ]]; then
                echo "$public_url"
                return 0
            fi
        fi
        sleep 2
        attempt=$((attempt + 1))
    done
    return 1
}

# Function to start ngrok tunnel (intelligently reuses existing tunnel)
start_ngrok_tunnel() {
    local port=${1:-5000}

    # First check if ngrok is already running with a tunnel for this port
    local existing_url=$(get_ngrok_public_url $port)
    if [ -n "$existing_url" ]; then
        echo "Found existing ngrok tunnel: $existing_url" >&2
        echo "Reusing existing tunnel (no reconfiguration needed)" >&2
        echo "$existing_url"
        return 0
    fi

    echo "No existing ngrok tunnel found. Starting new tunnel for port $port..." >&2

    # Start ngrok in background with explicit local target; capture logs to file
    local ngrok_log=".ngrok-${port}.log"
    rm -f "$ngrok_log" 2>/dev/null || true
    nohup ngrok http http://localhost:$port --log=stdout --log-format=json > "$ngrok_log" 2>&1 &

    # Wait for ngrok to initialize
    sleep 6

    # Get the public URL
    local ngrok_url=$(get_ngrok_public_url $port)
    if [ -z "$ngrok_url" ] && [ -f "$ngrok_log" ]; then
        # Fallback: parse from log file
        if command -v jq >/dev/null 2>&1; then
            ngrok_url=$(grep -a '"url"' "$ngrok_log" | jq -r 'select(.url? and (.url | startswith("https://"))) | .url' | head -1)
        else
            ngrok_url=$(grep -Eo 'https://[a-zA-Z0-9.-]+\.ngrok[^ ]*' "$ngrok_log" | head -1)
        fi
    fi

    if [ -n "$ngrok_url" ]; then
        echo "New ngrok tunnel created: $ngrok_url" >&2
        echo "You'll need to update your WhatsApp webhook URL in Meta Console" >&2
        rm -f "$ngrok_log" 2>/dev/null || true
        echo "$ngrok_url"
    else
        echo "Failed to get ngrok URL" >&2
        [ -f "$ngrok_log" ] && tail -n 20 "$ngrok_log" >&2 || true
        return 1
    fi
}

# Function to display WhatsApp setup information
show_whatsapp_setup() {
    local ngrok_url="$1"
    local is_new_tunnel="$2"

    if [ -n "$ngrok_url" ]; then
        local webhook_url="$ngrok_url/webhook/whatsapp"
        echo ""
        echo "ngrok tunnel is active!"
        echo "Your WhatsApp webhook URL: $webhook_url"

        if [ "$is_new_tunnel" = "true" ]; then
            echo ""
            echo "WhatsApp Business API Configuration (NEW TUNNEL):"
            echo "   1. Go to: https://developers.facebook.com/apps/1297233261804334/whatsapp-business/wa-settings/?business_id=742368565213885&phone_number_id"
            echo "   2. Select your WhatsApp Business app"
            echo "   3. Go to WhatsApp > Configuration"
            echo "   4. Set webhook URL to: $webhook_url"
            echo "   5. Set verify token to: raqibtech_whatsapp_webhook_2024"
            echo "   6. Subscribe to 'messages' webhook field"
            echo "   7. Add your phone number to the app for testing"
        else
            echo "Using existing tunnel - no reconfiguration needed!"
        fi
        echo ""
    else
        echo "ngrok tunnel failed to start. WhatsApp webhook will not be accessible."
        echo "   You can start ngrok manually: ngrok http 5000"
    fi
}

# Function to check if Redis is responding
check_redis_running() {
    if docker exec redis-server redis-cli ping 2>/dev/null | grep -q "PONG"; then
        return 0
    else
        return 1
    fi
}

# Function to check if Qdrant is responding
check_qdrant_running() {
    if curl -s http://localhost:6333/collections >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to check if container exists
check_container_exists() {
    local container_name="$1"
    if docker ps -a --filter "name=$container_name" --format "{{.Names}}" 2>/dev/null | grep -q "^$container_name$"; then
        return 0
    else
        return 1
    fi
}

# Function to start or create container
start_docker_container() {
    local container_name="$1"
    local image_name="$2"
    local ports="$3"
    local service_name="$4"

    echo "Managing $service_name container..."

    if check_container_exists "$container_name"; then
        echo "Starting existing $container_name container..."
        if docker start "$container_name" >/dev/null 2>&1; then
            echo "$service_name container started successfully"
        else
            echo "Failed to start existing container, removing and recreating..."
            docker rm -f "$container_name" >/dev/null 2>&1
            echo "Creating new $container_name container..."
            if docker run -d --name "$container_name" $ports "$image_name" >/dev/null 2>&1; then
                echo "$service_name container created and started successfully"
            else
                echo "ERROR: Failed to create $service_name container"
                return 1
            fi
        fi
    else
        echo "Creating new $container_name container..."
        if docker run -d --name "$container_name" $ports "$image_name" >/dev/null 2>&1; then
            echo "$service_name container created and started successfully"
        else
            echo "ERROR: Failed to create $service_name container"
            return 1
        fi
    fi
}

# Check Docker availability
echo "Checking Docker availability..."
if ! check_docker_running; then
    echo "ERROR: Docker is not running!"
    echo "Please start Docker Desktop and try again."
    read -p "Press Enter to exit"
    exit 1
fi
echo "Docker is running"

# Check ngrok availability
echo ""
echo "Checking ngrok availability..."
if ! check_ngrok_installed; then
    echo "WARNING: ngrok is not installed or not in PATH!"
    echo "WhatsApp webhook will not be accessible from the internet."
    echo "To install ngrok: brew install ngrok/ngrok/ngrok"
    echo "Continuing without ngrok..."
    ngrok_available=false
else
    if check_ngrok_authenticated; then
        echo "ngrok is available and authenticated"
        ngrok_available=true
    else
        echo "ngrok is installed but NOT authenticated (missing authtoken). Skipping ngrok."
        echo "To enable ngrok: ngrok config add-authtoken <YOUR_TOKEN>"
        ngrok_available=false
    fi
fi

# Clean up old containers if they exist
echo ""
echo "Cleaning up old containers..."
docker rm -f redis-server qdrant-server >/dev/null 2>&1

# Start Redis container
echo ""
echo "Setting up Redis service..."
if start_docker_container "redis-server" "redis:latest" "-p 6379:6379" "Redis"; then
    # Wait for container to be fully ready
    echo "Waiting for Redis to initialize..."
    sleep 3

    # Wait and verify Redis is responding
    echo "Checking Redis connectivity..."
    timeout=30
    elapsed=0
    redis_ready=false

    while [ "$redis_ready" = false ] && [ $elapsed -lt $timeout ]; do
        if check_redis_running; then
            redis_ready=true
        else
            sleep 2
            elapsed=$((elapsed + 2))
            echo -n "."
        fi
    done
    echo ""

    if [ "$redis_ready" = true ]; then
        echo "Redis is ready and responding (PONG received)"
    else
        echo "Trying alternative connectivity test..."
        # Fallback test using lsof
        if lsof -i :6379 >/dev/null 2>&1; then
            echo "Redis is listening on port 6379 (fallback test passed)"
        else
            echo "ERROR: Redis failed to become ready within $timeout seconds"
            echo "Checking Redis container logs..."
            docker logs redis-server --tail 10
            exit 1
        fi
    fi
else
    echo "ERROR: Failed to start Redis container"
    exit 1
fi

# Start Qdrant container
echo ""
echo "Setting up Qdrant service..."
if start_docker_container "qdrant-server" "qdrant/qdrant" "-p 6333:6333 -p 6334:6334" "Qdrant"; then
    # Wait for container to be fully ready
    echo "Waiting for Qdrant to initialize..."
    sleep 5

    # Wait and verify Qdrant is responding
    echo "Checking Qdrant connectivity..."
    timeout=45
    elapsed=0
    qdrant_ready=false

    while [ "$qdrant_ready" = false ] && [ $elapsed -lt $timeout ]; do
        if check_qdrant_running; then
            qdrant_ready=true
        else
            sleep 3
            elapsed=$((elapsed + 3))
            echo -n "."
        fi
    done
    echo ""

    if [ "$qdrant_ready" = true ]; then
        echo "Qdrant is ready and responding on port 6333"
    else
        echo "Trying alternative connectivity test..."
        # Fallback test using lsof
        if lsof -i :6333 >/dev/null 2>&1; then
            echo "Qdrant is listening on port 6333 (fallback test passed)"
        else
            echo "ERROR: Qdrant failed to become ready within $timeout seconds"
            echo "Checking Qdrant container logs..."
            docker logs qdrant-server --tail 10
            exit 1
        fi
    fi
else
    echo "ERROR: Failed to start Qdrant container"
    exit 1
fi

# Display service status
echo ""
echo "Service Status Summary:"
docker ps --filter "name=redis-server" --filter "name=qdrant-server" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Find available port for Flask app
echo ""
echo "Finding available port for Flask application..."
flask_port=$(find_available_port 5000)
if [ -z "$flask_port" ]; then
    echo "ERROR: No available ports found in range 5000-5009"
    echo "Please free up some ports or disable AirPlay Receiver in System Preferences"
    exit 1
fi

if [ "$flask_port" != "5000" ]; then
    echo "Port 5000 is in use (likely by AirPlay Receiver)"
    echo "Using alternative port: $flask_port"
    echo "💡 To free port 5000: System Preferences > General > AirDrop & Handoff > Disable AirPlay Receiver"
else
    echo "Port 5000 is available"
fi

# Start ngrok tunnel if available
ngrok_url=""
is_new_tunnel=false
if [ "$ngrok_available" = true ]; then
    echo ""
    echo "Setting up ngrok tunnel for WhatsApp webhook..."

    # Check if tunnel already exists before starting
    existing_url=$(get_ngrok_public_url $flask_port)
    if [ -n "$existing_url" ]; then
        ngrok_url="$existing_url"
        is_new_tunnel=false
        echo "Found existing ngrok tunnel: $ngrok_url"
        echo "Reusing existing tunnel (no reconfiguration needed)"
    else
        # Start new tunnel and capture the URL
        ngrok_url=$(start_ngrok_tunnel $flask_port)
        if [ -n "$ngrok_url" ]; then
            is_new_tunnel=true
        fi
    fi

    if [ -n "$ngrok_url" ]; then
        echo "ngrok tunnel ready: $ngrok_url"
    else
        echo "Failed to establish ngrok tunnel"
    fi
fi

echo ""
echo "All services are ready! Starting Flask application..."
echo "Application will be available at: http://localhost:$flask_port"
if [ -n "$ngrok_url" ]; then
    echo "Public URL (via ngrok): $ngrok_url"
fi
echo "Press Ctrl+C to stop the application"

# Force local Redis for local runs to avoid remote URL overrides
export REDIS_HOST=localhost
export REDIS_URL=redis://localhost:6379

# Display WhatsApp setup information if ngrok is available
if [ -n "$ngrok_url" ]; then
    show_whatsapp_setup "$ngrok_url" "$is_new_tunnel"
fi

# Start Flask application
echo ""
echo "Starting Flask application on port $flask_port..."
export FLASK_RUN_PORT=$flask_port
if [ -f "flask_app/run.py" ]; then
    python flask_app/run.py
elif [ -f "flask_app/app.py" ]; then
    python flask_app/app.py
else
    echo "ERROR: Neither flask_app/run.py nor flask_app/app.py found!"
    echo "Try running manually: FLASK_RUN_PORT=$flask_port python flask_app/app.py"
    exit 1
fi

# Cleanup instructions
echo ""
echo "Application stopped."
echo "To stop Docker services: docker stop redis-server qdrant-server"
if [ -n "$ngrok_url" ]; then
    echo "ngrok tunnel remains active (preserves webhook URL)"
    echo "   To stop ngrok: pkill ngrok"
fi

