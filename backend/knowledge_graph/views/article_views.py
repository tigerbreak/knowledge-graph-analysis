"""
文章分析相关的视图模块
包含文章上传、分析、历史查询等功能
"""
import logging
import json
import requests
import docx
import PyPDF2
import io
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response

from ..models import Article, Work, AnalysisResult
from ..services.neo4j_service import Neo4jService

logger = logging.getLogger(__name__)
neo4j_service = Neo4jService()


def call_ai_api(content):
    """
    调用 DeepSeek API 进行文章分析
    
    Args:
        content: 文章内容
        
    Returns:
        dict: 分析结果
    """
    session = requests.Session()
    session.trust_env = False
    session.proxies = {
        "http": None,
        "https": None
    }

    url = "https://api.deepseek.com/v1/chat/completions"
    
    system_prompt = """你是一个文学作品分析专家。请分析以下文章内容，识别出:
    1. 文章所属的作品名称
    2. 文章标题（根据内容总结，15 字以内）
    3. 文章中的人物、势力、事件和关系信息

    请以 JSON 格式返回分析结果：
    {
        "work_name": "作品名称",
        "title": "文章标题",
        "characters": [
            {
                "name": "人物名",
                "description": "人物描述",
                "faction": "所属势力"
            }
        ],
        "forces": [
            {
                "name": "势力名",
                "description": "描述"
            }
        ],
        "events": [
            {
                "title": "事件标题",
                "description": "事件描述",
                "participants": ["参与者 1", "参与者 2"],
                "location": "发生地点",
                "time": "发生时间"
            }
        ],
        "relationships": [
            {
                "source": "来源人物",
                "target": "目标人物/势力",
                "type": "关系类型",
                "description": "关系描述"
            }
        ]
    }

    关系类型说明：
    - 人物间关系：monarch-minister(君臣)、master-apprentice(师徒)、friend(朋友)、enemy(敌人)、family(家人)、spouse(配偶)
    - 人物与势力关系：belongs_to(属于)、leads(领导)、affiliated(附属)、opposes(对立)

    要求：
    1. 关系要双向记录，比如 A 是 B 的君主，要同时记录 B 是 A 的臣子
    2. 势力关系要准确，一个人物可以同时属于多个势力
    3. 事件要包含所有相关人物和具体地点
    4. 时间信息如果模糊也要记录，如"某年冬天"
    5. 所有描述要简明扼要
    6. 请确保返回的是合法的 JSON 格式，不要包含任何其他文本
    """

    headers = {
        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    max_retries = 3
    retry_count = 0
    chunk_size = settings.DEEPSEEK_CHUNK_SIZE

    while retry_count < max_retries:
        try:
            content_chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
            combined_analysis = {
                "work_name": "",
                "title": "",
                "characters": [],
                "forces": [],
                "events": [],
                "relationships": []
            }

            for chunk in content_chunks:
                data = {
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": chunk}
                    ],
                    "model": "deepseek-chat",
                    "temperature": 0.1,
                    "max_tokens": 2000,
                    "stream": False
                }

                response = session.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=settings.DEEPSEEK_API_TIMEOUT
                )

                if response.status_code == 200:
                    result = response.json()
                    try:
                        content = result['choices'][0]['message']['content']
                        content = content.strip()
                        if content.startswith('```json'):
                            content = content[7:]
                        elif content.startswith('```'):
                            content = content[3:]
                        if content.endswith('```'):
                            content = content[:-3]
                        content = content.strip()
                        
                        analysis = json.loads(content)
                        
                        # 规范化数据
                        if 'characters' in analysis:
                            for char in analysis['characters']:
                                char['name'] = char.get('name', '')
                                char['description'] = char.get('description', '')
                                char['faction'] = char.get('faction', '')
                                
                        if 'forces' in analysis:
                            for force in analysis['forces']:
                                force['name'] = force.get('name', '')
                                force['description'] = force.get('description', '')
                                
                        if 'events' in analysis:
                            for event in analysis['events']:
                                event['title'] = event.get('title', '')
                                event['description'] = event.get('description', '')
                                event['location'] = event.get('location', '')
                                event['time'] = event.get('time', '')
                                if not isinstance(event.get('participants'), list):
                                    event['participants'] = []
                                    
                        if 'relationships' in analysis:
                            for rel in analysis['relationships']:
                                rel['source'] = rel.get('source', '')
                                rel['target'] = rel.get('target', '')
                                rel['type'] = rel.get('type', '').lower()
                                rel['description'] = rel.get('description', '')
                        
                        # 合并分析结果
                        if not combined_analysis["work_name"] and analysis.get("work_name"):
                            combined_analysis["work_name"] = analysis["work_name"]
                        if not combined_analysis["title"] and analysis.get("title"):
                            combined_analysis["title"] = analysis["title"]
                        combined_analysis["characters"].extend(analysis.get("characters", []))
                        combined_analysis["forces"].extend(analysis.get("forces", []))
                        combined_analysis["events"].extend(analysis.get("events", []))
                        combined_analysis["relationships"].extend(analysis.get("relationships", []))
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON 解析失败：{content}")
                        logger.error(f"错误详情：{str(e)}")
                        continue
                else:
                    response.raise_for_status()

            # 去重处理
            seen_chars = set()
            unique_chars = []
            for char in combined_analysis["characters"]:
                if char["name"] and char["name"] not in seen_chars:
                    seen_chars.add(char["name"])
                    unique_chars.append(char)
            combined_analysis["characters"] = unique_chars
            
            seen_forces = set()
            unique_forces = []
            for force in combined_analysis["forces"]:
                if force["name"] and force["name"] not in seen_forces:
                    seen_forces.add(force["name"])
                    unique_forces.append(force)
            combined_analysis["forces"] = unique_forces
            
            return combined_analysis

        except Exception as e:
            retry_count += 1
            logger.error(f"AI API 调用失败 (尝试 {retry_count}/{max_retries}): {str(e)}")
            if retry_count >= max_retries:
                logger.error("AI API 调用失败，已达最大重试次数")
                return None


