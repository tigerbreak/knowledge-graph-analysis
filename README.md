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