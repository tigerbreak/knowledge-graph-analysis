# 使用官方 Python 镜像
FROM python:3.9

# 设置工作目录
WORKDIR /myproject

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update \
    && apt-get install -y \
        gcc \
        g++ \
        make \
        libpq-dev \
        default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# 配置pip镜像源
#RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 升级pip
RUN pip install --upgrade pip

# 复制整个项目
COPY . /myproject/

# 安装依赖
RUN pip install -r requirements.txt

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"] 