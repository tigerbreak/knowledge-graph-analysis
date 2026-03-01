"""
人物相关的视图模块
包含人物列表、详情、关系查询等功能
"""
import logging
from django.http import JsonResponse
from rest_framework.decorators import api_view

from ..models import Character, Relationship, Work
from ..services.neo4j_service import Neo4jService

logger = logging.getLogger(__name__)
neo4j_service = Neo4jService()


def get_graph():
    """获取 Neo4j 数据库连接"""
    from ..views import get_graph as get_neo4j_session
    return get_neo4j_session()


def get_neo4j_works():
    """从 Neo4j 获取作品列表"""
    try:
        session = get_graph()
        works = session.run("""
            MATCH (w:Work)
            RETURN w.id as id, w.name as name
        """).data()
        session.close()
        return list(works)
    except Exception as e:
        logger.error(f"获取 Neo4j 作品列表失败：{str(e)}")
        return []


@api_view(['GET'])
def character_details(request):
    """
    获取人物详情
    
    Query Parameters:
        - work_id: 作品 ID (可选)
        - character_name: 人物名称搜索关键词 (可选)
        
    Returns:
        JsonResponse: 人物列表和作品列表
    """
    try:
        work_id = request.GET.get('work_id')
        character_name = request.GET.get('character_name')

        logger.info(f"获取人物详情请求参数：work_id={work_id}, character_name={character_name}")

        works_list = get_neo4j_works()
        session = get_graph()
        
        try:
            if work_id:
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

            characters_list = []
            for record in char_results:
                character = {
                    'name': record['name'],
                    'description': record['description'] or '',
                    'faction': record['faction'] or '',
                    'force': record['faction'] or '',
                    'work_name': record.get('work_name', '')
                }
                logger.info(f"获取到人物数据：{character}")
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
        logger.error(f"获取人物详情失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'获取人物详情失败：{str(e)}'
        })


@api_view(['GET'])
def character_relationships(request, character_name):
    """
    获取人物的关系网络
    
    Args:
        character_name: 人物名称
        
    Query Parameters:
        - work_id: 作品 ID (可选)
        
    Returns:
        JsonResponse: 关系网络数据
    """
    try:
        work_id = request.GET.get('work_id')
        session = get_graph()
        
        try:
            if work_id:
                query = """
                MATCH (c:Character {name: $character_name})-[:BELONGS_TO]->(w:Work {id: $work_id})
                OPTIONAL MATCH (c)-[r]-(other:Character)-[:BELONGS_TO]->(w)
                WHERE type(r) <> 'BELONGS_TO'
                RETURN c, other, r, type(r) as rel_type
                UNION
                MATCH (c:Character {name: $character_name})-[:BELONGS_TO]->(w:Work {id: $work_id})
                OPTIONAL MATCH (c)-[r]->(f:Faction)-[:BELONGS_TO]->(w)
                RETURN c, f as other, r, type(r) as rel_type
                """
                result = session.run(query, character_name=character_name, work_id=str(work_id))
            else:
                query = """
                MATCH (c:Character {name: $character_name})
                OPTIONAL MATCH (c)-[r]-(other)
                WHERE type(r) <> 'BELONGS_TO'
                RETURN c, other, r, type(r) as rel_type
                """
                result = session.run(query, character_name=character_name)
            
            relationships = []
            for record in result:
                relationships.append({
                    'source': record['c']['name'],
                    'target': record['other']['name'],
                    'type': record['rel_type'],
                    'description': record['r'].get('description', '') if record['r'] else ''
                })
            
            return JsonResponse({
                'code': 0,
                'message': 'success',
                'data': {
                    'character': character_name,
                    'relationships': relationships,
                    'total': len(relationships)
                }
            })
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"获取人物关系失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'获取人物关系失败：{str(e)}'
        })


@api_view(['GET'])
def character_list(request):
    """
    获取人物列表
    
    Query Parameters:
        - work_id: 作品 ID (可选)
        - search: 搜索关键词 (可选)
        
    Returns:
        JsonResponse: 人物列表
    """
    try:
        work_id = request.GET.get('work_id')
        search = request.GET.get('search', '')
        
        filters = {}
        if work_id:
            filters['work_id'] = work_id
        if search:
            filters['name__icontains'] = search
        
        characters = Character.objects.filter(**filters).select_related('work').order_by('name')
        
        characters_data = []
        for char in characters:
            characters_data.append({
                'id': char.id,
                'name': char.name,
                'description': char.description or '',
                'faction': char.faction or '',
                'work_id': char.work.id if char.work else None,
                'work_name': char.work.name if char.work else ''
            })
        
        return JsonResponse({
            'code': 0,
            'message': 'success',
            'data': {
                'characters': characters_data,
                'total': len(characters_data)
            }
        })
        
    except Exception as e:
        logger.error(f"获取人物列表失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'获取人物列表失败：{str(e)}'
        })
