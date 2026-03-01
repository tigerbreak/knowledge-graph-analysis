# 快速参考指南

## 📚 目录结构

```
backend/knowledge_graph/
├── views/                      # 视图模块
│   ├── article_views.py        # 文章相关
│   ├── character_views.py      # 人物相关
│   ├── work_views.py           # 作品相关
│   ├── event_views.py          # 事件相关
│   └── admin_views.py          # 管理相关
├── services/                   # 服务层
│   ├── ai_service.py           # AI 分析服务
│   └── neo4j_service.py        # Neo4j 服务
├── exceptions.py               # 异常定义
├── utils.py                    # 工具函数
└── models.py                   # 数据模型
```

## 🔧 常用导入

### 视图导入
```python
from knowledge_graph.views.article_views import upload_file, article_list
from knowledge_graph.views.character_views import character_details
from knowledge_graph.views.work_views import work_list, get_work_graph
from knowledge_graph.views.event_views import get_events
from knowledge_graph.views.admin_views import clean_graph_data
```

### 服务导入
```python
from knowledge_graph.services.ai_service import ai_service
from knowledge_graph.services.neo4j_service import neo4j_service
```

### 工具导入
```python
from knowledge_graph.utils import json_response, error_response
from knowledge_graph.exceptions import AIAnalysisError, NotFoundError
```

## 📡 API 端点

### 文章管理
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/upload/` | 上传文件并分析 |
| GET | `/articles/` | 获取文章列表 |
| GET | `/articles/<id>/` | 获取文章详情 |
| GET | `/articles/<id>/analysis/` | 获取分析结果 |
| GET | `/analysis-history/` | 获取分析历史 |

### 人物管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/characters/` | 获取人物列表 |
| GET | `/characters/details/` | 获取人物详情 |
| GET | `/characters/<name>/relationships/` | 获取人物关系 |

### 作品管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/works/` | 获取作品列表 |
| GET | `/works/<id>/graph/` | 获取作品图谱 |
| POST | `/works/sync/` | 同步作品数据 |
| GET | `/works/check-data/` | 检查作品数据 |

### 图谱数据
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/graph/` | 获取图谱数据 |
| GET | `/graph/<work_id>/` | 按作品获取图谱 |
| GET | `/graph/node/<node_id>/` | 获取节点详情 |

### 事件管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/events/` | 获取事件列表 |
| GET | `/events/<id>/` | 获取事件详情 |
| GET | `/works/<id>/events/` | 按作品获取事件 |

### 管理功能
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/admin/clean-graph/` | 清理图谱数据 |
| POST | `/admin/delete-article/<id>/` | 删除文章 |
| GET | `/admin/debug-database/` | 调试数据库 |

## 💡 使用示例

### 1. 上传文件并分析

```python
# 前端调用示例
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('/upload/', {
    method: 'POST',
    body: formData
})
.then(res => res.json())
.then(data => {
    console.log('分析结果:', data);
});
```

### 2. 使用 AI 服务

```python
# 后端服务调用
from knowledge_graph.services.ai_service import ai_service

content = "文章内容..."
try:
    result = ai_service.analyze_article(content)
    print(f"识别到 {len(result['characters'])} 个人物")
    print(f"识别到 {len(result['forces'])} 个势力")
except AIAnalysisError as e:
    print(f"分析失败：{e}")
```

### 3. 获取作品图谱

```python
# 获取指定作品的图谱数据
import requests

response = requests.get('/works/1/graph/')
data = response.json()

if data['code'] == 0:
    nodes = data['data']['nodes']
    links = data['data']['links']
    print(f"图谱包含 {len(nodes)} 个节点，{len(links)} 条边")
```

### 4. 统一响应格式

```python
from knowledge_graph.utils import json_response, error_response

# 成功响应
return json_response(
    data={'id': 1, 'name': 'test'},
    message='操作成功',
    code=0
)

# 错误响应
return error_response(
    message='参数错误',
    code=1,
    status=400
)
```

### 5. 异常处理

```python
from knowledge_graph.exceptions import NotFoundError, AIAnalysisError

def process_article(article_id):
    try:
        article = Article.objects.get(id=article_id)
        result = ai_service.analyze_article(article.content)
        return json_response(result)
    except Article.DoesNotExist:
        raise NotFoundError("文章不存在")
    except AIAnalysisError as e:
        return error_response(str(e))
