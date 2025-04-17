# 知识图谱分析系统

一个基于深度学习的文学作品知识图谱分析系统，能够自动分析文本内容，提取人物、势力、事件等信息，并以知识图谱的形式可视化展示。

## 功能特点

- **文本分析**
  - 支持 TXT、PDF、DOCX 格式文件上传
  - 支持文本直接粘贴分析
  - 自动识别文章所属作品和标题
  - 智能提取人物、势力、事件等信息

- **知识图谱**
  - 可视化展示人物关系网络
  - 支持多作品管理
  - 展示势力分布
  - 事件时间线展示

- **数据分析**
  - 人物关系分析
  - 势力分布分析
  - 事件分析
  - 数据导出功能

## 技术栈

### 后端
- Python 3.8+
- Django 4.2
- Django REST framework
- Neo4j 图数据库
- MySQL 数据库
- DeepSeek API 集成

### 前端
- Vue.js 3
- Element Plus UI
- ECharts 图表库
- Vite 构建工具

### 部署
- Docker
- Docker Compose
- Kubernetes
- Nginx

## 系统要求

- Python 3.8+
- Node.js 16+
- Docker 20.10+
- Docker Compose 2.0+
- Neo4j 4.4+
- MySQL 8.0+

## 安装说明

### 使用 Docker Compose 部署

1. 克隆项目
```bash
git clone https://github.com/tigerbreak/knowledge-graph-analysis.git
cd knowledge-graph-analysis
```

2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，设置必要的环境变量
```

3. 启动服务
```bash
docker-compose up -d
```

### 使用 Kubernetes 部署

1. 构建镜像
```bash
docker build -t your-registry/knowledge-graph-analysis:latest -f backend.Dockerfile .
docker build -t your-registry/knowledge-graph-analysis-frontend:latest -f frontend.Dockerfile .
```

2. 推送镜像
```bash
docker push your-registry/knowledge-graph-analysis:latest
docker push your-registry/knowledge-graph-analysis-frontend:latest
```

3. 部署到 Kubernetes
```bash
kubectl apply -f k8s/
```

## 使用方法

1. 访问系统
   - 打开浏览器访问 `http://localhost:30080`
   - 默认端口可在 docker-compose.yml 中修改

2. 上传分析
   - 点击"新建分析"按钮
   - 选择上传文件或粘贴文本
   - 点击"开始分析"

3. 查看结果
   - 在左侧面板选择要查看的作品
   - 切换表格/图谱视图
   - 点击节点查看详细信息

4. 数据管理
   - 在左侧面板可以删除不需要的分析
   - 使用图谱视图可以直观地查看关系

## 项目结构

```
knowledge-graph-analysis/
├── backend/                 # 后端服务
├── frontend/               # 前端服务
├── knowledge_graph/        # Django 应用
├── k8s/                    # Kubernetes 配置
├── src/                    # 前端源代码
├── docker-compose.yml      # Docker Compose 配置
├── backend.Dockerfile      # 后端 Dockerfile
└── frontend.Dockerfile     # 前端 Dockerfile
```

## 开发说明

### 后端开发
1. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 运行开发服务器
```bash
python manage.py runserver
```

### 前端开发
1. 安装依赖
```bash
cd frontend
npm install
```

2. 运行开发服务器
```bash
npm run dev
```

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 联系方式

