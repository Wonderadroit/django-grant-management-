"""
Gunicorn configuration for Django Grant Management System
Production WSGI server configuration
"""

import multiprocessing
import os

# Bind settings
bind = "0.0.0.0:8000"
backlog = 2048

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

# Logging
accesslog = "/var/log/djf/gunicorn-access.log"
errorlog = "/var/log/djf/gunicorn-error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'djf_grant_system'

# Server mechanics
daemon = False
pidfile = '/var/run/djf/gunicorn.pid'
user = 'djf'
group = 'djf'
tmp_upload_dir = None

# SSL (if using Gunicorn for SSL termination)
# keyfile = '/path/to/ssl/private.key'
# certfile = '/path/to/ssl/certificate.crt'

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Memory management
worker_tmp_dir = '/dev/shm'

# Performance tuning
worker_class = 'gevent'  # Use gevent for better concurrency
worker_connections = 1000

# Graceful timeout for workers
graceful_timeout = 30

# Environment variables
raw_env = [
    'DJANGO_SETTINGS_MODULE=core.settings_production',
]

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