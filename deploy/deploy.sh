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
if [ -z "$SERVER_IP" ] || [ -z "$SERVER_USER" ] || [ -z "$SERVER_PASSWORD" ] || [ -z "$PROJECT_NAME" ] || [ -z "$ALIYUN_REGISTRY" ] || [ -z "$ALIYUN_NAMESPACE" ] || [ -z "$ALIYUN_REPOSITORY" ] || [ -z "$ALIYUN_USERNAME" ] || [ -z "$ALIYUN_PASSWORD" ] || [ -z "$DB_SERVER_IP" ]; then
    echo "错误：缺少必要的环境变量"
    exit 1
fi

# 替换环境变量
log "替换环境变量..."

# 打印所有环境变量
log "当前环境变量值："
log "ALIYUN_REGISTRY: ${ALIYUN_REGISTRY}"
log "ALIYUN_NAMESPACE: ${ALIYUN_NAMESPACE}"
log "ALIYUN_REPOSITORY: ${ALIYUN_REPOSITORY}"
log "DB_SERVER_IP: ${DB_SERVER_IP}"
log "NEO4J_USER: ${NEO4J_USER:-neo4j}"
log "NEO4J_PASSWORD: ${NEO4J_PASSWORD:-root123321}"
log "MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD:-123456}"
log "MYSQL_DATABASE: ${MYSQL_DATABASE:-knowledge_graph}"
log "MYSQL_USER: ${MYSQL_USER:-root}"
log "MYSQL_PASSWORD: ${MYSQL_PASSWORD:-123456}"
log "MYSQL_PORT: ${MYSQL_PORT:-3307}"

cd "$PROJECT_DIR/docker" || exit 1
log "当前目录: $(pwd)"

# 检查文件是否存在
if [ ! -f "docker-compose.yml" ]; then
    log "错误: docker-compose.yml 文件不存在"
    exit 1
fi

# 备份原文件
cp docker-compose.yml docker-compose.yml.bak
log "已备份原配置文件"

# 替换环境变量并检查结果
log "开始替换环境变量..."
sed -i "s|\${ALIYUN_REGISTRY}|${ALIYUN_REGISTRY}|g" docker-compose.yml && log "替换 ALIYUN_REGISTRY 成功" || log "替换 ALIYUN_REGISTRY 失败"
sed -i "s|\${ALIYUN_NAMESPACE}|${ALIYUN_NAMESPACE}|g" docker-compose.yml && log "替换 ALIYUN_NAMESPACE 成功" || log "替换 ALIYUN_NAMESPACE 失败"
sed -i "s|\${ALIYUN_REPOSITORY}|${ALIYUN_REPOSITORY}|g" docker-compose.yml && log "替换 ALIYUN_REPOSITORY 成功" || log "替换 ALIYUN_REPOSITORY 失败"
sed -i "s|\${DB_SERVER_IP}|${DB_SERVER_IP}|g" docker-compose.yml && log "替换 DB_SERVER_IP 成功" || log "替换 DB_SERVER_IP 失败"
sed -i "s|\${NEO4J_USER:-neo4j}|${NEO4J_USER:-neo4j}|g" docker-compose.yml && log "替换 NEO4J_USER 成功" || log "替换 NEO4J_USER 失败"
sed -i "s|\${NEO4J_PASSWORD:-root123321}|${NEO4J_PASSWORD:-root123321}|g" docker-compose.yml && log "替换 NEO4J_PASSWORD 成功" || log "替换 NEO4J_PASSWORD 失败"
sed -i "s|\${MYSQL_ROOT_PASSWORD:-123456}|${MYSQL_ROOT_PASSWORD:-123456}|g" docker-compose.yml && log "替换 MYSQL_ROOT_PASSWORD 成功" || log "替换 MYSQL_ROOT_PASSWORD 失败"
sed -i "s|\${MYSQL_DATABASE:-knowledge_graph}|${MYSQL_DATABASE:-knowledge_graph}|g" docker-compose.yml && log "替换 MYSQL_DATABASE 成功" || log "替换 MYSQL_DATABASE 失败"
sed -i "s|\${MYSQL_USER:-root}|${MYSQL_USER:-root}|g" docker-compose.yml && log "替换 MYSQL_USER 成功" || log "替换 MYSQL_USER 失败"
sed -i "s|\${MYSQL_PASSWORD:-123456}|${MYSQL_PASSWORD:-123456}|g" docker-compose.yml && log "替换 MYSQL_PASSWORD 成功" || log "替换 MYSQL_PASSWORD 失败"
sed -i "s|\${MYSQL_PORT:-3307}|${MYSQL_PORT:-3307}|g" docker-compose.yml && log "替换 MYSQL_PORT 成功" || log "替换 MYSQL_PORT 失败"

