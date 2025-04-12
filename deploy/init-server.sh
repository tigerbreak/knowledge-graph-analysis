#!/bin/bash

# 检查必要的环境变量
if [ -z "$SERVER_IP" ] || [ -z "$SERVER_USER" ] || [ -z "$SERVER_PASSWORD" ]; then
    echo "错误：缺少必要的环境变量"
    exit 1
fi

# 使用 sshpass 进行密码登录
sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
    # 更新系统
    echo "正在更新系统..."
    apt-get update -y
    apt-get upgrade -y

    # 检查并安装必要的包
    echo "检查并安装必要的包..."
    for pkg in apt-transport-https ca-certificates curl software-properties-common git sshpass; do
        if ! dpkg -l | grep -q "^ii  $pkg "; then
            echo "安装 $pkg..."
            apt-get install -y $pkg
        else
            echo "$pkg 已安装"
        fi
    done

    # 检查并安装 Docker
    if ! command -v docker &> /dev/null; then
        echo "安装 Docker..."
        # 添加 Docker 官方 GPG 密钥
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
        # 添加 Docker 仓库
        add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
        # 安装 Docker
        apt-get update
        apt-get install -y docker-ce docker-ce-cli containerd.io
        # 启动 Docker 服务
        systemctl start docker
        systemctl enable docker
    else
        echo "Docker 已安装"
    fi

    # 检查并安装 Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo "安装 Docker Compose..."
        # 下载 Docker Compose
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        # 添加执行权限
        chmod +x /usr/local/bin/docker-compose
        # 创建软链接
        ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    else
        echo "Docker Compose 已安装"
    fi

    # 创建项目目录
    if [ ! -d "/root/$PROJECT_NAME" ]; then
        echo "创建项目目录..."
        mkdir -p "/root/$PROJECT_NAME"
    else
        echo "项目目录已存在"
    fi

    # 显示安装的版本
    echo "Docker 版本:"
    docker --version
    echo "Docker Compose 版本:"
    docker-compose --version
EOF

echo "服务器初始化完成！" 