from django.http import JsonResponse
from py2neo import Graph
from rest_framework.decorators import api_view
import os

# Neo4j connection configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "root123321"  # 已更新为设置的新密码

def get_graph():
    return Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

@api_view(['GET'])
def get_works(request):
    """获取所有作品列表"""
    try:
        query = """
        MATCH (w:Work)
        RETURN w.id as id, w.name as name
        ORDER BY w.name
        """
        results = get_graph().run(query).data()
        return JsonResponse({
            'code': 0,
            'data': results
        })
    except Exception as e:
        return JsonResponse({
            'code': 1,
            'message': str(e)
        })

@api_view(['GET'])
def get_graph_data(request, work_id):
    """获取特定作品的图谱数据"""
    try:
        # 获取节点
        nodes_query = """
        MATCH (n)
        WHERE n.work_id = $work_id
        RETURN 
            id(n) as id,
            n.name as name,
            labels(n)[0] as category,
            n.description as value,
            CASE labels(n)[0]
                WHEN 'Character' THEN 50
                WHEN 'Force' THEN 40
                ELSE 30
            END as symbolSize
        """
        
        # 获取关系
        links_query = """
        MATCH (n)-[r]->(m)
        WHERE n.work_id = $work_id AND m.work_id = $work_id
        RETURN 
            id(n) as source,
            id(m) as target,
            type(r) as value
        """
        
        nodes = get_graph().run(nodes_query, work_id=work_id).data()
        links = get_graph().run(links_query, work_id=work_id).data()
        
        # 处理节点类别
        for node in nodes:
            node['category'] = 0 if node['category'] == 'Character' else 1
        
        return JsonResponse({
            'code': 0,
            'data': {
                'nodes': nodes,
                'links': links
            }
        })
    except Exception as e:
        return JsonResponse({
            'code': 1,
            'message': str(e)
        })

@api_view(['GET'])
def get_node_details(request, node_id):
    """获取节点详细信息"""
    try:
        query = """
        MATCH (n)
        WHERE id(n) = $node_id
        RETURN n
        """
        result = get_graph().run(query, node_id=int(node_id)).data()
        if result:
            return JsonResponse({
                'code': 0,
                'data': result[0]['n']
            })
        return JsonResponse({
            'code': 1,
            'message': '节点不存在'
        })
    except Exception as e:
        return JsonResponse({
            'code': 1,
            'message': str(e)
        })

@api_view(['GET'])
def get_relationships(request, node_id):
    """获取节点的关系信息"""
    try:
        query = """
        MATCH (n)-[r]-(m)
        WHERE id(n) = $node_id
        RETURN {
            source: m.name,
            description: type(r)
        } as relation
        """
        relations = get_graph().run(query, node_id=int(node_id)).data()
        return JsonResponse({
            'code': 0,
            'data': [r['relation'] for r in relations]
        })
    except Exception as e:
        return JsonResponse({
            'code': 1,
            'message': str(e)
        }) 