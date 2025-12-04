"""Gunicorn configuration for running the FastAPI ASGI app on Azure App Service.

App Service auto-detects Python apps and boots gunicorn with a WSGI-style
command (`gunicorn application:app`). FastAPI is ASGI, so we select the
UvicornWorker to serve ASGI traffic correctly and keep the platform defaults
for host/timeout.
"""
from uvicorn.workers import UvicornWorker

worker_class = "uvicorn.workers.UvicornWorker"
# Align with the platform-generated command `--timeout 600`.
timeout = 600
