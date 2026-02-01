# AI Project Rules – vps-app

## Project Summary
This is a Flask application deployed to a Hostinger VPS.
The app is run in production using Gunicorn and managed by systemd.

## Critical Deployment Facts
- The app is NOT run with `python app.py` in production.
- Gunicorn is used with systemd.
- systemd service name: `vps-app`
- Port 5000 is already in use by the systemd service.
- App directory: `/root/vps-app`
- Virtual environment: `/root/vps-app/.venv`
- Entry point: `app:app`

## Rules for Changes
- Do NOT suggest replacing Gunicorn with `flask run` or `python app.py`.
- Do NOT suggest using Docker unless explicitly requested.
- Do NOT change ports without updating systemd and documentation.
- Changes must be compatible with `systemctl restart vps-app`.

## Workflow Expectations
- Code changes are made locally.
- Changes are committed to GitHub.
- VPS updates are done via `git pull`.
- Services are restarted via systemd.

## When in Doubt
- Prefer incremental changes over rewrites.
- Ask before changing architecture.
- Assume this project is meant to grow, not be reset.
