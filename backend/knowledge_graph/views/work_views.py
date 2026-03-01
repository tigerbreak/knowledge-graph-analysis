"""
作品相关的视图模块
包含作品列表、图谱数据、同步等功能
"""
import logging
from django.http import JsonResponse
from rest_framework.decorators import api_view
from py2neo import Graph
from django.conf import settings

from ..models import Work, Article, Character, Event, Relationship, Faction
from ..services.neo4j_service import Neo4jService

logger = logging.getLogger(__name__)
neo4j_service = Neo4jService()


def get_graph():
    """获取 Neo4j 数据库连接"""
    return Graph(
        settings.NEO4J_CONFIG['uri'],
        auth=settings.NEO4J_CONFIG['auth']
    ).session()


def get_mysql_works():
    """从 MySQL 获取作品列表"""
    try:
        works = Work.objects.all().values('id', 'name')
        return list(works)
    except Exception as e:
        logger.error(f"获取作品列表失败：{str(e)}", exc_info=True)
        return []


@api_view(['GET'])
def work_list(request):
    """
    获取作品列表及其统计信息
    
    Returns:
        JsonResponse: 作品列表和统计信息
    """
    try:
        works_list = get_mysql_works()
        
        works_data = []
        for work in works_list:
            work_info = {
                'id': work['id'],
                'name': work['name'],
                'article_count': Article.objects.filter(work_id=work['id']).count(),
                'character_count': Character.objects.filter(work_id=work['id']).count(),
                'event_count': Event.objects.filter(work_id=work['id']).count(),
                'relationship_count': Relationship.objects.filter(work_id=work['id']).count()
            }
            works_data.append(work_info)
        
        logger.info(f"获取到 {len(works_data)} 个作品")
        
        return JsonResponse({
            'code': 0,
            'message': 'success',
            'data': {
                'works': works_data,
                'total': len(works_data)
            }
        })
        
    except Exception as e:
        logger.error(f"获取作品列表失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'获取作品列表失败：{str(e)}'
        })


@api_view(['GET'])
def get_work_graph(request, work_id):
    """
    获取指定作品的知识图谱数据
    
    Args:
        work_id: 作品 ID
        
    Returns:
        JsonResponse: 图谱数据 (节点和边)
    """
    try:
        work = Work.objects.get(id=work_id)
        graph_data = neo4j_service.get_graph_data(work.name)
        
        if not graph_data or not graph_data.get('nodes'):
            logger.warning(f"作品 {work.name} 的图谱数据为空")
        
        return JsonResponse({
            'code': 0,
            'message': 'success',
            'data': graph_data or {'nodes': [], 'links': [], 'work_name': work.name}
        })
        
    except Work.DoesNotExist:
        return JsonResponse({
            'code': 1,
            'message': '作品不存在'
        }, status=404)
    except Exception as e:
        logger.error(f"获取作品图谱数据失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'获取图谱数据失败：{str(e)}'
        })


@api_view(['GET'])
def get_graph_data(request, work_id=None):
    """
    获取图谱数据 (支持按作品过滤)
    
    Query Parameters:
        - work_id: 作品 ID (可选)
        
    Returns:
        JsonResponse: 图谱数据
    """
    try:
        if work_id:
            try:
                work = Work.objects.get(id=work_id)
                graph_data = neo4j_service.get_graph_data(work.name)
            except Work.DoesNotExist:
                return JsonResponse({
                    'code': 1,
                    'message': '作品不存在'
                }, status=404)
        else:
            graph_data = neo4j_service.get_graph_data()
        
        return JsonResponse({
            'code': 0,
            'message': 'success',
            'data': graph_data or {'nodes': [], 'links': []}
        })
        
    except Exception as e:
        logger.error(f"获取图谱数据失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'获取图谱数据失败：{str(e)}'
        })


@api_view(['GET'])
def get_node_details(request, node_id):
    """
    获取节点详情
    
    Args:
        node_id: Neo4j 节点 ID
        
    Returns:
        JsonResponse: 节点详情
    """
    try:
        session = get_graph()
        try:
            query = """
            MATCH (n)
            WHERE id(n) = $node_id
            RETURN n
            """
            result = session.run(query, node_id=int(node_id)).single()
            
            if not result:
                return JsonResponse({
                    'code': 1,
                    'message': '节点不存在'
                }, status=404)
            
            node = result['n']
            node_type = list(node.labels)[0] if node.labels else 'Unknown'
            
            node_data = {
                'id': str(node.identity),
                'name': node.get('name', ''),
                'type': node_type.lower(),
                'description': node.get('description', ''),
                'properties': dict(node)
            }
            
            # 获取相关关系
            rel_query = """
            MATCH (n)-[r]-(m)
            WHERE id(n) = $node_id
            RETURN m, type(r) as rel_type, r
            """
            rel_result = session.run(rel_query, node_id=int(node_id))
            
            relationships = []
            for record in rel_result:
                relationships.append({
                    'target_id': str(record['m'].identity),
                    'target_name': record['m'].get('name', ''),
                    'type': record['rel_type'],
                    'description': record['r'].get('description', '') if record['r'] else ''
                })
            
            node_data['relationships'] = relationships
            
            return JsonResponse({
                'code': 0,
                'message': 'success',
                'data': node_data
            })
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"获取节点详情失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'获取节点详情失败：{str(e)}'
        })


