# 🚀 Quick Start Guide - AI-Powered Customer Support Agent

## Prerequisites Setup

### 1. **Docker Desktop** (Required)
**YES, you need Docker Desktop running before executing the PowerShell scripts!**

- ✅ **Install Docker Desktop** from [docker.com](https://docker.com)
- ✅ **Start Docker Desktop** and wait for it to fully initialize
- ✅ **Verify it's running**: You should see the Docker icon in your system tray

### 2. **Python Environment** (Required)
- ✅ **Activate your Python environment**: `(llm)` environment as shown in your terminal
- ✅ **Install dependencies**: `pip install -r requirements.txt`

### 3. **Environment Configuration** (Required)
- ✅ **Create `.env` file** from `.env_example` with your API keys
- ✅ **PostgreSQL database** should be accessible (configured in `.env`)

## 🎯 Easy Startup Options

### **Option 1: Automated Startup (Recommended)**
```bash
# Just run this one command!
./start_services.ps1
```

This script will:
- ✅ Check if Docker is running
- ✅ Start Redis container (port 6379)
- ✅ Start Qdrant container (ports 6333-6334)
- ✅ Wait for services to be ready
- ✅ Start the Flask application
- ✅ Show you service status

### **Option 2: Manual Startup**
```bash
# Start Docker containers
docker run -d --name redis-server -p 6379:6379 redis:latest
docker run -d --name qdrant-server -p 6333:6333 -p 6334:6334 qdrant/qdrant

# Start Flask app
python flask_app/app.py
```

### **Option 3: Using Existing Containers**
```bash
# If containers already exist, just start them
docker start redis-server qdrant-server

# Then start Flask app
python flask_app/app.py
```

## 📊 Service Management

### **Stop All Services**
```bash
./stop_services.ps1
```

### **Check Service Status**
```bash
docker ps
```

### **View Logs**
```bash
# Redis logs
docker logs redis-server

# Qdrant logs
docker logs qdrant-server
```

### **Clean Up (Remove Containers)**
```bash
docker stop redis-server qdrant-server
docker rm redis-server qdrant-server
```

## 🌐 Access Your Application

Once all services are running:

- **Main Application**: http://localhost:5000
- **Alternative URL**: http://127.0.0.1:5000
- **Qdrant Dashboard**: http://localhost:6333/dashboard (if available)

## 🔧 Troubleshooting

### **"Redis connection refused" Error**
- ✅ Make sure Docker Desktop is running
- ✅ Run: `docker start redis-server`
- ✅ Check: `docker ps` shows redis-server running

### **"Qdrant connection failed" Error**
- ✅ Make sure Docker Desktop is running
- ✅ Run: `docker start qdrant-server`
- ✅ Check: `docker ps` shows qdrant-server running

### **"Docker is not running" Error**
- ✅ **Open Docker Desktop application**
- ✅ **Wait for it to fully start** (green icon in system tray)
- ✅ **Try the script again**

### **Permission Issues with PowerShell**
```bash
# Run this once to allow script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### **Flask App Won't Start**
- ✅ Check you're in the correct directory
- ✅ Ensure Python environment is activated: `(llm)`
- ✅ Install dependencies: `pip install -r requirements.txt`
- ✅ Check `.env` file exists with proper API keys

## 🎯 Expected Success Output

When everything works correctly, you should see:

```
🚀 Starting AI-Powered Customer Support Agent Services...
🐳 Checking Docker availability...
✅ Docker is running

📦 Setting up Redis service...
✅ Redis container started successfully
✅ Redis is ready and responding on port 6379

📦 Setting up Qdrant service...
✅ Qdrant container started successfully
✅ Qdrant is ready and responding on port 6333

🌐 All services are ready! Starting Flask application...
📍 Application will be available at: http://localhost:5000

* Running on all addresses (0.0.0.0)
* Running on http://127.0.0.1:5000
```

## 📋 Daily Workflow

1. **Start of day**: `./start_services.ps1`
2. **Work on your app**: Access http://localhost:5000
3. **End of day**: Press `Ctrl+C` to stop Flask, then `./stop_services.ps1`

## 🆘 Need Help?

- **Check service status**: `docker ps`
- **View container logs**: `docker logs <container-name>`
- **Restart everything**: `./stop_services.ps1` then `./start_services.ps1`
- **Full reset**: Remove containers and restart from scratch

---

**Happy coding! 🎉** Your AI-powered customer support agent is ready to serve Nigerian e-commerce customers!
