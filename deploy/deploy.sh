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
if [ -z "$SERVER_IP" ] || [ -z "$SERVER_USER" ] || [ -z "$SERVER_PASSWORD" ]; then
    log "错误：缺少必要的环境变量"
    log "SERVER_IP: $SERVER_IP"
    log "SERVER_USER: $SERVER_USER"
    log "PROJECT_NAME: $PROJECT_NAME"
    log "GITHUB_REPO: $GITHUB_REPO"
    exit 1
fi

# 定义远程服务器信息
REMOTE_HOST="$SERVER_IP"
REMOTE_USER="$SERVER_USER"
REMOTE_PASS="$SERVER_PASSWORD"
PROJECT_DIR="/root/$PROJECT_NAME"
DEPLOY_BRANCH="release/v1.0.3"

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

# 在远程服务器上执行部署命令
log "正在执行部署命令..."
$SSHPASS ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST "export PROJECT_NAME='$PROJECT_NAME' && export PROJECT_DIR='/root/$PROJECT_NAME' && export GITHUB_REPO='$GITHUB_REPO' && bash -s" << 'EOF'
    set -e
    
    # 输出当前目录和环境变量
    echo "当前目录：$(pwd)"
    echo "项目名称：$PROJECT_NAME"
    echo "项目目录：$PROJECT_DIR"
    echo "GitHub仓库：$GITHUB_REPO"
    
    # 进入项目目录
    echo "创建项目目录：$PROJECT_DIR"
    mkdir -p "$PROJECT_DIR"
    cd "$PROJECT_DIR" || {
        echo "无法进入目录：$PROJECT_DIR"
        exit 1
    }
    
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
    echo "创建必要的目录..."
    mkdir -p logs
    mkdir -p data/mysql
    mkdir -p data/neo4j
    
    # 复制环境变量文件（如果存在）
    if [ -f .env.example ]; then
        cp .env.example .env
    fi
    
    # 进入部署目录
    cd deploy || {
        echo "无法进入部署目录"
        exit 1
    }
    
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