@api_view(['POST'])
def sync_works(request):
    """
    同步 MySQL 和 Neo4j 中的作品数据
    
    Returns:
        JsonResponse: 同步结果
    """
    try:
        session = get_graph()
        neo4j_works = session.run("""
            MATCH (w:Work)
            RETURN w.id as id, w.name as name
        """).data()
        
        mysql_works = Work.objects.all().values('id', 'name')
        
        neo4j_work_map = {w['id']: w['name'] for w in neo4j_works}
        mysql_work_map = {str(w['id']): w['name'] for w in mysql_works}
        
        neo4j_only = set(neo4j_work_map.keys()) - set(mysql_work_map.keys())
        mysql_only = set(mysql_work_map.keys()) - set(neo4j_work_map.keys())
        common = set(neo4j_work_map.keys()) & set(mysql_work_map.keys())
        
        for work_id in neo4j_only:
            Work.objects.create(
                id=work_id,
                name=neo4j_work_map[work_id]
            )
            logger.info(f"将 Neo4j 作品添加到 MySQL: id={work_id}, name={neo4j_work_map[work_id]}")
        
        for work_id in mysql_only:
            session.run("""
                CREATE (w:Work {id: $id, name: $name})
            """, id=work_id, name=mysql_work_map[work_id])
            logger.info(f"将 MySQL 作品添加到 Neo4j: id={work_id}, name={mysql_work_map[work_id]}")
        
        for work_id in common:
            if neo4j_work_map[work_id] != mysql_work_map[work_id]:
                Work.objects.filter(id=work_id).update(name=neo4j_work_map[work_id])
                logger.info(f"更新 MySQL 作品名称：id={work_id}, old_name={mysql_work_map[work_id]}, new_name={neo4j_work_map[work_id]}")
        
        session.close()
        
        return JsonResponse({
            'code': 0,
            'message': '作品数据同步完成',
            'data': {
                'neo4j_only_count': len(neo4j_only),
                'mysql_only_count': len(mysql_only),
                'common_count': len(common)
            }
        })
        
    except Exception as e:
        logger.error(f"同步作品数据失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f"同步失败：{str(e)}"
        })


@api_view(['POST'])
def clean_duplicate_works(request):
    """
    清理重复的作品数据
    
    Returns:
        JsonResponse: 清理结果
    """
    try:
        works = Work.objects.all().order_by('id')
        works_by_name = {}
        cleaned_works = []
        
        for work in works:
            name = work.name.strip() if work.name else ''
            if name:
                if name not in works_by_name:
                    works_by_name[name] = work
                else:
                    cleaned_works.append(work.id)
                    work.delete()
            else:
                cleaned_works.append(work.id)
                work.delete()
        
        logger.info(f"清理重复作品：{len(cleaned_works)} 个")
        
        before_count = works.count()
        after_count = Work.objects.count()
        
        return JsonResponse({
            'code': 0,
            'message': '重复作品清理完成',
            'data': {
                'before_count': before_count,
                'after_count': after_count,
                'cleaned_works': cleaned_works
            }
        })
        
    except Exception as e:
        logger.error(f"清理重复作品失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'清理失败：{str(e)}'
        })


@api_view(['GET'])
def check_work_data(request):
    """
    检查所有作品的数据完整性
    
    Returns:
        JsonResponse: 检查结果
    """
    try:
        works_data = []
        works = Work.objects.all().order_by('id')
        
        for work in works:
            article_count = work.articles.count()
            
            session = get_graph()
            try:
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
            finally:
                session.close()
            
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
        
        works_by_name = {}
        for work in works_data:
            name = work['name']
            if name:
                if name not in works_by_name:
                    works_by_name[name] = []
                works_by_name[name].append(work)
        
        duplicates = {name: ws for name, ws in works_by_name.items() if len(ws) > 1}
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
        logger.error(f"检查作品数据失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'检查失败：{str(e)}'
        })
