#!/bin/bash

# 设置错误时退出
set -e

# 设置默认值
PROJECT_NAME=${PROJECT_NAME:-"myproject"}
GITHUB_REPO=${GITHUB_REPO:-"https://github.com/tigerbreak/knowledge-graph-analysis.git"}

# 本地日志函数
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# 检查必要的环境变量
if [ -z "$SERVER_IP" ] || [ -z "$SERVER_USER" ] || [ -z "$SERVER_PASSWORD" ] || [ -z "$PROJECT_NAME" ] || [ -z "$DOCKER_USERNAME" ] || [ -z "$DOCKER_PASSWORD" ]; then
    echo "错误：缺少必要的环境变量"
    exit 1
fi

# 定义远程服务器信息
REMOTE_HOST="$SERVER_IP"
REMOTE_USER="$SERVER_USER"
REMOTE_PASS="$SERVER_PASSWORD"
PROJECT_DIR="/root/$PROJECT_NAME"
DEPLOY_BRANCH="release/v1.0.3"

# 设置变量
DOCKER_IMAGE="$DOCKER_USERNAME/knowledge-graph"
GITHUB_SHA=$(git rev-parse HEAD)

# 输出环境变量信息（不包含密码）
log "部署配置信息："
log "远程主机：$REMOTE_HOST"
log "远程用户：$REMOTE_USER"
log "项目名称：$PROJECT_NAME"
log "项目目录：$PROJECT_DIR"
log "GitHub仓库：$GITHUB_REPO"
log "部署分支：$DEPLOY_BRANCH"

# 使用 sshpass 进行密码登录
SSHPASS="sshpass -p $REMOTE_PASS"

# 登录到服务器
echo "登录到服务器..."
sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << EOF
    # 登录到 Docker Hub
    echo "登录到 Docker Hub..."
    echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin

    # 拉取最新镜像
    echo "拉取后端镜像..."
    docker pull "$DOCKER_IMAGE:backend-$GITHUB_SHA"
    docker tag "$DOCKER_IMAGE:backend-$GITHUB_SHA" "$DOCKER_IMAGE:backend-latest"

    echo "拉取前端镜像..."
    docker pull "$DOCKER_IMAGE:frontend-$GITHUB_SHA"
    docker tag "$DOCKER_IMAGE:frontend-$GITHUB_SHA" "$DOCKER_IMAGE:frontend-latest"

    # 进入项目目录
    cd /root/$PROJECT_NAME

    # 停止并删除旧容器
    echo "停止并删除旧容器..."
    docker-compose down

    # 启动新容器
    echo "启动新容器..."
    docker-compose up -d

    # 清理未使用的镜像
    echo "清理未使用的镜像..."
    docker image prune -f
EOF

echo "部署完成！" 