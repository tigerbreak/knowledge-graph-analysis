from django.shortcuts import render
from rest_framework import viewsets, views, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Character, Relationship, Event, Work, Article, AnalysisResult
from .serializers import CharacterSerializer, RelationshipSerializer, EventSerializer
from django.db.models import Q
import json
import requests
import logging
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import time
from django.views.decorators.http import require_http_methods
from .services.neo4j_service import Neo4jService
from py2neo import Graph, Node, Relationship as Neo4jRelationship
from django.http import HttpResponse
from neo4j import GraphDatabase
import docx
import PyPDF2
import io

logger = logging.getLogger(__name__)
neo4j_service = Neo4jService()

# Neo4j connection
# 移除硬编码的连接信息，使用settings中的配置
def get_graph():
    """获取 Neo4j 数据库连接"""
    return GraphDatabase.driver(
        settings.NEO4J_CONFIG['uri'],
        auth=settings.NEO4J_CONFIG['auth']
    ).session()

def get_mysql_works():
    """从 MySQL 获取作品列表"""
    try:
        works = Work.objects.all().values('id', 'name')
        return list(works)
    except Exception as e:
        logger.error(f"获取作品列表失败: {str(e)}", exc_info=True)
        return []

def call_ai_api(content):
    """调用 DeepSeek API 进行文章分析"""
    session = requests.Session()
    session.trust_env = False  # 禁用环境代理
    session.proxies = {
        "http": None,
        "https": None
    }

    url = "https://api.deepseek.com/v1/chat/completions"
    
    system_prompt = """你是一个文学作品分析专家。请分析以下文章内容，识别出:
    1. 文章所属的作品名称
    2. 文章标题（根据内容总结，15字以内）
    3. 文章中的人物、势力、事件和关系信息

    请以JSON格式返回分析结果：
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
                "participants": ["参与者1", "参与者2"],
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
    1. 关系要双向记录，比如A是B的君主，要同时记录B是A的臣子
    2. 势力关系要准确，一个人物可以同时属于多个势力
    3. 事件要包含所有相关人物和具体地点
    4. 时间信息如果模糊也要记录，如"某年冬天"
    5. 所有描述要简明扼要
    6. 请确保返回的是合法的JSON格式，不要包含任何其他文本
    """

    headers = {
        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    max_retries = 3
    retry_count = 0
    chunk_size = 5000

    while retry_count < max_retries:
        try:
            # 分块处理长文本
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
                    timeout=(5, 120)  # 连接超时5秒，读取超时120秒
                )

                if response.status_code == 200:
                    result = response.json()
                    try:
                        # 清理 AI 返回的文本，确保只包含 JSON
                        content = result['choices'][0]['message']['content']
                        # 移除可能的 ```json 和 ``` 标记
                        content = content.strip()
                        if content.startswith('```json'):
                            content = content[7:]
                        elif content.startswith('```'):
                            content = content[3:]
                        if content.endswith('```'):
                            content = content[:-3]
                        content = content.strip()
                        
                        analysis = json.loads(content)
                        
                        # 验证和规范化数据
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
                        logger.error(f"JSON解析失败: {content}")
                        logger.error(f"错误详情: {str(e)}")
                        continue
                else:
                    response.raise_for_status()

            # 去重处理
            combined_analysis["characters"] = list({c["name"]: c for c in combined_analysis["characters"]}.values())
            combined_analysis["forces"] = list({f["name"]: f for f in combined_analysis["forces"]}.values())
            combined_analysis["events"] = list({e["title"]: e for e in combined_analysis["events"]}.values())
            # 关系去重时考虑source、target和type三个字段
            combined_analysis["relationships"] = list({f"{r['source']}-{r['target']}-{r['type']}": r for r in combined_analysis["relationships"]}.values())

            return combined_analysis

        except requests.exceptions.RequestException as e:
            retry_count += 1
            if retry_count == max_retries:
                logger.error(f"API调用失败: {str(e)}")
                raise
            time.sleep(5)  # 重试前等待5秒
        finally:
            session.close()

    raise Exception("达到最大重试次数")

