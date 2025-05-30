"""
Gunicorn Configuration for Nigerian E-commerce Customer Support Agent
Production-ready WSGI server configuration optimized for Nigerian market usage
"""

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "eventlet"  # For WebSocket support and async operations
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after processing this many requests
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "nigerian_customer_support"

# Server mechanics
daemon = False
pidfile = "logs/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# SSL (uncomment for HTTPS in production)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Nigerian market specific optimizations
worker_tmp_dir = "/dev/shm"  # Use tmpfs for better performance
preload_app = True  # Load application before forking workers

# Environment variables
raw_env = [
    'FLASK_ENV=production',
    'TZ=Africa/Lagos',  # Nigerian timezone
]

def when_ready(server):
    """Called when the server is started."""
    server.log.info("  Nigerian Customer Support Agent started successfully!")
    server.log.info(f"Workers: {workers}, Connections per worker: {worker_connections}")

def worker_int(worker):
    """Called when a worker receives the INT or QUIT signal."""
    worker.log.info("Worker received INT/QUIT signal")

def pre_fork(server, worker):
    """Called before forking a new worker."""
    server.log.info(f"Worker spawned (pid: {worker.pid})")

def post_fork(server, worker):
    """Called after a worker has been forked."""
    server.log.info(f"Worker spawned and ready (pid: {worker.pid})")

def pre_exec(server):
    """Called before exec()."""
    server.log.info("Forked child, re-executing.")

def on_exit(server):
    """Called when gunicorn is shutting down."""
    server.log.info("  Nigerian Customer Support Agent shutting down...")

def on_reload(server):
    """Called when gunicorn is reloading."""
    server.log.info("🔄 Nigerian Customer Support Agent reloading...")
