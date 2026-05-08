import os

bind         = f"0.0.0.0:{os.getenv('PORT', '5000')}"
workers      = 1
threads      = 4
worker_class = "gthread"
timeout      = 120
keepalive    = 5
preload_app  = True
loglevel     = "warning"
capture_output = True
enable_stdio_inheritance = True
forwarded_allow_ips = "*"