@require_http_methods(["POST"])
def analyze_article(request):
    """分析文章内容"""
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        
        if not content:
            return JsonResponse({
                'code': 1,
                'message': '文章内容不能为空'
            })

        content_length = len(content)
        logging.info(f'收到文章分析请求: content_length={content_length}')
        
        # 调用AI接口进行分析
        analysis_result = call_ai_api(content)
        if not analysis_result:
            return JsonResponse({
                'code': 1,
                'message': 'AI分析失败'
            })
            
        # 从分析结果中提取标题和作品名
        title = analysis_result.get('title', '')
        work_name = analysis_result.get('work_name', '')
        logging.info(f'AI分析完成，生成标题: {title}, 作品: {work_name}')
        
        # 获取或创建作品
        work, _ = Work.objects.get_or_create(name=work_name)
        
        # 创建文章
        article = Article.objects.create(
            title=title,
            content=content,
            work=work
        )
        logging.info(f"创建文章: {article.title}")
        
        # 尝试存储到Neo4j，但不影响整体流程
        neo4j_success = False
        try:
            # 检查 Neo4j 是否可用
            session = get_graph()
            # 尝试执行一个简单的查询来测试连接
            session.run("MATCH (n) RETURN n LIMIT 1")
            
            # 如果连接正常，则存储数据
            store_analysis_to_neo4j(article.id, analysis_result)
            neo4j_success = True
            logging.info('Neo4j数据存储成功')
        except Exception as e:
            logging.error(f'Neo4j存储失败: {str(e)}')
            # 这里不抛出异常，继续处理

        return JsonResponse({
            'code': 0,
            'message': '分析成功' + ('' if neo4j_success else '（知识图谱暂时无法使用）'),
            'data': {
                'article_id': article.id,
                'analysis': analysis_result,
                'neo4j_success': neo4j_success
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'code': 1,
            'message': '无效的请求数据格式'
        })
    except Exception as e:
        logging.error(f'分析文章失败: {str(e)}')
        return JsonResponse({
            'code': 1,
            'message': f'分析失败: {str(e)}'
        })

def store_analysis_to_neo4j(article_id, analysis_result):
    """将分析结果存储到 Neo4j"""
    try:
        session = get_graph()
        logger.info(f"开始存储分析结果: article_id={article_id}")
        logger.info(f"分析结果: {json.dumps(analysis_result, ensure_ascii=False)}")
        
        # 获取文章信息
        article = Article.objects.get(id=article_id)
        work = article.work
        title = article.title
        logger.info(f"获取到文章信息: title={title}, work={work.name}")
        
        # 获取或创建作品节点
        work_query = """
        MERGE (w:Work {id: $id})
        SET w.name = $name
        RETURN w
        """
        try:
            session.run(work_query, id=str(work.id), name=work.name)
            logger.info(f"创建作品节点成功: {work.name}")
        except Exception as e:
            logger.error(f"创建作品节点失败: {str(e)}")
            raise
        
        # 创建文章节点
        article_query = """
        MERGE (a:Article {id: $id})
        SET a.title = $title, a.work_id = $work_id
        WITH a
        MATCH (w:Work {id: $work_id})
        MERGE (a)-[:BELONGS_TO]->(w)
        """
        try:
            session.run(article_query, id=str(article_id), title=title, work_id=str(work.id))
            logger.info(f"创建文章节点成功: {title}")
        except Exception as e:
            logger.error(f"创建文章节点失败: {str(e)}")
            raise
        
        # 存储势力节点
        force_nodes = {}
        for force in analysis_result.get('forces', []):
            logger.info(f"开始处理势力节点: {force['name']}")
            force_query = """
            MERGE (f:Force {name: $name})
            SET f.description = $description,
                f.work_id = $work_id
            WITH f
            MATCH (w:Work {id: $work_id})
            MERGE (f)-[:BELONGS_TO]->(w)
            RETURN f
            """
            try:
                result = session.run(force_query, 
                                   name=force['name'],
                                   description=force.get('description', ''),
                                   work_id=str(work.id))
                force_nodes[force['name']] = force['name']
                logger.info(f"创建势力节点成功: {force['name']}")
            except Exception as e:
                logger.error(f"创建势力节点失败: {force['name']}, 错误: {str(e)}")
                continue
        
        # 存储人物节点
        character_nodes = {}
        for character in analysis_result.get('characters', []):
            logger.info(f"开始处理人物节点: {character['name']}, 势力: {character.get('faction', 'None')}")
            char_query = """
            MERGE (c:Character {name: $name})
            SET c.description = $description,
                c.faction = $faction,
                c.work_id = $work_id
            WITH c
            MATCH (w:Work {id: $work_id})
            MERGE (c)-[:BELONGS_TO]->(w)
            WITH c
            MATCH (a:Article {id: $article_id})
            MERGE (a)-[:HAS_CHARACTER]->(c)
            RETURN c
            """
            try:
                result = session.run(char_query,
                                   name=character['name'],
                                   description=character.get('description', ''),
                                   faction=character.get('faction', ''),
                                   work_id=str(work.id),
                                   article_id=str(article_id))
                character_nodes[character['name']] = character['name']
                logger.info(f"创建人物节点和关系成功: {character['name']}")
            except Exception as e:
                logger.error(f"创建人物节点失败: {character['name']}, 错误: {str(e)}")
                continue
            
            # 如果人物有所属势力，创建人物到势力的关系
            if character.get('faction') and character['faction'] in force_nodes:
                faction_rel_query = """
                MATCH (c:Character {name: $char_name})
                MATCH (f:Force {name: $force_name})
                MERGE (c)-[:BELONGS_TO]->(f)
                """
                try:
                    session.run(faction_rel_query,
                              char_name=character['name'],
                              force_name=character['faction'])
                    logger.info(f"创建人物-势力关系成功: {character['name']} -> {character['faction']}")
                except Exception as e:
                    logger.error(f"创建人物-势力关系失败: {character['name']} -> {character['faction']}, 错误: {str(e)}")
        
        # 存储人物关系
        for relation in analysis_result.get('relationships', []):
            source_name = relation['source']
            target_name = relation['target']
            relation_type = relation['type'].upper().replace('-', '_')
            
            logger.info(f"开始处理关系: {source_name} -[{relation_type}]-> {target_name}")
            
            if source_name in character_nodes and target_name in character_nodes:
                rel_query = f"""
                MATCH (source:Character {{name: $source_name}})
                MATCH (target:Character {{name: $target_name}})
                MERGE (source)-[r:{relation_type}]->(target)
                SET r.description = $description
                """
                try:
                    session.run(rel_query,
                              source_name=source_name,
                              target_name=target_name,
                              description=relation.get('description', ''))
                    logger.info(f"创建人物关系成功: {source_name} -[{relation_type}]-> {target_name}")
                except Exception as e:
                    logger.error(f"创建人物关系失败: {source_name} -[{relation_type}]-> {target_name}, 错误: {str(e)}")
            else:
                logger.warning(f"跳过关系创建，源节点或目标节点不存在: {source_name} -[{relation_type}]-> {target_name}")
        
        # 存储事件到MySQL
        logger.info("开始存储事件数据")
        for event in analysis_result.get('events', []):
            try:
                # 使用get_or_create避免重复创建
                event_obj, created = Event.objects.get_or_create(
                    name=event['title'],
                    article_id=article_id,
                    defaults={
                        'description': event.get('description', ''),
                        'location': event.get('location', ''),
                        'time': event.get('time', ''),
                        'participants': ','.join(event.get('participants', [])),
                        'work': work
                    }
                )
                if created:
                    logger.info(f"创建事件成功: {event['title']}")
                else:
                    logger.info(f"事件已存在: {event['title']}")
            except Exception as e:
                logger.error(f"创建事件失败: {event['title']}, 错误: {str(e)}")
                continue
        
        logger.info("分析结果存储完成")
        
    except Exception as e:
        logger.error(f"存储分析结果时发生错误: {str(e)}")
        raise
    finally:
        session.close()

@csrf_exempt
def upload_file(request):
    if request.method != 'POST':
        return JsonResponse({'code': 1, 'message': '不支持的请求方法'})
    
    try:
        file = request.FILES.get('file')
        if not file:
            return JsonResponse({'code': 1, 'message': '未找到上传的文件'})

        content = ''
        file_type = file.content_type

        if file_type == 'text/plain':
            content = file.read().decode('utf-8')
        elif file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            doc = docx.Document(io.BytesIO(file.read()))
            content = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        elif file_type == 'application/pdf':
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
            content = '\n'.join([page.extract_text() for page in pdf_reader.pages])
        else:
            return JsonResponse({'code': 1, 'message': '不支持的文件格式'})

        return JsonResponse({
            'code': 0,
            'message': '上传成功',
            'data': {
                'content': content
            }
        })

    except Exception as e:
        return JsonResponse({'code': 1, 'message': f'文件处理失败: {str(e)}'})

class RelationshipViewSet(viewsets.ModelViewSet):
    """
    关系视图集
    """
    queryset = Relationship.objects.all()
    serializer_class = RelationshipSerializer

def get_analysis_history(request):
    """获取分析历史记录"""
    try:
        # 获取最近的10条分析记录
        history = AnalysisResult.objects.select_related('article').order_by('-created_at')[:10]
        
        results = []
        for item in history:
            results.append({
                'id': item.id,
                'title': item.article.title if item.article else '',
                'created_at': item.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'content': item.content,
                'characters': item.characters,
                'relationships': item.relationships,
                'events': item.events
            })
        
        return JsonResponse({
            'code': 0,
            'message': '获取历史记录成功',
            'data': results
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 1,
            'message': f'获取历史记录失败: {str(e)}',
            'data': []
        })

@api_view(['GET'])
def article_list(request):
    """获取文章列表，按作品分组"""
    try:
        # 获取所有作品及其关联的文章
        works = Work.objects.prefetch_related('articles').all()
        
        # 构建响应数据
        data = []
        for work in works:
            work_data = {
                'id': work.id,  # 修改 work_id 为 id
                'work_name': work.name,  # 保持 work_name
                'articles': [{
                    'id': article.id,
                    'title': article.title,
                    'created_at': article.created_at.strftime('%Y-%m-%d %H:%M:%S')
                } for article in work.articles.all()]
            }
            data.append(work_data)
        
        return JsonResponse({
            'code': 0,
            'message': '获取成功',
            'data': data
        })
    except Exception as e:
        logger.error(f"获取文章列表失败: {str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'获取失败: {str(e)}'
        }, status=500)

@api_view(['GET'])
def article_detail(request, article_id):
    """获取文章详情"""
    try:
        article = Article.objects.select_related('work').get(id=article_id)
        
        data = {
            'id': article.id,
            'title': article.title,
            'content': article.content,
            'work_name': article.work.name,
            'created_at': article.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
            
        return JsonResponse({
            'code': 0,
            'message': '获取成功',
            'data': data
        })
    except Article.DoesNotExist:
            return JsonResponse({
                'code': 1,
            'message': '文章不存在'
            }, status=404)
    except Exception as e:
        logger.error(f"获取文章详情失败: {str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'获取失败: {str(e)}'
        }, status=500)

