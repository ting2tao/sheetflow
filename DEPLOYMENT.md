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
2. 选择 `Deploy to Aliyun ECS` 工作流
3. 点击 `Run workflow`
4. 输入镜像 tag（默认为 `latest`）
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

- **前端**: `http://<ECS_IP>:80`
- **后端 API**: `http://<ECS_IP>:8000`

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