# 验证替换结果
log "验证环境变量替换结果..."
if grep -q "\${" docker-compose.yml; then
    log "警告: 文件中仍存在未替换的变量"
    grep -n "\${" docker-compose.yml
else
    log "✅ 所有环境变量替换完成"
fi

# 显示替换后的文件内容
log "替换后的文件内容:"
cat docker-compose.yml

# 定义远程服务器信息
REMOTE_HOST="$SERVER_IP"
REMOTE_USER="$SERVER_USER"
REMOTE_PASS="$SERVER_PASSWORD"
PROJECT_DIR="/root/$PROJECT_NAME"

# 设置变量
DOCKER_IMAGE="$ALIYUN_REGISTRY/$ALIYUN_NAMESPACE/$ALIYUN_REPOSITORY"

# 输出环境变量信息（不包含密码）
log "部署配置信息："
log "远程主机：$REMOTE_HOST"
log "远程用户：$REMOTE_USER"
log "项目名称：$PROJECT_NAME"
log "项目目录：$PROJECT_DIR"
log "Docker镜像：$DOCKER_IMAGE"
log "数据库服务器IP：$DB_SERVER_IP"

# 获取系统信息
log "系统信息："
log "主机名：$(hostname)"
log "操作系统：$(uname -a)"
log "Docker版本：$(docker --version)"
log "Docker Compose版本：$(docker-compose --version)"
log "当前目录：$(pwd)"
log "当前用户：$(whoami)"
log "当前时间：$(date)"

