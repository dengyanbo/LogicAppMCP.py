"""WSGI entrypoint for Azure Web Apps and gunicorn.

This module exposes the FastAPI instance as ``application`` and ``app`` so
platform defaults like ``gunicorn --bind=0.0.0.0 --timeout 600 application:app``
can discover it without a custom startup command.
"""

from app.main import app as application

# gunicorn expects ``app`` by default; provide both names for clarity.
app = application