@api_view(['GET'])
def article_analysis(request, article_id):
    """获取文章分析结果"""
    try:
        session = get_graph()
        
        # 添加参数类型检查的日志
        logger.info(f"接收到的 article_id 类型: {type(article_id)}, 值: {article_id}")
        
        # 获取文章相关的所有人物节点
        char_query = """
        MATCH (a:Article {id: $article_id})-[:HAS_CHARACTER]->(c:Character)
        RETURN DISTINCT c.name as name, c.description as description, c.faction as faction
        """
        # 执行查询前记录参数
        logger.info(f"执行人物查询，参数 article_id: {str(article_id)}")
        char_results = session.run(char_query, article_id=str(article_id)).data()
        logger.info(f"人物查询结果: {json.dumps(char_results, ensure_ascii=False)}")
        
        characters = [{
            'name': char['name'],
            'description': char['description'],
            'faction': char['faction']
        } for char in char_results]
        logger.info(f"获取到人物数据: {len(characters)} 个")
        
        # 获取文章相关的所有势力节点
        force_query = """
        MATCH (a:Article {id: $article_id})-[:HAS_CHARACTER]->(c:Character)-[:BELONGS_TO]->(f:Force)
        RETURN DISTINCT f.name as name, f.description as description
        """
        # 执行查询前记录参数
        logger.info(f"执行势力查询，参数 article_id: {str(article_id)}")
        force_results = session.run(force_query, article_id=str(article_id)).data()
        logger.info(f"势力查询结果: {json.dumps(force_results, ensure_ascii=False)}")
        
        forces = [{
            'name': force['name'],
            'description': force['description']
        } for force in force_results]
        logger.info(f"获取到势力数据: {len(forces)} 个")
        
        # 获取文章中人物之间的关系
        rel_query = """
        MATCH (a:Article {id: $article_id})-[:HAS_CHARACTER]->(c1:Character)
        MATCH (a)-[:HAS_CHARACTER]->(c2:Character)
        MATCH (c1)-[r]->(c2)
        WHERE type(r) <> 'BELONGS_TO' AND type(r) <> 'HAS_CHARACTER'
        RETURN DISTINCT c1.name as source, c2.name as target, type(r) as type
        """
        rel_results = session.run(rel_query, article_id=str(article_id)).data()
        
        # 处理关系数据，添加中文类型
        relation_type_map = {
            'FRIEND': '朋友',
            'ENEMY': '敌人',
            'FAMILY': '家人',
            'MASTER_APPRENTICE': '师徒',
            'MASTER-APPRENTICE': '师徒',
            'MONARCH_MINISTER': '君臣',
            'MONARCH-MINISTER': '君臣',
            'SPOUSE': '配偶',
            'BELONGS_TO': '归属',
            'AFFILIATED': '附属',
            'OPPOSES': '对立',
            'LEADS': '领导'
        }
        
        relationships = [{
            'source': rel['source'],
            'target': rel['target'],
            'type': relation_type_map.get(rel['type'], rel['type']),
            'chinese_type': relation_type_map.get(rel['type'], rel['type'])
        } for rel in rel_results]
        logger.info(f"获取到关系数据: {len(relationships)} 个")
        
        # 获取文章中人物和势力的关系
        force_rel_query = """
        MATCH (a:Article {id: $article_id})-[:HAS_CHARACTER]->(c:Character)-[r:BELONGS_TO]->(f:Force)
        RETURN DISTINCT c.name as source, f.name as target
        """
        force_rel_results = session.run(force_rel_query, article_id=str(article_id)).data()
        
        # 添加人物和势力的关系
        force_relationships = [{
            'source': rel['source'],
            'target': rel['target'],
            'type': '归属',
            'chinese_type': '归属'
        } for rel in force_rel_results]
        
        # 使用集合去重
        seen_relationships = set()
        unique_relationships = []
        for rel in relationships + force_relationships:
            rel_key = f"{rel['source']}-{rel['type']}-{rel['target']}"
            if rel_key not in seen_relationships:
                seen_relationships.add(rel_key)
                unique_relationships.append(rel)
        
        logger.info(f"添加势力关系后，总关系数: {len(unique_relationships)} 个")
        
        # 获取事件数据
        events = Event.objects.filter(article_id=article_id).values(
            'id', 'name', 'description', 'location', 'time', 'participants'
        )
        events_list = []
        for event in events:
            event_data = {
                'id': event['id'],
                'title': event['name'],
                'description': event['description'],
                'location': event['location'],
                'time': event['time'],
                'participants': event['participants'].split(',') if event['participants'] else []
            }
            events_list.append(event_data)
        logger.info(f"从 MySQL 获取到 {len(events_list)} 个事件")
        
        session.close()
        
        return JsonResponse({
            'code': 0,
            'message': 'success',
            'data': {
                'characters': characters,
                'forces': forces,
                'relationships': unique_relationships,
                'events': events_list
            }
        })
        
    except Exception as e:
        logger.error(f"获取文章分析结果失败: {str(e)}")
        if session:
            session.close()
        return JsonResponse({
            'code': 1,
            'message': f'获取分析结果失败: {str(e)}'
        })

@api_view(['GET'])
def get_work_graph(request, work_id):
    """获取作品的知识图谱数据"""
    try:
        logger.info(f"开始获取作品图谱数据: work_id={work_id}")
        session = get_graph()
        
        # 获取所有人物节点
        char_query = """
        MATCH (w:Work {id: $work_id})<-[:BELONGS_TO]-(c:Character)
        WITH DISTINCT c
        RETURN COLLECT({
            id: c.name,
            name: c.name,
            description: c.description,
            type: 'character',
            faction: c.faction,
            category: 0,
            symbolSize: 50
        }) as characters
        """
        char_result = session.run(char_query, work_id=str(work_id)).single()
        characters = char_result['characters'] if char_result else []
        logger.info(f"获取到人物节点: {len(characters)} 个")
        
        # 获取所有势力节点
        force_query = """
        MATCH (w:Work {id: $work_id})<-[:BELONGS_TO]-(f:Force)
        WITH DISTINCT f
        RETURN COLLECT({
            id: f.name,
            name: f.name,
            description: f.description,
            type: 'force',
            category: 1,
            symbolSize: 70
        }) as forces
        """
        force_result = session.run(force_query, work_id=str(work_id)).single()
        forces = force_result['forces'] if force_result else []
        logger.info(f"获取到势力节点: {len(forces)} 个")
        
        # 获取所有事件数据
        events = Event.objects.filter(work_id=work_id).values(
            'id', 'name', 'description', 'time', 'location', 'participants'
        )
        events_list = []
        for event in events:
            event_data = {
                'id': event['id'],
                'title': event['name'],
                'description': event['description'],
                'time': event['time'],
                'location': event['location'],
                'participants': event['participants'].split(',') if event['participants'] else []
            }
            events_list.append(event_data)
        logger.info(f"获取到事件数据: {len(events_list)} 个")
        
        # 合并所有节点
        nodes = characters + forces
        
        # 获取人物之间的关系
        rel_query = """
        MATCH (w:Work {id: $work_id})<-[:BELONGS_TO]-(c1:Character)
        MATCH (c1)-[r]->(c2:Character)-[:BELONGS_TO]->(w)
        WHERE type(r) <> 'BELONGS_TO'
        WITH DISTINCT c1, r, c2
        RETURN COLLECT({
            source: c1.name,
            target: c2.name,
            type: type(r)
        }) as relationships
        """
        rel_result = session.run(rel_query, work_id=str(work_id)).single()
        relationships = rel_result['relationships'] if rel_result else []
        logger.info(f"获取到人物关系: {len(relationships)} 个")
        
        # 获取人物和势力的关系
        force_rel_query = """
        MATCH (w:Work {id: $work_id})<-[:BELONGS_TO]-(c:Character)
        MATCH (c)-[r:BELONGS_TO]->(f:Force)-[:BELONGS_TO]->(w)
        WITH DISTINCT c, f
        RETURN COLLECT({
            source: c.name,
            target: f.name,
            type: 'BELONGS_TO'
        }) as force_relationships
        """
        force_rel_result = session.run(force_rel_query, work_id=str(work_id)).single()
        force_relationships = force_rel_result['force_relationships'] if force_rel_result else []
        logger.info(f"获取到势力关系: {len(force_relationships)} 个")
        
        # 合并所有关系并添加中文类型
        relation_type_map = {
            'FRIEND': '朋友',
            'ENEMY': '敌人',
            'FAMILY': '家人',
            'MASTER_APPRENTICE': '师徒',
            'MASTER-APPRENTICE': '师徒',
            'MONARCH_MINISTER': '君臣',
            'MONARCH-MINISTER': '君臣',
            'SPOUSE': '配偶',
            'BELONGS_TO': '归属',
            'AFFILIATED': '附属',
            'OPPOSES': '对立',
            'LEADS': '领导'
        }
        
        links = []
        seen_links = set()
        
        # 处理人物之间的关系
        for rel in relationships:
            rel_key = f"{rel['source']}-{rel['type']}-{rel['target']}"
            if rel_key not in seen_links:
                seen_links.add(rel_key)
                links.append({
                    'source': rel['source'],
                    'target': rel['target'],
                    'type': rel['type'],
                    'chinese_type': relation_type_map.get(rel['type'], rel['type']),
                    'value': 1
                })
        
        # 处理人物和势力的关系
        for rel in force_relationships:
            rel_key = f"{rel['source']}-{rel['type']}-{rel['target']}"
            if rel_key not in seen_links:
                seen_links.add(rel_key)
                links.append({
                    'source': rel['source'],
                    'target': rel['target'],
                    'type': '归属',
                    'chinese_type': '归属',
                    'value': 1
                })
        
        logger.info(f"总关系数: {len(links)} 个")
        
        # 获取作品信息
        current_work = Work.objects.filter(id=work_id).values('id', 'name').first()
        works = Work.objects.all().values('id', 'name')
        
        response_data = {
            'code': 0,
            'message': 'success',
            'data': {
                'nodes': nodes,
                'links': links,
                'events': events_list,  # 添加事件数据到返回结果
                'current_work': current_work,
                'works': list(works)
            }
        }
        
        logger.info(f"返回数据: {json.dumps(response_data, ensure_ascii=False)}")
        session.close()
        return JsonResponse(response_data)
            
    except Exception as e:
        logger.error(f"获取作品知识图谱数据失败: {str(e)}", exc_info=True)
        if session:
            session.close()
        return JsonResponse({
            'code': 1,
            'message': f"获取作品知识图谱数据失败: {str(e)}"
        })

