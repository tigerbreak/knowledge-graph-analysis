#!/bin/bash

# 设置错误时退出
set -e

# 设置默认值
PROJECT_NAME=${PROJECT_NAME:-"myproject"}

# 本地日志函数
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# 检查必要的环境变量
if [ -z "$SERVER_IP" ] || [ -z "$SERVER_USER" ] || [ -z "$SERVER_PASSWORD" ] || [ -z "$PROJECT_NAME" ] || [ -z "$ALIYUN_USERNAME" ] || [ -z "$ALIYUN_PASSWORD" ]; then
    echo "错误：缺少必要的环境变量"
    exit 1
fi

# 定义远程服务器信息
REMOTE_HOST="$SERVER_IP"
REMOTE_USER="$SERVER_USER"
REMOTE_PASS="$SERVER_PASSWORD"
PROJECT_DIR="/root/$PROJECT_NAME"

# 设置变量
ALIYUN_REGISTRY="registry.cn-hongkong.aliyuncs.com"
ALIYUN_NAMESPACE="tongihttigerbreak"
ALIYUN_REPOSITORY="tigerhouse"
DOCKER_IMAGE="$ALIYUN_REGISTRY/$ALIYUN_NAMESPACE/$ALIYUN_REPOSITORY"
GITHUB_SHA=$(git rev-parse HEAD)

# 输出环境变量信息（不包含密码）
log "部署配置信息："
log "远程主机：$REMOTE_HOST"
log "远程用户：$REMOTE_USER"
log "项目名称：$PROJECT_NAME"
log "项目目录：$PROJECT_DIR"
log "Docker镜像：$DOCKER_IMAGE"
log "Git提交：$GITHUB_SHA"

# 登录到服务器
echo "登录到服务器..."
sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << EOF
    # 登录到阿里云容器镜像服务
    echo "登录到阿里云容器镜像服务..."
    echo "$ALIYUN_PASSWORD" | docker login -u "$ALIYUN_USERNAME" --password-stdin $ALIYUN_REGISTRY

    # 拉取最新镜像
    echo "拉取后端镜像..."
    docker pull "$DOCKER_IMAGE:backend-$GITHUB_SHA"
    docker tag "$DOCKER_IMAGE:backend-$GITHUB_SHA" "$DOCKER_IMAGE:backend-latest"

    echo "拉取前端镜像..."
    docker pull "$DOCKER_IMAGE:frontend-$GITHUB_SHA"
    docker tag "$DOCKER_IMAGE:frontend-$GITHUB_SHA" "$DOCKER_IMAGE:frontend-latest"

    # 进入项目目录
    cd $PROJECT_DIR

    # 停止并删除旧容器
    echo "停止并删除旧容器..."
    docker-compose down

    # 启动新容器
    echo "启动新容器..."
    docker-compose up -d

    # 等待容器启动完成
    echo "等待容器启动..."
    sleep 10

    # 检查容器状态
    if docker-compose ps | grep -q "Up"; then
        echo "新容器启动成功，开始清理旧镜像..."
        
        # 获取当前使用的镜像ID
        CURRENT_IMAGES=$(docker-compose images -q)
        
        # 删除所有未被使用的镜像（除了当前正在使用的）
        docker image prune -af --filter "until=24h" --filter "label!=com.docker.compose.service"
        
        echo "旧镜像清理完成！"
    else
        echo "容器启动失败，保留旧镜像以便回滚"
        exit 1
    fi
EOF

if [ $? -eq 0 ]; then
    echo "部署成功！"
    exit 0
else
    echo "部署失败！"
    exit 1
fi 