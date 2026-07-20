# ECS 最简部署(10 分钟,3 步)

目标:让评委打开 `http://<你的IP>/` 就能看到 live studio。以下是最省事的路径,
全程只需要复制粘贴 4 条命令。

## 第 1 步 · 买一台 ECS(约 3 分钟)

1. 打开 [ECS 控制台](https://ecs.console.aliyun.com/) → **创建实例**。
2. 选这几项,其他全部默认:
   - **地域**:新加坡(ap-southeast-1)— 和 DashScope intl 网关同区,延迟最低
   - **规格**:`ecs.e-c1m2.large`(2 vCPU / 4 GiB,经济型)— 按量付费,一天几块钱
   - **镜像**:Ubuntu 22.04 64 位
   - **公网 IP**:勾选「分配公网 IPv4」,按使用流量计费,带宽峰值 5 Mbps 即可
   - **登录凭证**:设 root 密码(或密钥对,能 ssh 上去就行)
3. 创建后在实例列表里记下**公网 IP**。

## 第 2 步 · 开防火墙端口(1 分钟)

实例详情 → **安全组** → 配置规则 → **入方向手动添加**:

| 端口 | 授权对象 | 用途 |
|---|---|---|
| 80 | 0.0.0.0/0 | 评委访问 studio(nginx 反代) |
| 22 | 0.0.0.0/0 | 你自己 ssh |

## 第 3 步 · 一条命令部署(约 5 分钟)

ssh 上去,把两处 `sk-ws-…`/`你的token` 换成真实值后整段粘贴:

```bash
ssh root@<你的公网IP>

git clone https://github.com/Yanjin-ai/showrunner.git && cd showrunner && \
DASHSCOPE_API_KEY=sk-ws-你的key SHOWRUNNER_TOKEN=你的token bash deploy/deploy.sh
```

脚本会自动装 ffmpeg + 中文字体 + nginx,建 systemd 服务并启动。
结束时会打印 `done. Open http://<IP>/`。

**验证:**

```bash
curl http://127.0.0.1/healthz     # 应返回 {"ok": true, ...}
```

浏览器打开 `http://<你的公网IP>/` → 看到 studio 即成功。把这个地址填进 Devpost 的
Try it out,并截一张「浏览器地址栏带公网 IP + studio 界面」的图,就是 Devpost 要求的
**proof of Alibaba Cloud deployment**。

## 常见问题

- **打不开页面** → 九成是安全组 80 没开(第 2 步);其余看 `journalctl -u showrunner -f`。
- **要改 .env** → `nano /opt/showrunner/.env` 后 `systemctl restart showrunner`。
- **省钱** → 演示期结束后在控制台「停止(节省停机模式)」,评审期间保持运行。
- **SHOWRUNNER_TOKEN 的作用** → 评委可以*看*所有内容;但生成/重拍等花钱操作需要
  这个 token(UI 会弹框输入),防止陌生人烧你的 API 额度。

## 替代方案(不推荐,但更熟悉 Docker 的话)

```bash
git clone https://github.com/Yanjin-ai/showrunner.git && cd showrunner
cp .env.example .env && nano .env      # 填 key
docker compose up -d --build           # 需要先 apt install docker.io docker-compose-v2
```

systemd 方案(上面第 3 步)更省内存,4 GiB 机器上更稳,优先用它。