@api_view(['GET'])
def get_node_details(request, node_id):
    """获取节点详细信息"""
    try:
        session = get_graph()
        
        # 查询节点信息
        node = session.run("MATCH (n) WHERE id(n) = $node_id RETURN n", node_id=node_id).single().value()
        if not node:
            return JsonResponse({
                'code': 1,
                'message': '节点不存在'
            }, status=404)
        
        # 获取节点类型
        node_type = next(iter(node.labels))
        
        # 获取节点属性
        properties = dict(node)
        
        # 获取相关关系
        relationships = []
        rel_query = """
        MATCH (n)-[r]-(m)
        WHERE id(n) = $node_id
        RETURN type(r) as type, m.name as related_name, labels(m) as related_type
        """
        
        rel_results = session.run(rel_query, node_id=node_id).data()
        for rel in rel_results:
            relationships.append({
                'type': rel['type'],
                'related_name': rel['related_name'],
                'related_type': rel['related_type'][0]
            })
        
        return JsonResponse({
            'code': 0,
            'message': '获取成功',
            'data': {
                'type': node_type,
                'properties': properties,
                'relationships': relationships
            }
        })
    except Exception as e:
        logger.error(f"获取节点详情失败: {str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'获取失败: {str(e)}'
        }, status=500)

@require_http_methods(["POST"])
def clean_test_data(request):
    try:
        # 保留ID为17的文章（甄士隐梦幻识通灵）
        keep_article_id = 17
        
        # 获取要保留的文章
        article_to_keep = Article.objects.get(id=keep_article_id)
        work_to_keep = article_to_keep.work
        
        # 删除其他所有文章和作品
        Article.objects.exclude(id=keep_article_id).delete()
        Work.objects.exclude(id=work_to_keep.id).delete()
        
        # 清理Neo4j中的测试数据，但保留指定文章的数据
        neo4j_service = Neo4jService()
        neo4j_service.clean_test_data(keep_article_id)
        
        return JsonResponse({
            'code': 0,
            'message': '测试数据清理成功',
            'data': {
                'kept_article': {
                    'id': article_to_keep.id,
                    'title': article_to_keep.title,
                    'work_name': work_to_keep.name
                }
            }
        })
    except Article.DoesNotExist:
        return JsonResponse({
            'code': 1,
            'message': f'未找到ID为{keep_article_id}的文章'
        })
    except Exception as e:
        logging.error(f'清理测试数据失败: {str(e)}')
        return JsonResponse({
            'code': 1,
            'message': f'清理测试数据失败: {str(e)}'
        })

@require_http_methods(["DELETE"])
def delete_article(request, article_id):
    """删除指定的文章及其相关数据"""
    try:
        # 获取文章
        article = Article.objects.get(id=article_id)
        work = article.work
        
        # 删除 Neo4j 中的数据
        try:
            session = get_graph()
            session.run("MATCH (a:Article {id: $id}) DETACH DELETE a", id=str(article_id))
            logging.info(f'Neo4j数据删除成功: article_id={article_id}')
        except Exception as e:
            logging.error(f'Neo4j数据删除失败: {str(e)}')
            
        # 删除 MySQL 中的文章
        article.delete()
        
        # 检查作品是否还有其他文章
        remaining_articles = Article.objects.filter(work=work).count()
        if remaining_articles == 0:
            # 如果没有其他文章了，删除作品
            work.delete()
            logging.info(f'作品删除成功: work_name={work.name}')
            
        return JsonResponse({
            'code': 0,
            'message': '文章删除成功'
        })
    except Article.DoesNotExist:
        return JsonResponse({
            'code': 1,
            'message': f'未找到ID为{article_id}的文章'
        })
    except Exception as e:
        logging.error(f'删除文章失败: {str(e)}')
        return JsonResponse({
            'code': 1,
            'message': f'删除文章失败: {str(e)}'
        })

@require_http_methods(["GET"])
def work_list(request):
    """获取作品列表"""
    try:
        # 从Neo4j获取作品列表
        session = get_graph()
        neo4j_works = session.run("MATCH (w:Work) RETURN w.id as id, w.name as name").data()
        session.close()
        
        # 从MySQL获取作品列表
        mysql_works = Work.objects.all().values('id', 'name')
        mysql_work_dict = {str(work['id']): work['name'] for work in mysql_works}
        
        # 同步作品数据
        for work in neo4j_works:
            work_id = work['id']
            neo4j_name = work['name']
            
            # 如果MySQL中没有这个作品，或者名称不同，则更新
            if work_id not in mysql_work_dict or mysql_work_dict[work_id] != neo4j_name:
                try:
                    # 先尝试通过ID获取
                    work_obj = Work.objects.filter(id=work_id).first()
                    if work_obj:
                        # 如果存在，更新名称
                        work_obj.name = neo4j_name
                        work_obj.save()
                    else:
                        # 如果不存在，尝试通过名称获取或创建
                        work_obj, created = Work.objects.get_or_create(
                            name=neo4j_name,
                            defaults={'id': work_id}
                        )
                        if not created:
                            # 如果已存在同名作品，更新ID
                            work_obj.id = work_id
                            work_obj.save()
                except Exception as e:
                    logger.error(f"处理作品时出错: {str(e)}")
                    continue
        
        # 返回最新的作品列表，确保ID和名称的一致性
        works = Work.objects.all().values('id', 'name').order_by('id')
        works_list = []
        for work in works:
            works_list.append({
                'id': str(work['id']),  # 确保ID是字符串类型
                'name': work['name'],
                'display_name': f"{work['name']} ({work['id']})"  # 添加显示名称
            })
            
        return JsonResponse({
            'code': 0,
            'message': 'success',
            'data': works_list
        })
    except Exception as e:
        logger.error(f"获取作品列表失败: {str(e)}")
        return JsonResponse({
            'code': 1,
            'message': f'获取作品列表失败: {str(e)}'
        })

