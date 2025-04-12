#!/bin/bash

# 检查必要的环境变量
if [ -z "$SERVER_IP" ] || [ -z "$SERVER_USER" ] || [ -z "$SERVER_PASSWORD" ]; then
    echo "错误：缺少必要的环境变量"
    exit 1
fi

# 定义远程服务器信息
REMOTE_HOST="$SERVER_IP"
REMOTE_USER="$SERVER_USER"
REMOTE_PASS="$SERVER_PASSWORD"

# 使用 sshpass 进行密码登录
SSHPASS="sshpass -p $REMOTE_PASS"

# 在远程服务器上执行初始化命令
echo "正在初始化服务器..."
$SSHPASS ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST << EOF
    # 更新系统
    yum update -y
    
    # 安装必要的软件包
    yum install -y yum-utils device-mapper-persistent-data lvm2
    
    # 添加 Docker 仓库
    yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    
    # 安装 Docker
    yum install -y docker-ce docker-ce-cli containerd.io
    
    # 启动 Docker 服务
    systemctl start docker
    systemctl enable docker
    
    # 安装 Docker Compose
    curl -L "https://github.com/docker/compose/releases/download/v2.20.3/docker-compose-\$(uname -s)-\$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # 安装 git
    yum install -y git
    
    # 安装 sshpass（用于自动化部署）
    yum install -y epel-release
    yum install -y sshpass
    
    # 创建项目目录
    mkdir -p /root/myproject
    
    # 显示安装结果
    echo "Docker 版本:"
    docker --version
    echo "Docker Compose 版本:"
    docker-compose --version
EOF

echo "服务器初始化完成！" 