@api_view(['POST'])
@require_http_methods(["POST"])
def upload_file(request):
    """
    上传文件并进行分析
    
    Request:
        - file: 上传的文件 (docx 或 pdf)
        
    Returns:
        JsonResponse: 分析结果
    """
    try:
        if 'file' not in request.FILES:
            return JsonResponse({
                'code': 1,
                'message': '请上传文件'
            })
        
        file = request.FILES['file']
        content = ''
        
        # 根据文件类型读取内容
        if file.name.endswith('.docx'):
            doc = docx.Document(file)
            content = '\n'.join([para.text for para in doc.paragraphs])
        elif file.name.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
            content = '\n'.join([page.extract_text() for page in pdf_reader.pages])
        else:
            return JsonResponse({
                'code': 1,
                'message': '不支持的文件格式，请上传 docx 或 pdf 文件'
            })
        
        if not content.strip():
            return JsonResponse({
                'code': 1,
                'message': '文件内容为空'
            })
        
        # 调用 AI 分析
        analysis_result = call_ai_api(content)
        
        if not analysis_result:
            return JsonResponse({
                'code': 1,
                'message': 'AI 分析失败'
            })
        
        # 获取或创建作品
        work_name = analysis_result.get('work_name', '未知作品')
        if not work_name:
            work_name = '未知作品'
            
        work, created = Work.objects.get_or_create(name=work_name)
        
        # 创建文章记录
        article = Article.objects.create(
            title=analysis_result.get('title', '未命名文章'),
            content=content[:10000],  # 限制存储长度
            work=work
        )
        
        # 保存分析结果
        AnalysisResult.objects.create(
            article=article,
            result=analysis_result
        )
        
        # 导入到 Neo4j
        neo4j_service.import_analysis_result(analysis_result)
        
        return JsonResponse({
            'code': 0,
            'message': '分析成功',
            'data': {
                'article_id': article.id,
                'work_name': work_name,
                'title': analysis_result.get('title', ''),
                'characters_count': len(analysis_result.get('characters', [])),
                'forces_count': len(analysis_result.get('forces', [])),
                'events_count': len(analysis_result.get('events', [])),
                'relationships_count': len(analysis_result.get('relationships', []))
            }
        })
        
    except Exception as e:
        logger.error(f"上传文件分析失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'分析失败：{str(e)}'
        })