@api_view(['GET'])
def get_article_graph_data(request, article_id):
    """获取文章的知识图谱数据"""
    try:
        # 首先获取文章信息
        article = Article.objects.get(id=article_id)
        
        session = get_graph()
        
        # 获取文章相关的所有节点和关系
        query = """
        MATCH (a:Article {id: $article_id})
        WITH a
        MATCH (a)-[:HAS_CHARACTER]->(c:Character)
        OPTIONAL MATCH (c)-[r]-(other)
        WHERE NOT other:Article AND NOT other:Work
        RETURN DISTINCT c, r, other
        UNION
        MATCH (a:Article {id: $article_id})
        WITH a
        MATCH (a)-[:HAS_FORCE]->(f:Force)
        OPTIONAL MATCH (f)-[r]-(other)
        WHERE NOT other:Article AND NOT other:Work
        RETURN DISTINCT f as c, r, other
        UNION
        MATCH (a:Article {id: $article_id})
        WITH a
        MATCH (a)-[:HAS_EVENT]->(e:Event)
        OPTIONAL MATCH (e)-[r]-(other)
        WHERE NOT other:Article AND NOT other:Work
        RETURN DISTINCT e as c, r, other
        """
        
        result = session.run(query, article_id=article_id).data()
        
        # 处理节点和关系数据
        nodes = {}
        links = []
        
        # 添加所有节点
        for record in result:
            # 添加主节点
            if record.get('c'):
                node = record['c']
                node_id = node.get('name', str(node.identity))
                if node_id not in nodes:
                    node_type = list(node.labels)[0].lower()  # 获取节点类型
                    node_data = {
                        'id': node_id,
                        'name': node.get('name', ''),
                        'type': node_type,
                        'description': node.get('description', ''),
                        'work_id': node.get('work_id', '')
                    }
                    nodes[node_id] = node_data
            
            # 添加关联节点
            if record.get('other'):
                node = record['other']
                node_id = node.get('name', str(node.identity))
                if node_id not in nodes:
                    node_type = list(node.labels)[0].lower()  # 获取节点类型
                    node_data = {
                        'id': node_id,
                        'name': node.get('name', ''),
                        'type': node_type,
                        'description': node.get('description', ''),
                        'work_id': node.get('work_id', '')
                    }
                    nodes[node_id] = node_data
            
            # 添加关系
            if record.get('r'):
                rel = record['r']
                source_id = rel.start_node.get('name', str(rel.start_node.identity))
                target_id = rel.end_node.get('name', str(rel.end_node.identity))
                rel_type = type(rel).__name__
                
                # 避免重复的关系
                link_id = f"{source_id}-{rel_type}-{target_id}"
                if link_id not in [f"{l['source']}-{l['type']}-{l['target']}" for l in links]:
                    links.append({
                        'source': source_id,
                        'target': target_id,
                        'type': rel_type,
                        'description': rel.get('description', '')
                    })
        
        return JsonResponse({
            'code': 0,
            'message': '获取成功',
            'data': {
                'nodes': list(nodes.values()),
                'links': links
            }
        })
    except Article.DoesNotExist:
        return JsonResponse({
            'code': 1,
            'message': '文章不存在'
        }, status=404)
    except Exception as e:
        logger.error(f"获取文章知识图谱数据失败: {str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'获取失败: {str(e)}'
        }, status=500)

@api_view(['GET'])
def get_graph_data(request, work_id=None):
    """获取知识图谱数据"""
    try:
        logger.info(f"开始获取图谱数据: work_id={work_id}")
        session = get_graph()
        
        # 如果没有指定 work_id，获取第一个作品的 ID
        if not work_id:
            first_work = Work.objects.first()
            if first_work:
                work_id = first_work.id
                logger.info(f"未指定work_id，使用第一个作品: {work_id}")
            else:
                logger.info("没有找到任何作品")
                return JsonResponse({
                    'code': 0,
                    'message': 'success',
                    'data': {
                        'nodes': [],
                        'links': [],
                        'current_work': None,
                        'works': []
                    }
                })
        
        # 获取所有作品列表
        works = Work.objects.all().values('id', 'name').order_by('id')
        works_list = []
        for work in works:
            works_list.append({
                'id': str(work['id']),  # 确保ID是字符串类型
                'name': work['name'],
                'display_name': f"{work['name']} ({work['id']})"  # 添加显示名称
            })
        logger.info(f"获取到作品列表: {works_list}")
        
        # 获取当前作品信息
        current_work = Work.objects.filter(id=work_id).values('id', 'name').first()
        if current_work:
            current_work = {
                'id': str(current_work['id']),
                'name': current_work['name'],
                'display_name': f"{current_work['name']} ({current_work['id']})"
            }
        logger.info(f"当前作品信息: {current_work}")
        
        # 构建 Neo4j 查询
        query = """
        MATCH (w:Work {id: $work_id})
        
        OPTIONAL MATCH (c:Character)-[:BELONGS_TO]->(w)
        WITH w, COLLECT(DISTINCT {
            name: c.name,
            description: c.description,
            type: 'character',
            faction: c.faction
        }) as characters
        
        OPTIONAL MATCH (f:Force)-[:BELONGS_TO]->(w)
        WITH w, characters, COLLECT(DISTINCT {
            name: f.name,
            description: f.description,
            type: 'force'
        }) as forces
        
        OPTIONAL MATCH (e:Event)-[:BELONGS_TO]->(w)
        WITH w, characters, forces, COLLECT(DISTINCT {
            name: e.name,
            description: e.description,
            type: 'event',
            time: e.time,
            location: e.location
        }) as events
        
        RETURN {
            characters: characters,
            forces: forces,
            events: events
        } as data
        """
        
        result = session.run(query, work_id=str(work_id)).data()
        session.close()
        
        if not result:
            logger.warning(f"未找到作品 {work_id} 的数据")
            return JsonResponse({
                'code': 0,
                'message': 'success',
                'data': {
                    'nodes': [],
                    'links': [],
                    'current_work': current_work,
                    'works': works_list
                }
            })
        
        data = result[0]['data']
        
        # 构建节点和关系数据
        nodes = []
        links = []
        
        # 添加人物节点
        for char in data['characters']:
            nodes.append({
                'id': char['name'],
                'name': char['name'],
                'type': 'character',
                'description': char.get('description', ''),
                'faction': char.get('faction', '')
            })
        
        # 添加势力节点
        for force in data['forces']:
            nodes.append({
                'id': force['name'],
                'name': force['name'],
                'type': 'force',
                'description': force.get('description', '')
            })
        
        # 添加事件节点
        for event in data['events']:
            nodes.append({
                'id': event['name'],
                'name': event['name'],
                'type': 'event',
                'description': event.get('description', ''),
                'time': event.get('time', ''),
                'location': event.get('location', '')
            })
        
        return JsonResponse({
            'code': 0,
            'message': 'success',
            'data': {
                'nodes': nodes,
                'links': links,
                'current_work': current_work,
                'works': works_list
            }
        })
    except Exception as e:
        logger.error(f"获取知识图谱数据失败: {str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'获取失败: {str(e)}'
        })

@api_view(['POST'])
def clean_graph_data(request):
    """清理图谱数据"""
    try:
        session = get_graph()
        
        # 清理无效节点
        session.run("MATCH (n) DETACH DELETE n")
        
        # 检查所有作品的数据
        works = Work.objects.all()
        work_data = []
        for work in works:
            result = session.run("MATCH (c:Character)-[:BELONGS_TO]->(w:Work {id: $id}) RETURN c", id=str(work.id)).data()
            if result:
                work_data.append({
                    'work_id': work.id,
                    'work_name': work.name,
                    'characters': result
                })
        
        return JsonResponse({
            'code': 0,
            'message': '数据清理完成',
            'data': work_data
        })
    except Exception as e:
        logger.error(f"清理图谱数据失败: {str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'清理失败: {str(e)}'
        })