- 项目维护者：[您的名字]
- 邮箱：[您的邮箱]
- 项目链接：[https://github.com/tigerbreak/knowledge-graph-analysis](https://github.com/tigerbreak/knowledge-graph-analysis)

## 部署说明

### 一、数据库部署（一次性）

#### 1. 数据库服务器要求
- 操作系统：CentOS 7+
- 内存：至少 1GB
- 磁盘：至少 10GB 可用空间
- Docker 版本：20.10+
- Docker Compose 版本：2.0+

#### 2. 数据库环境变量
在数据库服务器的 GitHub Secrets 中配置：
```bash
# 服务器配置
DB_SERVER_IP=        # 数据库服务器IP
DB_SERVER_USER=      # 服务器用户名
DB_SERVER_PASSWORD=  # 服务器密码

# Neo4j配置
NEO4J_USER=          # Neo4j用户名，默认为 neo4j
NEO4J_PASSWORD=      # Neo4j密码，默认为 root123321

# MySQL配置
MYSQL_ROOT_PASSWORD= # MySQL root密码，默认为 123456
MYSQL_DATABASE=      # MySQL数据库名，默认为 knowledge_graph
MYSQL_USER=          # MySQL用户名，默认为 root
MYSQL_PASSWORD=      # MySQL密码，默认为 123456
MYSQL_PORT=          # MySQL端口，默认为 3307
```

#### 3. 数据库部署流程

1. **准备工作**
   - 安装 Docker 和 Docker Compose
   - 开放必要端口（MySQL: 3307, Neo4j: 7474, 7687）
   - 创建数据目录：
     ```bash
     mkdir -p /data/mysql
     mkdir -p /data/neo4j
     ```

2. **自动部署触发**
   - 推送到 `release/v1.0.3` 分支时自动触发
   - 当以下文件发生变化时触发：
     - `docker/docker-compose.db.yml`
     - `deploy/deploy-db.sh`
   - 或手动在 GitHub Actions 中触发

3. **部署步骤**
   - 自动连接到数据库服务器
   - 复制部署文件到服务器
   - 执行部署脚本
   - 验证服务状态

4. **验证部署**
   - 检查 MySQL：
     ```bash
     docker exec -it mysql mysql -uroot -p
     ```
   - 检查 Neo4j：
     ```bash
     curl http://localhost:7474
     ```
   - 检查容器状态：
     ```bash
     docker ps
     ```

5. **部署后配置**
   - 设置数据库备份策略
   - 配置监控告警
   - 设置资源限制
   - 配置安全策略

### 二、前后端部署（持续迭代）

#### 1. 应用服务器要求
- 操作系统：CentOS 7+
- 内存：至少 1GB
- 磁盘：至少 5GB 可用空间
- Docker 版本：20.10+
- Docker Compose 版本：2.0+

#### 2. 应用环境变量
在应用服务器的 GitHub Secrets 中配置：
```bash
# 服务器配置
SERVER_IP=           # 部署服务器IP
SERVER_USER=         # 服务器用户名
SERVER_PASSWORD=     # 服务器密码

# 项目配置
PROJECT_NAME=        # 项目名称，默认为 myproject

# 阿里云容器镜像服务配置
ALIYUN_REGISTRY=     # 镜像仓库地址，默认为 registry.cn-hongkong.aliyuncs.com
ALIYUN_NAMESPACE=    # 命名空间，默认为 tongihttigerbreak
ALIYUN_REPOSITORY=   # 仓库名称，默认为 tigerhouse
ALIYUN_USERNAME=     # 阿里云账号
ALIYUN_PASSWORD=     # 阿里云密码

# 数据库连接配置
DB_SERVER_IP=        # 数据库服务器IP
```

#### 3. 自动部署配置

1. **触发条件**
   - 推送到 `release/v1.0.3` 分支时自动触发
   - 手动在 GitHub Actions 中触发
   - 仅当以下文件发生变化时触发：
     - `docker/docker-compose.yml`
     - `deploy/deploy.sh`
     - `frontend/` 目录下的文件
     - `backend/` 目录下的文件

2. **部署流程**
   - 自动连接到部署服务器
   - 替换环境变量
   - 拉取最新镜像
   - 停止并删除旧容器
   - 启动新容器
   - 清理旧镜像

3. **验证部署**
   - 检查容器状态：`docker-compose ps`
   - 检查服务日志：`docker-compose logs`
   - 访问前端页面：`http://服务器IP`
   - 访问后端API：`http://服务器IP:8000`

### 三、注意事项

1. **数据库维护**
   - 定期备份数据
   - 监控数据库性能
   - 及时更新数据库版本
   - 设置合适的资源限制

2. **应用维护**
   - 定期更新应用版本
   - 监控应用性能
   - 设置日志轮转
   - 配置监控告警

3. **安全建议**
   - 使用强密码
   - 限制服务器访问IP
   - 启用防火墙
   - 定期更新系统和依赖
   - 配置 SSL 证书

4. **故障处理**
   - 保存部署日志
   - 建立回滚机制
   - 准备应急方案
   - 定期进行故障演练

## 开发环境配置

// ... existing code ... 