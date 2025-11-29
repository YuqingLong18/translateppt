# Gunicorn configuration file for production deployment
import multiprocessing

# Server socket
bind = "127.0.0.1:3001"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = "/www/wwwroot/translateppt/logs/access.log"
errorlog = "/www/wwwroot/translateppt/logs/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "translateppt"

# Server mechanics
daemon = False
pidfile = "/www/wwwroot/translateppt/gunicorn.pid"
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = None
# certfile = None

# Application
chdir = "/www/wwwroot/translateppt"

