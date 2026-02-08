# VPS App Deployment

## Overview
Simple Flask app deployed to a Hostinger VPS using:
- Python + Flask
- Gunicorn
- systemd service

## Server
- OS: Ubuntu 24.04
- IP: 76.13.101.176
- User: root
- App directory: /root/vps-app

## App
- Entry point: app.py
- Flask app object: app
- Port: 5000

## Virtual Environment
- Path: /root/vps-app/.venv

## Service
- systemd service: vps-app.service
- ExecStart:
  /root/vps-app/.venv/bin/gunicorn --bind 0.0.0.0:5000 app:app

## Common Commands

### Restart app
sudo systemctl restart vps-app

### View status
sudo systemctl status vps-app --no-pager

### View logs
journalctl -u vps-app -n 50 --no-pager

### Update code
git pull
sudo systemctl restart vps-app

## Background Jobs

This project uses systemd timers for background ingestion tasks.

Active jobs:
- `vps-balance-ingest.timer`
  - Runs `email_ingest.py` once per day
  - Ingests daily balance emails
  - Writes to SQLite database

Systemd unit files live in:
- `/etc/systemd/system/` on the server

Template/example unit files are stored in the repo under:
- `/systemd/`