# 部署函数
deploy() {
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << EOF
        # 设置环境变量
        export ALIYUN_REGISTRY='registry.cn-hongkong.aliyuncs.com'
        export ALIYUN_NAMESPACE='tongihttigerbreak'
        export ALIYUN_REPOSITORY='tigerhouse'
        export PROJECT_NAME='myproject'
        export PROJECT_DIR="/root/\$PROJECT_NAME"
        export DOCKER_IMAGE="\$ALIYUN_REGISTRY/\$ALIYUN_NAMESPACE/\$ALIYUN_REPOSITORY"
        
        # 设置数据库相关环境变量
        export DB_SERVER_IP='${DB_SERVER_IP}'
        export NEO4J_USER='${NEO4J_USER:-neo4j}'
        export NEO4J_PASSWORD='${NEO4J_PASSWORD:-root123321}'
        export MYSQL_ROOT_PASSWORD='${MYSQL_ROOT_PASSWORD:-123456}'
        export MYSQL_DATABASE='${MYSQL_DATABASE:-knowledge_graph}'
        export MYSQL_USER='${MYSQL_USER:-root}'
        export MYSQL_PASSWORD='${MYSQL_PASSWORD:-123456}'

        # 设置显示时间的函数
        log() {
            echo "[$(date +'%Y-%m-%d %H:%M:%S')] \$1"
        }

        # 检查基础镜像函数
        check_and_pull_image() {
            local IMAGE_NAME=$1
            local IMAGE_TAG=$2
            local FULL_IMAGE="${IMAGE_NAME}:${IMAGE_TAG}"
            
            log "检查 ${FULL_IMAGE} 镜像..."
            if docker images ${FULL_IMAGE} --quiet | grep -q .; then
                log "${FULL_IMAGE} 镜像已存在，检查是否需要更新..."
                # 获取本地镜像 ID
                LOCAL_IMAGE_ID=$(docker images ${FULL_IMAGE} --quiet)
                
                # 获取远程镜像信息
                REMOTE_DIGEST=$(docker manifest inspect ${FULL_IMAGE} | grep -i sha256 | head -1)
                
                # 获取本地镜像 digest
                LOCAL_DIGEST=$(docker image inspect ${FULL_IMAGE} | grep -i sha256 | head -1)
                
                if [ "$LOCAL_DIGEST" = "$REMOTE_DIGEST" ]; then
                    log "${FULL_IMAGE} 本地镜像已是最新版本，跳过拉取"
                else
                    log "${FULL_IMAGE} 发现新版本，开始拉取..."
                    docker pull ${FULL_IMAGE} 2>&1 | while read line; do echo "[$(date +'%Y-%m-%d %H:%M:%S')] [$FULL_IMAGE] $line"; done
                fi
            else
                log "本地不存在 ${FULL_IMAGE} 镜像，开始拉取..."
                docker pull ${FULL_IMAGE} 2>&1 | while read line; do echo "[$(date +'%Y-%m-%d %H:%M:%S')] [$FULL_IMAGE] $line"; done
            fi
        }

        # 显示系统信息
        log "系统信息："
        df -h | grep /dev/vda1
        log "Docker 信息："
        docker system df -v
        echo "✅ 系统信息检查完成"

        # 登录到阿里云容器镜像服务
        log "登录到阿里云容器镜像服务..."
        echo "$ALIYUN_PASSWORD" | docker login --username="$ALIYUN_USERNAME" --password-stdin $ALIYUN_REGISTRY
        echo "✅ 阿里云容器镜像服务登录完成"

        # 显示拉取前的镜像列表
        log "拉取前的镜像列表："
        docker images | grep "$DOCKER_IMAGE" || true

        # 打印完整的镜像引用
        log "DOCKER_IMAGE 值: $DOCKER_IMAGE"
        log "后端镜像完整引用: ${DOCKER_IMAGE}:backend-latest"
        log "前端镜像完整引用: ${DOCKER_IMAGE}:frontend-latest"

        # 拉取最新镜像并显示进度
        log "=== 开始拉取后端镜像 ==="
        docker pull "${DOCKER_IMAGE}:backend-latest" 2>&1 | while read line; do echo "[$(date +'%Y-%m-%d %H:%M:%S')] [后端] $line"; done
        echo "✅ 后端镜像拉取完成"
        
        log "=== 开始拉取前端镜像 ==="
        docker pull "${DOCKER_IMAGE}:frontend-latest" 2>&1 | while read line; do echo "[$(date +'%Y-%m-%d %H:%M:%S')] [前端] $line"; done
        echo "✅ 前端镜像拉取完成"

        # 显示拉取后的镜像信息
        log "拉取后的镜像列表："
        docker images | grep "$DOCKER_IMAGE"

        # 显示镜像大小变化
        log "镜像存储信息："
        docker system df -v | grep -A 10 "Images space usage:"

        # 进入项目目录
        cd "$PROJECT_DIR" || exit 1
        log "当前工作目录: $(pwd)"
        log "项目目录内容:"
        ls -la
        
        # 检查 docker 目录是否存在
        if [ ! -d "docker" ]; then
            log "错误: docker 目录不存在"
            log "当前目录内容:"
            ls -la
            exit 1
        fi

        # 进入项目目录下的 docker 目录
        cd "$PROJECT_DIR/docker" || exit 1
        log "当前工作目录: $(pwd)"
        log "docker 目录内容:"
        ls -la
        
        # 检查 docker-compose.yml 是否存在
        if [ ! -f "docker-compose.yml" ]; then
            log "错误: docker-compose.yml 文件不存在"
            log "当前目录内容:"
            ls -la
            exit 1
        fi

        # 停止并删除旧容器
        log "停止并删除旧容器..."
        docker-compose ps
        docker-compose down
        echo "✅ 旧容器清理完成"

        # 启动新容器
        log "启动新容器..."
        docker-compose up -d
        echo "✅ 新容器启动完成"

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
            docker images | grep "$DOCKER_IMAGE" | grep -v "latest" || true
            
            # 获取所有镜像标签
            ALL_TAGS=$(docker images | grep "$DOCKER_IMAGE" | awk '{print \$2}' | grep -v "latest")
            
            # 只保留当前和上一个版本
            if [ -n "$ALL_TAGS" ]; then
                log "开始清理旧镜像..."
                for tag in $ALL_TAGS; do
                    log "删除镜像标签: $tag"
                    docker rmi "$DOCKER_IMAGE:$tag" || true
                done
            fi
            
            log "✅ 旧镜像清理完成"

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
        log "✅ 部署成功！"
        exit 0
    else
        if [ $attempt -lt $MAX_RETRIES ]; then
            log "部署失败，${RETRY_INTERVAL}秒后重试..."
            sleep $RETRY_INTERVAL
        else
            log "❌ 已达到最大重试次数($MAX_RETRIES)，部署失败"
            exit 1
        fi
    fi
    attempt=$((attempt + 1))
done 