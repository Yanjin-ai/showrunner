#!/usr/bin/env bash
# One-line deploy from your Mac:  bash deploy/push_deploy.sh <ECS-public-IP>
# Reads DASHSCOPE_API_KEY (and optional SHOWRUNNER_TOKEN) from the local .env,
# so no secret ever needs to be pasted anywhere. You'll be prompted for the
# ECS root password by ssh itself.
set -euo pipefail
IP=${1:?usage: bash deploy/push_deploy.sh <ECS-public-IP>}
cd "$(dirname "$0")/.."
set -a; source .env; set +a
: "${DASHSCOPE_API_KEY:?DASHSCOPE_API_KEY missing from .env}"

ssh -o StrictHostKeyChecking=accept-new "root@$IP" \
  "export DEBIAN_FRONTEND=noninteractive; \
   apt-get update -qq >/dev/null && apt-get install -y -qq git >/dev/null; \
   rm -rf /root/showrunner && \
   git clone -q https://github.com/Yanjin-ai/showrunner.git /root/showrunner && \
   cd /root/showrunner && \
   DASHSCOPE_API_KEY='$DASHSCOPE_API_KEY' SHOWRUNNER_TOKEN='${SHOWRUNNER_TOKEN:-}' \
   bash deploy/deploy.sh"

echo
echo "==> deployed. Verify:"
echo "    open http://$IP/          (the studio)"
echo "    open http://$IP/healthz   (should show the ECS instance-id = your proof)"
