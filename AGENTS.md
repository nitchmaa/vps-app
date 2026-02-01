# AI Project Instructions

- This is a VPS-hosted Flask app.
- Deployment uses Gunicorn + systemd.
- Do NOT suggest running with `python app.py` in production.
- Port 5000 is already in use by systemd service.
- Changes must be compatible with systemd restarts.
- Prefer incremental changes over rewrites.