@api_view(['GET'])
def test_relationships(request, work_id):
    """获取作品的人物关系数据"""
    try:
        logger.info(f"开始获取作品关系数据: work_id={work_id}")
        session = get_graph()
        
        # 获取当前作品信息
        current_work = Work.objects.filter(id=work_id).values('id', 'name').first()
        if not current_work:
            logger.error(f"作品不存在: work_id={work_id}")
            return JsonResponse({
                'code': 1,
                'message': '作品不存在',
                'data': None
            }, status=404)
            
        logger.info(f"当前作品信息: {current_work}")
        
        # 获取所有作品列表
        works = Work.objects.all().values('id', 'name')
        works_list = list(works)
        logger.info(f"获取到作品列表: {works_list}")
        
        # 构建 Neo4j 查询
        query = """
        MATCH (w:Work {id: $work_id})
        
        OPTIONAL MATCH (c:Character)-[:BELONGS_TO]->(w)
        WITH w, COLLECT(DISTINCT c) as characters
        
        OPTIONAL MATCH (f:Force)-[:BELONGS_TO]->(w)
        WITH w, characters, COLLECT(DISTINCT f) as forces
        
        WITH characters + forces as all_nodes
        
        UNWIND all_nodes as n1
        OPTIONAL MATCH (n1)-[r]-(n2)
        WHERE n2 IN all_nodes
        AND type(r) <> 'BELONGS_TO'
        
        RETURN all_nodes as nodes, COLLECT(DISTINCT r) as relationships
        """
        
        logger.info(f"执行Neo4j查询: {query}")
        result = session.run(query, work_id=str(work_id))
        data = result.data()
        logger.info(f"Neo4j查询结果: {data}")
        
        session.close()
        
        record = data[0] if data else None
        
        if not record:
            logger.info("未找到图谱数据")
            return JsonResponse({
                'code': 0,
                'message': 'success',
                'data': {
                    'nodes': [],
                    'links': [],
                    'current_work': current_work,
                    'works': works_list
                }
            })
        
        # 处理节点数据
        nodes_data = []
        node_ids = {}
        
        logger.info("开始处理节点数据")
        for i, node in enumerate(record['nodes']):
            if not node:
                continue
            node_type = list(node.labels)[0].lower()
            node_data = {
                'id': str(i),
                'name': node.get('name', ''),
                'type': node_type,
                'description': node.get('description', ''),
                'faction': node.get('faction', '') if node_type == 'character' else ''
            }
            nodes_data.append(node_data)
            node_ids[node.identity] = str(i)
            logger.info(f"处理节点: {node_data}")
        
        # 处理关系数据
        links_data = []
        logger.info("开始处理关系数据")
        for rel in record.get('relationships', []):
            if not rel or not rel.start_node or not rel.end_node:
                continue
            
            start_node = rel.start_node
            end_node = rel.end_node
            
            # 检查节点是否在 node_ids 中
            if start_node.identity not in node_ids or end_node.identity not in node_ids:
                logger.warning(f"关系的节点不在节点列表中: {start_node.get('name')} -> {end_node.get('name')}")
                continue
                
            link_data = {
                'source': node_ids[start_node.identity],
                'target': node_ids[end_node.identity],
                'type': type(rel).__name__,
                'description': rel.get('description', '')
            }
            links_data.append(link_data)
            logger.info(f"处理关系: {link_data}")
        
        response_data = {
            'code': 0,
            'message': 'success',
            'data': {
                'nodes': nodes_data,
                'links': links_data,
                'current_work': current_work,
                'works': works_list
            }
        }
        logger.info(f"返回数据: {response_data}")
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"获取关系数据失败: {str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'获取失败: {str(e)}',
            'data': None
        }, status=500)

