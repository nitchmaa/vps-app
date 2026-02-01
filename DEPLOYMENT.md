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