```

## 🎯 常见场景

### 场景 1: 创建新视图

```python
# backend/knowledge_graph/views/custom_views.py
from rest_framework.decorators import api_view
from knowledge_graph.utils import json_response
from knowledge_graph.exceptions import NotFoundError

@api_view(['GET'])
def custom_view(request):
    """自定义视图示例"""
    try:
        # 业务逻辑
        data = {'message': 'Hello World'}
        return json_response(data)
    except Exception as e:
        return error_response(str(e))
```

### 场景 2: 使用服务层

```python
from knowledge_graph.services.ai_service import ai_service
from knowledge_graph.services.neo4j_service import neo4j_service

def analyze_and_store(content):
    # 使用 AI 服务分析
    result = ai_service.analyze_article(content)
    
    # 存储到 Neo4j
    neo4j_service.import_analysis_result(result)
    
    return result
```

### 场景 3: 批量处理

```python
from knowledge_graph.utils import batch_process

def process_batch(items):
    def processor(batch):
        return [item.upper() for item in batch]
    
    results = batch_process(
        items,
        processor,
        batch_size=100
    )
    return results
```

## 🔍 调试技巧

### 1. 查看日志

```python
import logging
logger = logging.getLogger(__name__)

def my_view(request):
    logger.info("开始处理请求")
    logger.debug(f"请求参数：{request.GET}")
    try:
        # 业务逻辑
        pass
    except Exception as e:
        logger.error(f"处理失败：{e}", exc_info=True)
        raise
```

### 2. 数据库调试

```bash
# 查看数据库状态
GET /admin/debug-database/

# 检查关系数据
GET /admin/check-relationships/

# 检查作品数据
GET /works/check-data/
```

### 3. Neo4j 查询

```python
from knowledge_graph.services.neo4j_service import neo4j_service

# 执行自定义查询
result = neo4j_service.run_query("""
    MATCH (n:Character)
    RETURN n.name, n.description
    LIMIT 10
""")
```

## ⚡ 性能优化

### 1. 数据库查询优化

```python
# 使用 select_related 减少查询
articles = Article.objects.select_related('work').all()

# 使用 prefetch_related 优化多对多查询
works = Work.objects.prefetch_related('articles', 'characters').all()
```

### 2. 批量操作

```python
# 批量创建
Article.objects.bulk_create([
    Article(title=f'Article {i}', work=work)
    for i in range(100)
])

# 批量更新
Article.objects.filter(work=work).update(updated_at=timezone.now())
```

### 3. 缓存使用

```python
from django.core.cache import cache

def get_work_graph(work_id):
    cache_key = f'work_graph_{work_id}'
    data = cache.get(cache_key)
    
    if not data:
        data = neo4j_service.get_graph_data(work_id)
        cache.set(cache_key, data, timeout=300)
    
    return data
```

## 🛡️ 错误处理

### 常见错误码

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 1 | 通用错误 |
| 404 | 资源未找到 |
| 1001 | Neo4j 错误 |
| 2001 | AI 分析错误 |
| 3001 | 数据验证错误 |
| 4001 | 文件上传错误 |

### 错误处理最佳实践

```python
from knowledge_graph.exceptions import KnowledgeGraphError

@api_view(['POST'])
def upload_file(request):
    try:
        # 1. 参数验证
        if 'file' not in request.FILES:
            return error_response('请上传文件', code=3001)
        
        # 2. 业务处理
        result = process_file(request.FILES['file'])
        
        # 3. 返回成功
        return json_response(result)
        
    except ValidationError as e:
        logger.warning(f"验证失败：{e}")
        return error_response(str(e), code=3001)
        
    except AIAnalysisError as e:
        logger.error(f"AI 分析失败：{e}")
        return error_response(str(e), code=2001)
        
    except Exception as e:
        logger.error(f"未知错误：{e}", exc_info=True)
        return error_response('服务器内部错误', code=1)
```

## 📖 相关文档

- [REFACTORING_DOCUMENT.md](./REFACTORING_DOCUMENT.md) - 详细重构文档
- [OPTIMIZATION_SUMMARY.md](./OPTIMIZATION_SUMMARY.md) - 优化总结
- [CODE_OPTIMIZATION_PLAN.md](./CODE_OPTIMIZATION_PLAN.md) - 优化计划

## 🆘 获取帮助

1. 查看文档: 阅读相关 Markdown 文档
2. 查看源码: 代码中有完整的类型提示和文档
3. 联系团队: 遇到问题联系开发团队

---

**最后更新**: 2025-03-01  
**版本**: v2.0