@api_view(['GET'])
def debug_database(request):
    """调试数据库内容"""
    try:
        session = get_graph()
        
        # 修改查询以避免聚合问题
        debug_query = """
        MATCH (a:Article {id: 22})
        
        OPTIONAL MATCH (a)-[:HAS_CHARACTER]->(c:Character)
        WITH a, collect({
            name: c.name,
            description: c.description,
            faction: c.faction
        }) as char_list
        
        OPTIONAL MATCH (a)-[:HAS_FORCE]->(f:Force)
        WITH a, char_list, collect({
            name: f.name,
            description: f.description
        }) as force_list
        
        OPTIONAL MATCH (a)-[:HAS_CHARACTER]->(c1:Character)
        OPTIONAL MATCH (a)-[:HAS_CHARACTER]->(c2:Character)
        OPTIONAL MATCH (c1)-[r]->(c2)
        WHERE c1 <> c2
        WITH a, char_list, force_list,
             collect(DISTINCT {
                source: c1.name,
                target: c2.name,
                type: CASE WHEN r IS NULL THEN 'NO_RELATION' ELSE type(r) END,
                description: r.description
             }) as char_relations
        
        OPTIONAL MATCH (a)-[:HAS_CHARACTER]->(c:Character)
        OPTIONAL MATCH (c)-[rf:BELONGS_TO]->(f:Force)
        WITH char_list, force_list, char_relations,
             collect(DISTINCT CASE WHEN rf IS NOT NULL
                THEN {
                    character: c.name,
                    force: f.name,
                    description: rf.description
                }
                ELSE NULL
             END) as force_relations
        
        RETURN {
            characters: [x IN char_list WHERE x IS NOT NULL],
            forces: [x IN force_list WHERE x IS NOT NULL],
            character_relations: [x IN char_relations WHERE x IS NOT NULL],
            force_relations: [x IN force_relations WHERE x IS NOT NULL]
        } as debug_info
        """
        
        result = session.run(debug_query).data()
        
        # 构建HTML表格内容
        character_rows = ''
        if result and result[0]['debug_info']['characters']:
            for c in result[0]['debug_info']['characters']:
                character_rows += '<tr><td>{}</td><td>{}</td><td>{}</td></tr>'.format(
                    c['name'], 
                    c.get('description', ''), 
                    c.get('faction', '')
                )
        
        force_rows = ''
        if result and result[0]['debug_info']['forces']:
            for f in result[0]['debug_info']['forces']:
                force_rows += '<tr><td>{}</td><td>{}</td></tr>'.format(
                    f['name'],
                    f.get('description', '')
                )
        
        char_relation_rows = ''
        if result and result[0]['debug_info']['character_relations']:
            for r in result[0]['debug_info']['character_relations']:
                char_relation_rows += '<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>'.format(
                    r['source'],
                    r['target'],
                    r['type'],
                    r.get('description', '')
                )
        
        force_relation_rows = ''
        if result and result[0]['debug_info']['force_relations']:
            for r in result[0]['debug_info']['force_relations']:
                force_relation_rows += '<tr><td>{}</td><td>{}</td><td>{}</td></tr>'.format(
                    r['character'],
                    r['force'],
                    r.get('description', '')
                )
        
        # 返回HTML格式的调试信息
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>数据库调试信息</title>
            <style>
                pre {{ background: #f5f5f5; padding: 10px; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid black; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h2>数据库调试信息</h2>
            
            <h3>人物节点</h3>
            <table>
                <tr><th>名称</th><th>描述</th><th>势力</th></tr>
                {character_rows}
            </table>
            
            <h3>势力节点</h3>
            <table>
                <tr><th>名称</th><th>描述</th></tr>
                {force_rows}
            </table>
            
            <h3>人物关系</h3>
            <table>
                <tr><th>源节点</th><th>目标节点</th><th>关系类型</th><th>描述</th></tr>
                {char_relation_rows}
            </table>
            
            <h3>势力关系</h3>
            <table>
                <tr><th>人物</th><th>势力</th><th>描述</th></tr>
                {force_relation_rows}
            </table>
            
            <h3>原始数据</h3>
            <pre>{raw_data}</pre>
        </body>
        </html>
        """.format(
            character_rows=character_rows,
            force_rows=force_rows,
            char_relation_rows=char_relation_rows,
            force_relation_rows=force_relation_rows,
            raw_data=json.dumps(result, ensure_ascii=False, indent=2)
        )
        
        return HttpResponse(html)
        
    except Exception as e:
        logger.error(f"数据库调试失败: {str(e)}", exc_info=True)
        return HttpResponse(f"错误: {str(e)}")

@api_view(['GET'])
def check_relationships(request):
    """检查Neo4j中的所有关系"""
    try:
        session = get_graph()
        
        # 检查文章22的所有关系
        check_query = """
        MATCH (a:Article {id: 22})-[:HAS_CHARACTER]->(c:Character)
        
        OPTIONAL MATCH (c)-[r]->(target)
        WHERE NOT type(r) IN ['BELONGS_TO', 'HAS_CHARACTER', 'HAS_FORCE', 'HAS_EVENT']
        AND (target:Character OR target:Force)
        
        WITH DISTINCT r, c, target
        WHERE r IS NOT NULL
        RETURN type(r) as relation_type,
               labels(c) as source_labels,
               c.name as source_name,
               labels(target) as target_labels,
               target.name as target_name,
               r.description as description
        ORDER BY source_name, target_name
        """
        
        result = session.run(check_query).data()
        
        # 返回HTML格式的调试信息
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Neo4j关系检查（文章22）</title>
            <style>
                pre {{ background: #f5f5f5; padding: 10px; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid black; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h2>Neo4j关系检查（文章22）</h2>
            
            <h3>所有关系</h3>
            <table>
                <tr>
                    <th>关系类型</th>
                    <th>源节点类型</th>
                    <th>源节点名称</th>
                    <th>目标节点类型</th>
                    <th>目标节点名称</th>
                    <th>描述</th>
                </tr>
                {rows}
            </table>
            
            <h3>原始数据</h3>
            <pre>{raw_data}</pre>
        </body>
        </html>
        """.format(
            rows=''.join(
                f"<tr><td>{r['relation_type']}</td><td>{r['source_labels']}</td><td>{r['source_name']}</td>"
                f"<td>{r['target_labels']}</td><td>{r['target_name']}</td><td>{r['description']}</td></tr>"
                for r in result
            ),
            raw_data=json.dumps(result, ensure_ascii=False, indent=2)
        )
        
        return HttpResponse(html)
        
    except Exception as e:
        logger.error(f"检查关系失败: {str(e)}", exc_info=True)
        return HttpResponse(f"错误: {str(e)}")

def clear_database(request):
    """清理所有数据库数据"""
    try:
        # 清理 Neo4j 数据
        session = get_graph()
        session.run("MATCH (n) DETACH DELETE n")
        logger.info("Neo4j 数据已清理")

        # 清理 MySQL 数据
        Work.objects.all().delete()
        Article.objects.all().delete()
        Event.objects.all().delete()
        logger.info("MySQL 数据已清理")

        return JsonResponse({
            'code': 0,
            'message': '数据库清理成功'
        })
    except Exception as e:
        logger.error(f"清理数据库失败: {str(e)}")
        return JsonResponse({
            'code': 1,
            'message': f'清理数据库失败: {str(e)}'
        })

def get_neo4j_works():
    """从Neo4j获取作品列表"""
    session = get_graph()
    try:
        works_query = """
        MATCH (w:Work)
        WHERE w.name IS NOT NULL AND w.name <> ''
        RETURN DISTINCT w.id as id, w.name as name
        ORDER BY w.name
        """
        works_result = session.run(works_query)
        works_list = [{'id': record['id'], 'name': record['name']} for record in works_result]
        logger.info(f"从Neo4j获取到作品列表: {works_list}")
        return works_list
    finally:
        session.close()

@api_view(['GET'])
def character_details(request):
    """获取人物详情"""
    try:
        # 获取请求参数
        work_id = request.GET.get('work_id')
        character_name = request.GET.get('character_name')
        
        logger.info(f"获取人物详情请求参数: work_id={work_id}, character_name={character_name}")
        
        # 从Neo4j获取作品列表
        works_list = get_neo4j_works()
        
        # 构建人物查询
        session = get_graph()
        try:
            if work_id:
                # 如果指定了作品ID，获取该作品下的所有人物
                char_query = """
                MATCH (w:Work {id: $work_id})<-[:BELONGS_TO]-(c:Character)
                WHERE CASE
                    WHEN $character_name IS NOT NULL
                    THEN c.name CONTAINS $character_name
                    ELSE true
                END
                RETURN DISTINCT c.name as name, c.description as description, c.faction as faction
                ORDER BY c.name
                """
                char_results = session.run(char_query, 
                                         work_id=str(work_id),
                                         character_name=character_name)
            else:
                # 如果没有指定作品ID，但指定了人物名称，搜索所有作品中的匹配人物
                char_query = """
                MATCH (w:Work)<-[:BELONGS_TO]-(c:Character)
                WHERE CASE
                    WHEN $character_name IS NOT NULL
                    THEN c.name CONTAINS $character_name
                    ELSE true
                END
                RETURN DISTINCT c.name as name, c.description as description, c.faction as faction, w.name as work_name
                ORDER BY c.name
                """
                char_results = session.run(char_query, character_name=character_name)
            
            # 处理查询结果
            characters_list = []
            for record in char_results:
                character = {
                    'name': record['name'],
                    'description': record['description'] or '',
                    'faction': record['faction'] or '',
                    'force': record['faction'] or '',  # 保持与前端兼容
                    'work_name': record.get('work_name', '')  # 仅在未指定work_id时返回
                }
                logger.info(f"获取到人物数据: {character}")
                characters_list.append(character)
            
            logger.info(f"共获取到 {len(characters_list)} 个人物")
            
            return JsonResponse({
                'code': 0,
                'message': 'success',
                'data': {
                    'characters': characters_list,
                    'works': works_list
                }
            })
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"获取人物详情失败: {str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'获取人物详情失败: {str(e)}'
        })

@api_view(['POST'])
def clean_duplicate_works(request):
    """清理重复和无效的作品数据"""
    try:
        # 记录清理前的状态
        before_count = Work.objects.count()
        logger.info(f"清理前的作品数量: {before_count}")
        
        # 1. 获取所有作品，按名称分组
        works_by_name = {}
        for work in Work.objects.all():
            name = work.name.strip() if work.name else ''
            if name:  # 忽略空名称的作品
                if name not in works_by_name:
                    works_by_name[name] = []
                works_by_name[name].append(work)
        
        # 2. 处理每组重复的作品
        cleaned_works = []
        for name, works in works_by_name.items():
            if len(works) > 1:
                logger.info(f"发现重复作品 '{name}': {len(works)} 个实例")
                
                # 获取每个作品实例的关联数据数量
                work_data = []
                for work in works:
                    article_count = work.articles.count()  # 关联的文章数
                    
                    # 检查Neo4j中的关联数据
                    session = get_graph()
                    char_count = session.run("""
                        MATCH (w:Work {id: $work_id})<-[:BELONGS_TO]-(c:Character)
                        RETURN count(c) as count
                    """, work_id=str(work.id)).single()['count']
                    
                    force_count = session.run("""
                        MATCH (w:Work {id: $work_id})<-[:BELONGS_TO]-(f:Force)
                        RETURN count(f) as count
                    """, work_id=str(work.id)).single()['count']
                    
                    rel_count = session.run("""
                        MATCH (w:Work {id: $work_id})<-[:BELONGS_TO]-(c1:Character)
                        MATCH (c1)-[r]->(c2:Character)-[:BELONGS_TO]->(w)
                        WHERE type(r) <> 'BELONGS_TO'
                        RETURN count(r) as count
                    """, work_id=str(work.id)).single()['count']
                    
                    session.close()
                    
                    total_data = article_count + char_count + force_count + rel_count
                    work_data.append({
                        'work': work,
                        'total_data': total_data,
                        'details': {
                            'articles': article_count,
                            'characters': char_count,
                            'forces': force_count,
                            'relationships': rel_count
                        }
                    })
                    
                    logger.info(f"作品ID {work.id} 的关联数据统计:")
                    logger.info(f"- 文章数: {article_count}")
                    logger.info(f"- 人物数: {char_count}")
                    logger.info(f"- 势力数: {force_count}")
                    logger.info(f"- 关系数: {rel_count}")
                    logger.info(f"- 总数据量: {total_data}")
                
                # 按总数据量排序，保留数据最多的记录
                work_data.sort(key=lambda x: x['total_data'], reverse=True)
                keep_work = work_data[0]['work']
                delete_works = [w['work'] for w in work_data[1:]]
                
                logger.info(f"保留数据最多的作品记录: id={keep_work.id}, 数据量={work_data[0]['total_data']}")
                logger.info(f"数据详情: {work_data[0]['details']}")
                
                # 更新关联的文章到保留的作品
                for work in delete_works:
                    Article.objects.filter(work=work).update(work=keep_work)
                    # 删除重复的作品
                    work.delete()
                    logger.info(f"删除重复作品: id={work.id}, name={work.name}")
                
                cleaned_works.append({
                    'name': name,
                    'kept_id': keep_work.id,
                    'kept_data_count': work_data[0]['total_data'],
                    'kept_details': work_data[0]['details'],
                    'deleted_ids': [w.id for w in delete_works]
                })
        
        # 3. 删除空名称的作品
        empty_works = Work.objects.filter(name__isnull=True) | Work.objects.filter(name='')
        empty_count = empty_works.count()
        empty_ids = list(empty_works.values_list('id', flat=True))
        empty_works.delete()
        logger.info(f"删除空名称作品: {empty_count} 个")
        
        # 记录清理后的状态
        after_count = Work.objects.count()
        logger.info(f"清理后的作品数量: {after_count}")
        
        return JsonResponse({
            'code': 0,
            'message': '重复和无效作品清理完成',
            'data': {
                'before_count': before_count,
                'after_count': after_count,
                'cleaned_works': cleaned_works,
                'empty_works_removed': empty_ids
            }
        })
        
    except Exception as e:
        logger.error(f"清理重复作品失败: {str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'清理失败: {str(e)}'
        })

