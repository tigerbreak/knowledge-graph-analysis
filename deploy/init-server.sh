#!/bin/bash

# 检查必要的环境变量
if [ -z "$SERVER_IP" ] || [ -z "$SERVER_USER" ] || [ -z "$SERVER_PASSWORD" ] || [ -z "$PROJECT_NAME" ]; then
    echo "错误：缺少必要的环境变量"
    exit 1
fi

# 使用 sshpass 进行密码登录
sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
    # 更新系统
    echo "更新系统..."
    yum update -y
    echo "✅ 系统更新完成"

    # 检查并安装必要的包
    echo "检查并安装必要的包..."
    for pkg in yum-utils device-mapper-persistent-data lvm2 git sshpass; do
        if ! rpm -q $pkg >/dev/null 2>&1; then
            echo "安装 $pkg..."
            yum install -y $pkg
            echo "✅ $pkg 安装完成"
        else
            echo "✅ $pkg 已安装"
        fi
    done

    # 检查并添加 Docker 仓库
    if [ ! -f "/etc/yum.repos.d/docker-ce.repo" ]; then
        echo "设置 Docker 仓库..."
        yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
        echo "✅ Docker 仓库设置完成"
    else
        echo "✅ Docker 仓库已配置"
    fi

    # 检查并安装 Docker
    if ! command -v docker >/dev/null 2>&1; then
        echo "安装 Docker..."
        yum install -y docker-ce docker-ce-cli containerd.io
        echo "✅ Docker 安装完成"
    else
        echo "✅ Docker 已安装"
    fi

    # 检查并启动 Docker 服务
    if ! systemctl is-active docker >/dev/null 2>&1; then
        echo "启动 Docker 服务..."
        systemctl start docker
        systemctl enable docker
        echo "✅ Docker 服务启动完成"
    else
        echo "✅ Docker 服务已在运行"
    fi

    # 检查并安装 Docker Compose
    if ! command -v docker-compose >/dev/null 2>&1; then
        echo "安装 Docker Compose..."
        curl -L "https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
        ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
        echo "✅ Docker Compose 安装完成"
    else
        echo "✅ Docker Compose 已安装"
    fi

    # 创建项目目录结构
    echo "创建项目目录结构..."
    mkdir -p /root/$PROJECT_NAME/docker
    echo "✅ 项目目录结构创建完成"

    # 显示安装结果
    echo "=== 安装完成 ==="
    echo "Docker 版本:"
    docker --version
    echo "Docker Compose 版本:"
    docker-compose --version
EOF

echo "✅ 服务器初始化完成！" 