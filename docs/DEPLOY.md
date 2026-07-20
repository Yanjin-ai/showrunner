# Deploy on Alibaba Cloud (submission requirement: proof of deployment)

Deploy in the **Singapore (ap-southeast-1)** region to match the DashScope-intl video endpoint.

## Option A — Docker (any host)

```bash
cp .env.example .env    # set DASHSCOPE_API_KEY and (for public hosts) SHOWRUNNER_TOKEN
docker compose up -d --build
# http://<host>:8000 · health: /healthz · state persists in ./runs ./library ./logs
```
Single container, single process **by design** (in-memory gates + one job queue serializing
generation against one API key). Do not scale with --workers or replicas.

## Option B — one command on a fresh Ubuntu ECS

On a fresh Ubuntu 22.04 ECS, clone the repo and run:
```bash
bash deploy/deploy.sh          # installs ffmpeg + fonts-noto-cjk + nginx, sets up systemd + reverse proxy
# then: edit /opt/showrunner/.env to add DASHSCOPE_API_KEY, and: sudo systemctl restart showrunner
```
Open port 80 in the ECS security group, then browse to `http://<ECS-public-ip>/`.
Service management: `journalctl -u showrunner -f` · `systemctl restart showrunner`.
Assets: [`deploy/deploy.sh`](../deploy/deploy.sh) · [`deploy/showrunner.service`](../deploy/showrunner.service) · [`deploy/nginx.conf`](../deploy/nginx.conf).

## Manual steps (reference)

## 1. ECS instance
- Ubuntu 22.04, 2 vCPU / 4 GB is enough (generation runs on Alibaba's side, not the box).
- Security group: allow inbound TCP **8000** (dashboard) and 22 (SSH).

## 2. Provision
```bash
sudo apt update && sudo apt install -y python3-venv ffmpeg git
git clone <your-public-repo> showrunner && cd showrunner
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # paste DASHSCOPE_API_KEY; keep the -intl endpoints
python -m scripts.smoke_test   # confirm model IDs on the deployed box
```

## 3. Run the service
```bash
uvicorn showrunner.server:app --host 0.0.0.0 --port 8000
# production: nohup uvicorn showrunner.server:app --host 0.0.0.0 --port 8000 &  (or a systemd unit)
```
Open `http://<ECS-public-ip>:8000` — the dashboard is your proof-of-deployment shot for the demo video.

## 4. (Optional) OSS for image-to-video consistency
If you enable reference-to-video, generated reference frames must be at a public URL. Create an OSS
bucket in ap-southeast-1, upload frames, and pass their URLs as `img_url`. Without OSS the pipeline
falls back to text-level consistency (appearance descriptors baked into every prompt), which needs no
public storage and always works.

## Proof-of-deployment checklist for Devpost
- [ ] Screenshot/scene of the dashboard served from the ECS public IP
- [ ] `smoke_test` output run on the ECS box (shows live QwenCloud calls)
- [ ] Region = ap-southeast-1 visible in console