@api_view(['GET'])
def get_analysis_history(request):
    """
    获取分析历史记录
    
    Query Parameters:
        - work_id: 作品 ID (可选)
        - limit: 返回数量限制 (可选，默认 20)
        
    Returns:
        JsonResponse: 分析历史列表
    """
    try:
        work_id = request.GET.get('work_id')
        limit = int(request.GET.get('limit', 20))
        
        # 构建查询条件
        filters = {}
        if work_id:
            filters['article__work_id'] = work_id
        
        # 获取分析结果
        results = AnalysisResult.objects.filter(**filters).select_related(
            'article', 'article__work'
        ).order_by('-created_at')[:limit]
        
        history = []
        for result in results:
            history.append({
                'id': result.id,
                'article_id': result.article.id,
                'title': result.article.title,
                'work_name': result.article.work.name if result.article.work else '',
                'created_at': result.created_at.isoformat(),
                'result': result.result
            })
        
        return JsonResponse({
            'code': 0,
            'message': 'success',
            'data': {
                'history': history,
                'total': len(history)
            }
        })
        
    except Exception as e:
        logger.error(f"获取分析历史失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'获取分析历史失败：{str(e)}'
        })


@api_view(['GET'])
def article_list(request):
    """
    获取文章列表
    
    Query Parameters:
        - work_id: 作品 ID (可选)
        - search: 搜索关键词 (可选)
        
    Returns:
        JsonResponse: 文章列表
    """
    try:
        work_id = request.GET.get('work_id')
        search = request.GET.get('search', '')
        
        # 构建查询条件
        filters = {}
        if work_id:
            filters['work_id'] = work_id
        if search:
            filters['title__icontains'] = search
        
        # 获取文章列表
        articles = Article.objects.filter(**filters).select_related('work').order_by('-created_at')
        
        articles_data = []
        for article in articles:
            articles_data.append({
                'id': article.id,
                'title': article.title,
                'work_id': article.work.id if article.work else None,
                'work_name': article.work.name if article.work else '',
                'created_at': article.created_at.isoformat(),
                'has_analysis': hasattr(article, 'analysisresult')
            })
        
        return JsonResponse({
            'code': 0,
            'message': 'success',
            'data': {
                'articles': articles_data,
                'total': len(articles_data)
            }
        })
        
    except Exception as e:
        logger.error(f"获取文章列表失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'获取文章列表失败：{str(e)}'
        })


@api_view(['GET'])
def article_detail(request, article_id):
    """
    获取文章详情
    
    Args:
        article_id: 文章 ID
        
    Returns:
        JsonResponse: 文章详情
    """
    try:
        article = Article.objects.select_related('work').get(id=article_id)
        
        # 获取分析结果
        analysis_result = None
        if hasattr(article, 'analysisresult'):
            analysis_result = article.analysisresult.result
        
        return JsonResponse({
            'code': 0,
            'message': 'success',
            'data': {
                'id': article.id,
                'title': article.title,
                'content': article.content,
                'work_id': article.work.id if article.work else None,
                'work_name': article.work.name if article.work else '',
                'created_at': article.created_at.isoformat(),
                'updated_at': article.updated_at.isoformat(),
                'analysis_result': analysis_result
            }
        })
        
    except Article.DoesNotExist:
        return JsonResponse({
            'code': 1,
            'message': '文章不存在'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"获取文章详情失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'获取文章详情失败：{str(e)}'
        })


@api_view(['GET'])
def article_analysis(request, article_id):
    """
    获取文章的分析结果和图谱数据
    
    Args:
        article_id: 文章 ID
        
    Returns:
        JsonResponse: 分析结果和图谱数据
    """
    try:
        article = Article.objects.select_related('work').get(id=article_id)
        
        # 获取分析结果
        analysis_result = None
        if hasattr(article, 'analysisresult'):
            analysis_result = article.analysisresult.result
        
        # 获取图谱数据
        graph_data = None
        if article.work:
            graph_data = neo4j_service.get_graph_data(article.work.name)
        
        return JsonResponse({
            'code': 0,
            'message': 'success',
            'data': {
                'article': {
                    'id': article.id,
                    'title': article.title,
                    'work_name': article.work.name if article.work else ''
                },
                'analysis_result': analysis_result,
                'graph_data': graph_data
            }
        })
        
    except Article.DoesNotExist:
        return JsonResponse({
            'code': 1,
            'message': '文章不存在'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"获取文章分析结果失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'获取文章分析结果失败：{str(e)}'
        })
