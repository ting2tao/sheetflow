# SheetFlow 部署指南

## 概述

本项目使用 GitHub Actions 自动构建 Docker 镜像并部署到阿里云 ECS。

## 部署架构

```
GitHub Repository
    ↓ (push to main/tag)
GitHub Actions
    ↓ (build & push)
GitHub Container Registry (ghcr.io)
    ↓ (deploy)
阿里云 ECS
```

## 配置步骤

### 1. 启用 GitHub Packages

确保你的 GitHub 仓库已启用 Packages 功能。

### 2. 配置 GitHub Secrets

在仓库的 `Settings` → `Secrets and variables` → `Actions` 中添加以下 secrets：

| Secret 名称 | 说明 | 示例 |
|-------------|------|------|
| `ALIYUN_HOST` | ECS 公网 IP | `47.100.xxx.xxx` |
| `ALIYUN_USER` | SSH 用户名 | `root` |
| `ALIYUN_SSH_KEY` | SSH 私钥 | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `ALIYUN_PORT` | SSH 端口（可选） | `22` |
| `ALIYUN_DEPLOY_PATH` | 部署目录（可选） | `/opt/sheetflow` |
| `ALIYUN_DATA_DIR` | 数据目录（可选） | `/root/sheetflow-data` |
| `GHCR_USERNAME` | GitHub 用户名 | `ting2tao` |
| `GHCR_TOKEN` | GitHub Personal Access Token | `ghp_xxxx` |

同时在 `Settings` → `Secrets and variables` → `Actions` → `Variables`
中添加 GitHub Actions 仓库变量：

| Variable 名称 | 说明 |
|---------------|------|
| `PUBLIC_SITE_URL` | 前端对外公开的 HTTPS 源站地址；建议末尾不带斜杠 |

CI 构建前端镜像时必须读取 `PUBLIC_SITE_URL`，并会拒绝非 HTTPS 地址；未配置时
工作流也会直接失败。该值不是容器启动时配置，而是通过
`VITE_PUBLIC_SITE_URL` 在前端构建时写入。

### 3. ECS 环境准备

确保 ECS 上已安装：
- Docker
- Docker Compose

```bash
# 安装 Docker
curl -fsSL https://get.docker.com | sh

# 启动 Docker
systemctl start docker
systemctl enable docker

# 验证安装
docker --version
docker compose version
```

## 使用方法

### 前端公开地址

构建任何生产前端镜像前，先将 `VITE_PUBLIC_SITE_URL` 设置为部署站点的公开
HTTPS 源站地址。构建会自动移除末尾斜杠，但建议配置时直接省略。该地址会嵌入
以下构建产物：

- canonical 和 hreflang 链接
- Open Graph 与 Twitter Card 元数据
- JSON-LD 结构化数据
- `sitemap.xml` 和 `robots.txt`

下面使用 `https://sheetflow.example` 这一保留域名作为示例；实际构建必须替换成
真实公开源站：

```bash
export VITE_PUBLIC_SITE_URL=https://sheetflow.example
test -n "$VITE_PUBLIC_SITE_URL"

case "$VITE_PUBLIC_SITE_URL" in
  https://*) ;;
  *) echo "VITE_PUBLIC_SITE_URL must use HTTPS" >&2; exit 1 ;;
esac

docker build \
  --build-arg VITE_PUBLIC_SITE_URL="$VITE_PUBLIC_SITE_URL" \
  -t sheetflow-frontend ./frontend
```

使用 Compose 在本地构建时也应显式传入该变量：

```bash
export VITE_PUBLIC_SITE_URL=https://sheetflow.example
test -n "$VITE_PUBLIC_SITE_URL"
docker compose build frontend
```

### 自动构建

推送到 `main` 分支或创建 tag 时，会自动构建并推送镜像：

```bash
# 推送到 main 分支
git push origin main

# 创建版本 tag
git tag v1.0.0
git push origin v1.0.0
```

### 手动部署

1. 进入仓库的 `Actions` 页面
2. 选择 `CI/CD` 工作流
3. 点击 `Run workflow`
4. 填写可选的 `image_tag`：手动运行时留空会部署 `main`，不会自动选择最新的
   Git tag；如需部署版本镜像，必须显式填写其 tag，例如 `v1.0.0`
5. 点击 `Run workflow` 按钮

## 镜像标签说明

| 触发条件 | 镜像标签 |
|---------|---------|
| 推送到 main 分支 | `main` |
| Pull Request | `pr-<number>` |
| 推送 tag `v1.2.3` | `1.2.3`, `1.2` |
| 推送 tag `v1.2.3` | `sha-<commit>` |

## 访问应用

部署完成后：

- **中文前端**：`/zh/`
- **英文前端**：`/en/`
- **后端 API**：`/api/`

生产 Nginx 会将 `/zh` 和 `/en` 以 301 规范重定向到 `/zh/` 和 `/en/`。
根路径 `/` 是语言选择入口；站内语言切换不会刷新应用，因此会保留进行中的状态。
Open Graph 分享图片位于 `/og-image.png`。

部署后可用同一个已验证的公开地址检查关键产物：

```bash
test -n "$VITE_PUBLIC_SITE_URL"

zh_headers=$(curl -fsSI "$VITE_PUBLIC_SITE_URL/zh" | tr -d '\r')
printf '%s\n' "$zh_headers" | grep -q '^HTTP/.* 301'
printf '%s\n' "$zh_headers" | grep -qi "^location: $VITE_PUBLIC_SITE_URL/zh/$"

en_headers=$(curl -fsSI "$VITE_PUBLIC_SITE_URL/en" | tr -d '\r')
printf '%s\n' "$en_headers" | grep -q '^HTTP/.* 301'
printf '%s\n' "$en_headers" | grep -qi "^location: $VITE_PUBLIC_SITE_URL/en/$"

curl -fsS "$VITE_PUBLIC_SITE_URL/zh/" | grep 'lang="zh-CN"'
curl -fsS "$VITE_PUBLIC_SITE_URL/en/" | grep 'lang="en-US"'
curl -fsS "$VITE_PUBLIC_SITE_URL/zh/" | grep -F "$VITE_PUBLIC_SITE_URL/zh/"
curl -fsS "$VITE_PUBLIC_SITE_URL/en/" | grep -F "$VITE_PUBLIC_SITE_URL/en/"
curl -fsS "$VITE_PUBLIC_SITE_URL/robots.txt"
curl -fsS "$VITE_PUBLIC_SITE_URL/sitemap.xml" | grep '/en/'
curl -fsSI "$VITE_PUBLIC_SITE_URL/og-image.png"
```

## 数据持久化

应用数据存储在 `${DATA_DIR}` 目录（默认 `/root/sheetflow-data`），包含：

- `uploads/` - 上传的文件
- `jobs/` - 任务数据
- `outputs/` - 输出文件

## 常见问题

### 部署失败

1. 检查 ECS 是否安装 Docker
2. 检查 SSH 密钥是否正确
3. 检查 GitHub Secrets 配置
4. 查看 Actions 运行日志

### 无法访问应用

1. 检查 ECS 安全组是否开放 80 和 8000 端口
2. 检查容器是否正常运行: `docker compose ps`
3. 查看容器日志: `docker compose logs`

### 更新应用

1. 推送新代码到 main 分支
2. 等待镜像构建完成
3. 手动触发部署或使用最新 tag
