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

## Feature: Daily Balance Tracking (v1)

Goal:
- Read a daily balance email
- Store one balance per day
- Display balances on the dashboard

Architecture Rules:
- app.py remains thin (routes + rendering only)
- Email logic must live outside app.py
- Database access must be centralized
- SQLite is acceptable for v1
- No background threads inside Flask routes

Data Flow:
- Email ingestion runs separately from web requests
- Flask only reads from the database
- One row per day, idempotent inserts

Non-Goals (for v1):
- Charts
- Multiple accounts
- Real-time email polling
- Docker

## Data Ingestion & Future Scope

Long-term Vision:
- This project may eventually ingest multiple types of email-based data
  (balances, transactions, bills, reminders, etc.)
- The system is expected to grow into a general personal tracking system
  (finance, tasks, projects).

Architecture Rules:
- Email ingestion must be isolated from Flask routes
- Ingestion sources (IMAP, Gmail API, others) must be swappable
- Core database models should not depend on email protocol details
- Prefer normalized “event-like” records over tightly coupled schemas

Current Scope (v1):
- Only daily balance ingestion is in scope
- IMAP is acceptable for v1 ingestion
- No generalized transaction or bill tracking yet

## Server-Level Configuration Rules

- systemd unit files are deployment artifacts
- Real unit files live only on the server
- Templates/examples must live in the repo
- Secrets must never be committed
- Background work must never run inside Flask routes
- Background jobs must be observable via systemd logs
