#!/bin/bash

# 设置错误时退出
set -e

# 日志函数
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# 检查 Docker 是否安装
check_docker() {
    log "=== 检查 Docker 是否安装 ==="
    if ! command -v docker &> /dev/null; then
        log "错误: Docker 未安装"
        exit 1
    fi
    log "Docker 已安装"
}

# 检查 Docker Compose 是否安装
check_docker_compose() {
    log "=== 检查 Docker Compose 是否安装 ==="
    if ! command -v docker-compose &> /dev/null; then
        log "错误: Docker Compose 未安装"
        exit 1
    fi
    log "Docker Compose 已安装"
}

# 检查必要的目录
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
            mkdir -p "$dir"
            chmod 777 "$dir"
        fi
    done
}

# 检查基础镜像
check_and_pull_image() {
    local image=$1
    log "=== 检查镜像 $image ==="
    
    # 检查镜像是否存在
    if ! docker images -q "$image" &> /dev/null; then
        log "镜像 $image 不存在，开始拉取..."
        docker pull "$image"
        log "镜像 $image 拉取完成"
    else
        log "镜像 $image 已存在"
    fi
}

# 停止并删除旧容器
cleanup_old_containers() {
    log "=== 清理旧容器 ==="
    docker-compose -f ~/docker-compose.db.yml down || true
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
}

# 主函数
main() {
    log "=== 开始部署数据库服务 ==="
    
    # 检查系统环境
    check_docker
    check_docker_compose
    check_directories
    
    # 检查基础镜像
    check_and_pull_image "mysql:8.0"
    check_and_pull_image "neo4j:4.4"
    
    # 清理旧容器
    cleanup_old_containers
    
    # 启动服务
    start_services
    
    log "=== 数据库服务部署完成 ==="
}

# 执行主函数
main 