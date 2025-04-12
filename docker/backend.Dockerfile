# 使用官方 Python 镜像
FROM python:3.9

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 设置 pip 镜像源
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 升级 pip
RUN pip install --upgrade pip

# 复制项目文件
COPY requirements.txt .
COPY backend/ ./backend/

# 复制本地依赖包
COPY packages/ ./packages/

# 安装依赖
RUN if [ -d "packages" ]; then \
        pip install --no-index --find-links=./packages -r requirements.txt; \
    else \
        pip install -r requirements.txt; \
    fi

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "backend/manage.py", "runserver", "0.0.0.0:8000"] 