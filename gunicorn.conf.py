"""
Gunicorn configuration for Django Grant Management System
Render.com production WSGI server configuration
"""

import multiprocessing
import os

# Bind settings - Use PORT environment variable from Render
port = os.environ.get('PORT', '10000')
bind = f"0.0.0.0:{port}"

# Worker settings
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 50

# Restart workers after this many requests to prevent memory leaks
preload_app = True

# Logging - Use stdout/stderr for Render
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'django_grant_system'

# Server mechanics - Don't specify user/group for Render
daemon = False

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Performance tuning
worker_class = 'sync'  # Use sync for simplicity on Render
worker_connections = 1000

# Graceful timeout for workers
graceful_timeout = 30

# Hooks
def on_starting(server):
    server.log.info("Django Grant Management System starting...")

def on_reload(server):
    server.log.info("Django Grant Management System reloading...")

def worker_int(worker):
    worker.log.info("Worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def worker_abort(worker):
    worker.log.info("Worker received SIGABRT signal")