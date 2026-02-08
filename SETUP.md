# Project Setup & Re-entry Guide

## Local Development
- Python 3.12
- Virtual environment required
- SQLite used for storage

## Production (VPS)
- Ubuntu server
- Flask app runs via Gunicorn + systemd
- Background jobs via systemd timers
- Database stored at `data/app.db`

## Common Commands

Restart app:
sudo systemctl restart vps-app

Run ingestion now:
sudo systemctl start vps-balance-ingest.service

View ingestion logs:
journalctl -u vps-balance-ingest.service
