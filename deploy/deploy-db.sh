#!/bin/bash

# 设置错误时退出
set -e

# 日志函数
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# 检查并安装 Docker
install_docker() {
    log "=== 检查并安装 Docker ==="
    if ! command -v docker &> /dev/null; then
        log "Docker 未安装，开始安装..."
        # 安装依赖
        sudo apt-get update
        sudo apt-get install -y \
            apt-transport-https \
            ca-certificates \
            curl \
            gnupg \
            lsb-release

        # 添加 Docker 官方 GPG 密钥
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

        # 设置稳定版仓库
        echo \
            "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
            $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

        # 安装 Docker
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io

        # 启动 Docker
        sudo systemctl start docker
        sudo systemctl enable docker

        # 添加当前用户到 docker 组
        sudo usermod -aG docker $USER
        log "Docker 安装完成"
    else
        log "Docker 已安装"
    fi
}

# 检查并安装 Docker Compose
install_docker_compose() {
    log "=== 检查并安装 Docker Compose ==="
    if ! command -v docker-compose &> /dev/null; then
        log "Docker Compose 未安装，开始安装..."
        # 下载最新版本的 Docker Compose
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        
        # 添加执行权限
        sudo chmod +x /usr/local/bin/docker-compose
        log "Docker Compose 安装完成"
    else
        log "Docker Compose 已安装"
    fi
}

# 检查并创建必要的目录
check_directories() {
    log "=== 检查必要的目录 ==="
    local dirs=(
        "/data/mysql"
        "/data/neo4j/data"
        "/data/neo4j/logs"
    )
    
    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            log "创建目录: $dir"
            sudo mkdir -p "$dir"
            sudo chmod 777 "$dir"
        fi
    done
    log "目录检查完成"
}

# 检查并拉取基础镜像
check_and_pull_images() {
    log "=== 检查并拉取基础镜像 ==="
    local images=(
        "mysql:8.0"
        "neo4j:4.4"
    )
    
    for image in "${images[@]}"; do
        if ! docker images -q "$image" &> /dev/null; then
            log "拉取镜像: $image"
            docker pull "$image"
        else
            log "镜像已存在: $image"
        fi
    done
    log "镜像检查完成"
}

# 停止并删除旧容器
cleanup_old_containers() {
    log "=== 清理旧容器 ==="
    docker-compose -f ~/docker-compose.db.yml down || true
    log "清理完成"
}

# 启动服务
start_services() {
    log "=== 启动数据库服务 ==="
    docker-compose -f ~/docker-compose.db.yml up -d
    
    # 等待服务启动
    log "等待服务启动..."
    sleep 30
    
    # 检查服务状态
    log "检查服务状态..."
    docker-compose -f ~/docker-compose.db.yml ps
    log "服务启动完成"
}

# 主函数
main() {
    log "=== 开始部署数据库服务 ==="
    
    # 检查并安装必要的软件
    install_docker
    install_docker_compose
    
    # 检查环境
    check_directories
    check_and_pull_images
    
    # 清理旧容器
    cleanup_old_containers
    
    # 启动服务
    start_services
    
    log "=== 数据库服务部署完成 ==="
}

# 执行主函数
main 