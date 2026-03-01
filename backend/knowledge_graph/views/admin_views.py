"""
管理相关的视图模块
包含数据清理、调试、测试等功能
"""
import logging
from django.http import JsonResponse, HttpResponse
from rest_framework.decorators import api_view
from py2neo import Graph
from django.conf import settings

from ..models import Work, Article, Character, Relationship, Event, Faction
from ..services.neo4j_service import Neo4jService

logger = logging.getLogger(__name__)
neo4j_service = Neo4jService()


def get_graph():
    """获取 Neo4j 数据库连接"""
    return Graph(
        settings.NEO4J_CONFIG['uri'],
        auth=settings.NEO4J_CONFIG['auth']
    ).session()


@api_view(['POST'])
def clean_graph_data(request):
    """
    清理知识图谱数据
    
    Returns:
        JsonResponse: 清理结果
    """
    try:
        result = neo4j_service.clean_invalid_nodes()
        
        return JsonResponse({
            'code': 0,
            'message': '图谱数据清理完成',
            'data': {
                'success': result
            }
        })
        
    except Exception as e:
        logger.error(f"清理图谱数据失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'清理失败：{str(e)}'
        })


@api_view(['POST'])
def delete_article(request, article_id):
    """
    删除文章及其相关数据
    
    Args:
        article_id: 文章 ID
        
    Returns:
        JsonResponse: 删除结果
    """
    try:
        article = Article.objects.get(id=article_id)
        article.delete()
        
        neo4j_service.delete_article_data(article_id)
        
        return JsonResponse({
            'code': 0,
            'message': '文章删除成功',
            'data': {
                'article_id': article_id
            }
        })
        
    except Article.DoesNotExist:
        return JsonResponse({
            'code': 1,
            'message': '文章不存在'
        }, status=404)
    except Exception as e:
        logger.error(f"删除文章失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'删除失败：{str(e)}'
        })


@api_view(['POST'])
def clean_test_data(request):
    """
    清理测试数据
    
    Returns:
        JsonResponse: 清理结果
    """
    try:
        session = get_graph()
        try:
            query = """
            MATCH (n)
            WHERE n.test = true
            DETACH DELETE n
            """
            result = session.run(query)
            
            return JsonResponse({
                'code': 0,
                'message': '测试数据清理完成',
                'data': {
                    'deleted': True
                }
            })
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"清理测试数据失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'清理失败：{str(e)}'
        })


@api_view(['GET'])
def test_relationships(request, work_id):
    """
    测试作品关系查询
    
    Args:
        work_id: 作品 ID
        
    Returns:
        JsonResponse: 关系测试结果
    """
    try:
        work = Work.objects.get(id=work_id)
        session = get_graph()
        
        try:
            query = """
            MATCH (w:Work {id: $work_id})<-[:BELONGS_TO]-(c1:Character)
            MATCH (c1)-[r]-(c2:Character)-[:BELONGS_TO]->(w)
            WHERE type(r) <> 'BELONGS_TO'
            RETURN c1.name as source, c2.name as target, type(r) as rel_type, r.description as description
            LIMIT 100
            """
            result = session.run(query, work_id=str(work_id))
            
            relationships = []
            for record in result:
                relationships.append({
                    'source': record['source'],
                    'target': record['target'],
                    'type': record['rel_type'],
                    'description': record['description'] or ''
                })
            
            return JsonResponse({
                'code': 0,
                'message': 'success',
                'data': {
                    'work_name': work.name,
                    'relationships': relationships,
                    'total': len(relationships)
                }
            })
        finally:
            session.close()
            
    except Work.DoesNotExist:
        return JsonResponse({
            'code': 1,
            'message': '作品不存在'
        }, status=404)
    except Exception as e:
        logger.error(f"测试关系查询失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'测试失败：{str(e)}'
        })


@api_view(['GET'])
def debug_database(request):
    """
    调试数据库连接和状态
    
    Returns:
        JsonResponse: 数据库状态信息
    """
    try:
        mysql_status = {
            'connected': True,
            'works_count': Work.objects.count(),
            'articles_count': Article.objects.count(),
            'characters_count': Character.objects.count(),
            'events_count': Event.objects.count(),
            'relationships_count': Relationship.objects.count(),
            'factions_count': Faction.objects.count()
        }
        
        neo4j_status = {'connected': False}
        try:
            session = get_graph()
            try:
                result = session.run("MATCH (n) RETURN count(n) as count").single()
                neo4j_status = {
                    'connected': True,
                    'nodes_count': result['count'] if result else 0
                }
            finally:
                session.close()
            except Exception as e:
                neo4j_status['error'] = str(e)
        except Exception as e:
            neo4j_status['error'] = str(e)
        
        return JsonResponse({
            'code': 0,
            'message': 'success',
            'data': {
                'mysql': mysql_status,
                'neo4j': neo4j_status
            }
        })
        
    except Exception as e:
        logger.error(f"调试数据库失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'调试失败：{str(e)}'
        })


@api_view(['GET'])
def check_relationships(request):
    """
    检查关系数据完整性
    
    Returns:
        JsonResponse: 检查结果
    """
    try:
        relationships = Relationship.objects.select_related(
            'source', 'target', 'work'
        ).all()
        
        issues = []
        for rel in relationships:
            if not rel.source or not rel.target:
                issues.append({
                    'id': rel.id,
                    'issue': 'Missing source or target',
                    'type': rel.type
                })
        
        return JsonResponse({
            'code': 0,
            'message': 'success',
            'data': {
                'total': relationships.count(),
                'issues': issues,
                'issues_count': len(issues)
            }
        })
        
    except Exception as e:
        logger.error(f"检查关系数据失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'检查失败：{str(e)}'
        })


@api_view(['POST'])
def clear_database(request):
    """
    清空数据库 (危险操作)
    
    Returns:
        JsonResponse: 清空结果
    """
    try:
        count = {
            'relationships': Relationship.objects.count(),
            'events': Event.objects.count(),
            'factions': Faction.objects.count(),
            'characters': Character.objects.count(),
            'articles': Article.objects.count(),
            'works': Work.objects.count()
        }
        
        Relationship.objects.all().delete()
        Event.objects.all().delete()
        Faction.objects.all().delete()
        Character.objects.all().delete()
        Article.objects.all().delete()
        Work.objects.all().delete()
        
        logger.warning("数据库已清空")
        
        return JsonResponse({
            'code': 0,
            'message': '数据库已清空',
            'data': {
                'deleted_counts': count
            }
        })
        
    except Exception as e:
        logger.error(f"清空数据库失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'清空失败：{str(e)}'
        })
