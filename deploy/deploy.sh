#!/bin/bash

# 设置错误时退出
set -e

# 设置默认值
PROJECT_NAME=${PROJECT_NAME:-"myproject"}
MAX_RETRIES=10
RETRY_INTERVAL=3

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

# 部署函数
deploy() {
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
        # 设置显示时间的函数
        log() {
            echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
        }

        # 显示系统信息
        log "系统信息："
        df -h | grep /dev/vda1
        log "Docker 信息："
        docker system df -v

        # 登录到阿里云容器镜像服务
        log "登录到阿里云容器镜像服务..."
        echo "$ALIYUN_PASSWORD" | docker login -u "$ALIYUN_USERNAME" --password-stdin $ALIYUN_REGISTRY

        # 显示拉取前的镜像列表
        log "拉取前的镜像列表："
        docker images | grep "$DOCKER_IMAGE" || true

        # 拉取最新镜像并显示进度
        log "=== 开始拉取后端镜像 ==="
        docker pull "$DOCKER_IMAGE:backend-$GITHUB_SHA" 2>&1 | while read line; do
            echo "[后端] $line"
        done
        docker tag "$DOCKER_IMAGE:backend-$GITHUB_SHA" "$DOCKER_IMAGE:backend-latest"
        
        log "=== 开始拉取前端镜像 ==="
        docker pull "$DOCKER_IMAGE:frontend-$GITHUB_SHA" 2>&1 | while read line; do
            echo "[前端] $line"
        done
        docker tag "$DOCKER_IMAGE:frontend-$GITHUB_SHA" "$DOCKER_IMAGE:frontend-latest"

        # 显示拉取后的镜像信息
        log "拉取后的镜像列表："
        docker images | grep "$DOCKER_IMAGE"

        # 显示镜像大小变化
        log "镜像存储信息："
        docker system df -v | grep -A 10 "Images space usage:"

        # 进入项目目录
        cd $PROJECT_DIR/docker || exit 1
        log "当前工作目录: $(pwd)"
        
        # 检查 docker-compose.yml 是否存在
        if [ ! -f "docker-compose.yml" ]; then
            log "错误: docker-compose.yml 文件不存在"
            exit 1
        fi

        # 停止并删除旧容器
        log "停止并删除旧容器..."
        docker-compose ps
        docker-compose down

        # 启动新容器
        log "启动新容器..."
        docker-compose up -d

        # 等待容器启动完成并显示启动进度
        log "等待容器启动..."
        for i in {1..10}; do
            echo -n "."
            sleep 1
        done
        echo ""

        # 检查容器状态
        if docker-compose ps | grep -q "Up"; then
            log "新容器启动成功，开始清理旧镜像..."
            
            # 获取当前使用的镜像ID
            CURRENT_IMAGES=$(docker-compose images -q)
            
            # 显示要清理的镜像信息
            log "准备清理的镜像："
            docker images | grep "$DOCKER_IMAGE" | grep -v "latest" | grep -v "$GITHUB_SHA" || true
            
            # 删除所有未被使用的镜像
            docker image prune -af --filter "until=24h" --filter "label!=com.docker.compose.service"
            
            log "旧镜像清理完成！"

            # 显示最终状态
            log "=== 部署完成状态 ==="
            log "1. 容器状态："
            docker-compose ps
            log "2. 剩余镜像："
            docker images | grep "$DOCKER_IMAGE"
            log "3. 系统存储状态："
            df -h | grep /dev/vda1
            docker system df -v
        else
            log "容器启动失败，保留旧镜像以便回滚"
            log "失败的容器状态："
            docker-compose ps
            log "容器日志："
            docker-compose logs --tail=50
            exit 1
        fi
EOF
}

# 执行部署，带重试机制
attempt=1
while [ $attempt -le $MAX_RETRIES ]; do
    log "尝试部署 (第 $attempt 次)"
    if deploy; then
        log "部署成功！"
        exit 0
    else
        if [ $attempt -lt $MAX_RETRIES ]; then
            log "部署失败，${RETRY_INTERVAL}秒后重试..."
            sleep $RETRY_INTERVAL
        else
            log "已达到最大重试次数($MAX_RETRIES)，部署失败"
            exit 1
        fi
    fi
    attempt=$((attempt + 1))
done 