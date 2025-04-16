#!/bin/bash

# 设置错误时退出
set -e

# 环境变量设置
MYSQL_DATABASE=${MYSQL_DATABASE:-knowledge_graph}
MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD:-123456}
NEO4J_PASSWORD=${NEO4J_PASSWORD:-root123321}
NEO4J_AUTH="neo4j/${NEO4J_PASSWORD}"

# 输出环境变量配置
echo "=== 环境变量配置 ==="
echo "MYSQL_DATABASE: $MYSQL_DATABASE"
echo "MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD:0:2}******"
echo "NEO4J_PASSWORD: ${NEO4J_PASSWORD:0:2}******"
echo "NEO4J_AUTH: $NEO4J_AUTH"
echo "==================="
echo

# 日志函数
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# 检查并安装 Docker
install_docker() {
    log "=== 检查并安装 Docker ==="
    if ! command -v docker &> /dev/null; then
        log "Docker 未安装，开始安装..."
        
        # 卸载旧版本
        sudo yum remove -y docker \
            docker-client \
            docker-client-latest \
            docker-common \
            docker-latest \
            docker-latest-logrotate \
            docker-logrotate \
            docker-engine

        # 安装依赖
        sudo yum install -y yum-utils

        # 设置仓库
        sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

        # 安装 Docker
        sudo yum install -y docker-ce docker-ce-cli containerd.io

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
        # 检查镜像是否存在
        if ! docker images -q "$image" &> /dev/null; then
            log "拉取镜像: $image"
            if ! docker pull "$image"; then
                log "错误: 拉取镜像 $image 失败"
                exit 1
            fi
        else
            log "镜像已存在: $image"
        fi
    done
    log "镜像检查完成"
}

# 处理配置文件
process_config_file() {
    log "=== 处理配置文件 ==="
    
    # 检查源文件是否存在
    if [ ! -f "/root/docker-compose.db.yml" ]; then
        log "错误: /root/docker-compose.db.yml 文件不存在"
        exit 1
    fi
    
    # 使用 sudo 创建文件并设置权限
    sudo sed -e "s/\${MYSQL_DATABASE}/${MYSQL_DATABASE}/g" \
        -e "s/\${MYSQL_ROOT_PASSWORD}/${MYSQL_ROOT_PASSWORD}/g" \
        -e "s/\${NEO4J_PASSWORD}/${NEO4J_PASSWORD}/g" \
        -e "s/\${NEO4J_AUTH}/${NEO4J_AUTH}/g" \
        "/root/docker-compose.db.yml" > /root/docker-compose.db.yml
    
    # 设置文件权限
    sudo chmod 644 /root/docker-compose.db.yml
    
    # 检查文件是否成功创建
    if [ ! -f /root/docker-compose.db.yml ]; then
        log "错误: 创建配置文件失败"
        exit 1
    fi
    
    log "配置文件处理完成"
}

# 停止并删除旧容器
cleanup_old_containers() {
    log "=== 清理旧容器 ==="
    docker-compose -f /root/docker-compose.db.yml down || true
    log "清理完成"
}

# 启动服务
start_services() {
    log "=== 启动数据库服务 ==="
    # 使用环境变量启动服务
    MYSQL_DATABASE="$MYSQL_DATABASE" \
    MYSQL_ROOT_PASSWORD="$MYSQL_ROOT_PASSWORD" \
    NEO4J_PASSWORD="$NEO4J_PASSWORD" \
    NEO4J_AUTH="$NEO4J_AUTH" \
    docker-compose -f /root/docker-compose.db.yml up -d
    
    # 等待服务启动
    log "等待服务启动..."
    sleep 30
    
    # 检查服务状态
    log "检查服务状态..."
    docker-compose -f /root/docker-compose.db.yml ps
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
    
    # 处理配置文件
    process_config_file
    
    # 清理旧容器
    cleanup_old_containers
    
    # 启动服务
    start_services
    
    log "=== 数据库服务部署完成 ==="
}

# 执行主函数
main 