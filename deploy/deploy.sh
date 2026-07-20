#!/usr/bin/env bash
# One-command deploy to a fresh Ubuntu 22.04 ECS in Alibaba Cloud ap-southeast-1 (Singapore).
# Run from the repo root on the ECS box:  bash deploy/deploy.sh
set -euo pipefail

APP=/opt/showrunner

echo "==> installing system deps (ffmpeg, CJK fonts for burned subtitles, nginx)"
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip ffmpeg fonts-noto-cjk git nginx rsync

echo "==> syncing app to $APP"
sudo mkdir -p "$APP"
sudo rsync -a --exclude .venv --exclude runs --exclude .git ./ "$APP"/

echo "==> python env"
cd "$APP"
python3 -m venv .venv
.venv/bin/pip install -q -U pip
.venv/bin/pip install -q -r requirements.txt

if [ ! -f "$APP/.env" ]; then
  cp .env.example .env
  # keys can be passed inline:  DASHSCOPE_API_KEY=sk-ws-xxx bash deploy/deploy.sh
  if [ -n "${DASHSCOPE_API_KEY:-}" ]; then
    sed -i "s|^DASHSCOPE_API_KEY=.*|DASHSCOPE_API_KEY=$DASHSCOPE_API_KEY|" .env
  else
    echo "!!! edit $APP/.env and set DASHSCOPE_API_KEY, then: sudo systemctl restart showrunner"
  fi
  if [ -n "${SHOWRUNNER_TOKEN:-}" ]; then
    sed -i "s|^SHOWRUNNER_TOKEN=.*|SHOWRUNNER_TOKEN=$SHOWRUNNER_TOKEN|" .env
  fi
fi

echo "==> service user + systemd"
sudo useradd -r -s /usr/sbin/nologin showrunner 2>/dev/null || true
sudo chown -R showrunner:showrunner "$APP"
sudo cp deploy/showrunner.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now showrunner

echo "==> nginx reverse proxy"
sudo cp deploy/nginx.conf /etc/nginx/sites-available/showrunner
sudo ln -sf /etc/nginx/sites-available/showrunner /etc/nginx/sites-enabled/showrunner
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

IP=$(curl -s https://api.ipify.org || echo "<ECS-public-ip>")
echo "==> done. Open http://$IP/   (open port 80 in the ECS security group)"
echo "    logs: journalctl -u showrunner -f"