@api_view(['GET'])
def check_work_data(request):
    """查询所有作品的数据情况"""
    try:
        works_data = []
        
        # 获取所有作品
        works = Work.objects.all().order_by('id')
        logger.info(f"开始检查作品数据，共 {works.count()} 个作品")
        
        for work in works:
            # 获取MySQL中的数据
            article_count = work.articles.count()
            
            # 获取Neo4j中的数据
            session = get_graph()
            
            # 获取人物数量
            char_count = session.run("""
                MATCH (w:Work {id: $work_id})<-[:BELONGS_TO]-(c:Character)
                RETURN count(c) as count
            """, work_id=str(work.id)).single()['count']
            
            # 获取势力数量
            force_count = session.run("""
                MATCH (w:Work {id: $work_id})<-[:BELONGS_TO]-(f:Force)
                RETURN count(f) as count
            """, work_id=str(work.id)).single()['count']
            
            # 获取关系数量
            rel_count = session.run("""
                MATCH (w:Work {id: $work_id})<-[:BELONGS_TO]-(c1:Character)
                MATCH (c1)-[r]->(c2:Character)-[:BELONGS_TO]->(w)
                WHERE type(r) <> 'BELONGS_TO'
                RETURN count(r) as count
            """, work_id=str(work.id)).single()['count']
            
            session.close()
            
            # 汇总数据
            work_info = {
                'id': work.id,
                'name': work.name.strip() if work.name else '',
                'data_counts': {
                    'articles': article_count,
                    'characters': char_count,
                    'forces': force_count,
                    'relationships': rel_count,
                    'total': article_count + char_count + force_count + rel_count
                }
            }
            works_data.append(work_info)
            
            logger.info(f"作品 [{work.id}] {work.name} 的数据统计:")
            logger.info(f"- 文章数: {article_count}")
            logger.info(f"- 人物数: {char_count}")
            logger.info(f"- 势力数: {force_count}")
            logger.info(f"- 关系数: {rel_count}")
            logger.info(f"- 总数据量: {work_info['data_counts']['total']}")
        
        # 按作品名称分组
        works_by_name = {}
        for work in works_data:
            name = work['name']
            if name:  # 忽略空名称
                if name not in works_by_name:
                    works_by_name[name] = []
                works_by_name[name].append(work)
        
        # 分析重复情况
        duplicates = {
            name: works for name, works in works_by_name.items() 
            if len(works) > 1
        }
        
        # 找出空名称的作品
        empty_works = [work for work in works_data if not work['name']]
        
        return JsonResponse({
            'code': 0,
            'message': '作品数据检查完成',
            'data': {
                'all_works': works_data,
                'duplicates': duplicates,
                'empty_works': empty_works,
                'summary': {
                    'total_works': len(works_data),
                    'duplicate_names': len(duplicates),
                    'empty_names': len(empty_works)
                }
            }
        })
        
    except Exception as e:
        logger.error(f"检查作品数据失败: {str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'检查失败: {str(e)}'
        })

@api_view(['POST'])
def sync_works(request):
    """同步MySQL和Neo4j中的作品数据"""
    try:
        # 1. 获取Neo4j中的所有作品
        session = get_graph()
        neo4j_works = session.run("""
            MATCH (w:Work)
            RETURN w.id as id, w.name as name
        """).data()
        
        # 2. 获取MySQL中的所有作品
        mysql_works = Work.objects.all().values('id', 'name')
        
        # 3. 创建映射
        neo4j_work_map = {w['id']: w['name'] for w in neo4j_works}
        mysql_work_map = {str(w['id']): w['name'] for w in mysql_works}
        
        # 4. 找出差异
        neo4j_only = set(neo4j_work_map.keys()) - set(mysql_work_map.keys())
        mysql_only = set(mysql_work_map.keys()) - set(neo4j_work_map.keys())
        common = set(neo4j_work_map.keys()) & set(mysql_work_map.keys())
        
        # 5. 处理差异
        # 5.1 将Neo4j独有的作品添加到MySQL
        for work_id in neo4j_only:
            Work.objects.create(
                id=work_id,
                name=neo4j_work_map[work_id]
            )
            logger.info(f"将Neo4j作品添加到MySQL: id={work_id}, name={neo4j_work_map[work_id]}")
        
        # 5.2 将MySQL独有的作品添加到Neo4j
        for work_id in mysql_only:
            session.run("""
                CREATE (w:Work {id: $id, name: $name})
            """, id=work_id, name=mysql_work_map[work_id])
            logger.info(f"将MySQL作品添加到Neo4j: id={work_id}, name={mysql_work_map[work_id]}")
        
        # 5.3 同步共同作品的名称（以Neo4j为准）
        for work_id in common:
            if neo4j_work_map[work_id] != mysql_work_map[work_id]:
                Work.objects.filter(id=work_id).update(name=neo4j_work_map[work_id])
                logger.info(f"更新MySQL作品名称: id={work_id}, old_name={mysql_work_map[work_id]}, new_name={neo4j_work_map[work_id]}")
        
        session.close()
        
        return JsonResponse({
            'code': 0,
            'message': '作品数据同步完成',
            'data': {
                'neo4j_only_count': len(neo4j_only),
                'mysql_only_count': len(mysql_only),
                'common_count': len(common),
                'neo4j_only': list(neo4j_only),
                'mysql_only': list(mysql_only)
            }
        })
        
    except Exception as e:
        logger.error(f"同步作品数据失败: {str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f"同步失败: {str(e)}"
        })

@api_view(['GET'])
def get_events(request, work_id=None):
    """获取事件列表"""
    try:
        # 从MySQL获取作品列表
        works_list = get_mysql_works()
        
        # 构建事件查询条件
        filters = {}
        if work_id:
            filters['work_id'] = work_id
        
        # 获取事件数据
        events = Event.objects.filter(**filters).values(
            'id', 'name', 'time', 'description', 'location', 'participants'
        )
        
        # 格式化事件数据
        events_list = []
        for event in events:
            event_data = {
                'id': event['id'],
                'title': event['name'],
                'time': event['time'],
                'description': event['description'],
                'location': event['location'],
                'participants': event['participants'].split(',') if event['participants'] else []
            }
            events_list.append(event_data)
        
        logger.info(f"从MySQL获取到 {len(events_list)} 个事件")
        
        return JsonResponse({
            'code': 0,
            'message': 'success',
            'data': {
                'events': events_list,
                'works': works_list
            }
        })
        
    except Exception as e:
        logger.error(f"获取事件列表失败: {str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'获取事件列表失败: {str(e)}'
        })