#!/usr/bin/env bash
# One-command deploy to a fresh Ubuntu 22.04 ECS in Alibaba Cloud ap-southeast-1 (Singapore).
# Run from the repo root on the ECS box:  bash deploy/deploy.sh
set -euo pipefail

APP=/opt/showrunner

# tiny instances (512 MiB) need swap or pip/ffmpeg get OOM-killed
if [ "$(awk '/MemTotal/{print $2}' /proc/meminfo)" -lt 1048576 ] && [ ! -f /swapfile ]; then
  echo "==> small RAM detected: adding 2G swapfile"
  sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
  sudo mkswap /swapfile >/dev/null && sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
fi

# mainland-China regions: use the Aliyun PyPI mirror
PIP_MIRROR=""
if curl -s --max-time 2 http://100.100.100.200/latest/meta-data/region-id | grep -q "^cn-"; then
  PIP_MIRROR="-i https://mirrors.aliyun.com/pypi/simple/"
fi

echo "==> installing system deps (ffmpeg, CJK fonts for burned subtitles, nginx)"
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip ffmpeg fonts-noto-cjk git nginx rsync

echo "==> syncing app to $APP"
sudo mkdir -p "$APP"
sudo rsync -a --exclude .venv --exclude runs --exclude .git ./ "$APP"/

echo "==> python env"
cd "$APP"
python3 -m venv .venv
.venv/bin/pip install -q -U pip $PIP_MIRROR
.venv/bin/pip install -q -r requirements.txt $PIP_MIRROR

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
