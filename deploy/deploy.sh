#!/bin/bash

# 设置错误时退出
set -e

# 本地日志函数
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# 检查必要的环境变量
if [ -z "$SERVER_IP" ] || [ -z "$SERVER_USER" ] || [ -z "$SERVER_PASSWORD" ] || [ -z "$PROJECT_NAME" ]; then
    log "错误：缺少必要的环境变量"
    exit 1
fi

# 定义远程服务器信息
REMOTE_HOST="$SERVER_IP"
REMOTE_USER="$SERVER_USER"
REMOTE_PASS="$SERVER_PASSWORD"
PROJECT_DIR="/root/$PROJECT_NAME"
GITHUB_REPO="https://github.com/tigerbreak/knowledge-graph-analysis.git"
DEPLOY_BRANCH="release/v1.0.3"

# 使用 sshpass 进行密码登录
SSHPASS="sshpass -p $REMOTE_PASS"

# 在远程服务器上执行部署命令
log "正在执行部署命令..."
$SSHPASS ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST << "EOF"
    set -e
    
    # 进入项目目录
    mkdir -p "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    
    # Git 操作
    if [ ! -d ".git" ]; then
        echo "正在克隆代码仓库..."
        git clone "$GITHUB_REPO" .
        git checkout "$DEPLOY_BRANCH"
    else
        echo "正在更新代码..."
        git fetch --all
        git reset --hard "origin/$DEPLOY_BRANCH"
    fi
    
    # 检查并创建必要的目录
    mkdir -p logs
    mkdir -p data/mysql
    mkdir -p data/neo4j
    
    # 复制环境变量文件（如果存在）
    if [ -f .env.example ]; then
        cp .env.example .env
    fi
    
    # 进入部署目录
    cd deploy
    
    # 停止并删除现有容器
    echo "停止现有服务..."
    docker-compose -p beta down || true
    
    # 清理未使用的镜像和卷
    echo "清理旧的构建缓存..."
    docker system prune -f
    
    # 重新构建并启动容器
    echo "开始构建新服务..."
    docker-compose -p beta up --build -d
    
    # 等待服务启动
    echo "等待服务启动..."
    sleep 30
    
    # 检查服务状态
    echo "检查服务状态..."
    docker-compose -p beta ps
    
    # 检查容器健康状态
    echo "检查容器健康状态..."
    if ! docker-compose -p beta ps | grep -q "Up"; then
        echo "错误：部分服务未能正常启动"
        docker-compose -p beta logs
        exit 1
    fi
    
    # 检查服务可访问性
    echo "检查服务可访问性..."
    curl -f http://localhost:8000/api/health || {
        echo "错误：后端服务未能正常响应"
        docker-compose -p beta logs backend
        exit 1
    }
EOF

if [ $? -eq 0 ]; then
    log "部署完成！"
else
    log "部署失败！请检查日志"
    exit 1
fi 