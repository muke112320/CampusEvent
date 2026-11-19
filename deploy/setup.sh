#!/usr/bin/env bash
# 在 Ubuntu 22.04/24.04 上一键准备 CampusEvent 运行环境（在项目根目录执行）
set -euo pipefail

APP_DIR="/opt/campusevent"
SERVICE_USER="campusevent"

if ! id "$SERVICE_USER" >/dev/null 2>&1; then
  sudo useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin "$SERVICE_USER"
fi

sudo mkdir -p "$APP_DIR"
sudo cp -r app tests deploy requirements*.txt run.py wsgi.py README.md "$APP_DIR"/
sudo chown -R "$SERVICE_USER":"$SERVICE_USER" "$APP_DIR"

cd "$APP_DIR"
sudo -u "$SERVICE_USER" python3 -m venv .venv
sudo -u "$SERVICE_USER" .venv/bin/pip install --upgrade pip
sudo -u "$SERVICE_USER" .venv/bin/pip install -r requirements-prod.txt
sudo -u "$SERVICE_USER" .venv/bin/python -c "from app import create_app; create_app()"

sudo cp deploy/campusevent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now campusevent

sudo cp deploy/nginx-campusevent.conf /etc/nginx/sites-available/campusevent
sudo ln -sf /etc/nginx/sites-available/campusevent /etc/nginx/sites-enabled/campusevent
sudo nginx -t
sudo systemctl reload nginx

echo "部署完成。检查：systemctl status campusevent；curl -I http://127.0.0.1/"
