"""One model cache per container; platform provides HTTPS and the public port."""
import os

bind = "0.0.0.0:" + os.environ.get("PORT", "8080")
workers = 1
threads = 2
timeout = 120
graceful_timeout = 30
accesslog = None
errorlog = "-"
capture_output = False
