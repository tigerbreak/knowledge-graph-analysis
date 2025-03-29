from py2neo import Graph, Node, Relationship
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class Neo4jService:
    def __init__(self):
        """初始化 Neo4j 连接"""
        try:
            # 从环境变量或设置中获取连接信息
            neo4j_uri = getattr(settings, 'NEO4J_URI', "bolt://localhost:7687")
            neo4j_user = getattr(settings, 'NEO4J_USER', "neo4j")
            neo4j_password = getattr(settings, 'NEO4J_PASSWORD', "root123321")
            
            self.graph = Graph(neo4j_uri, auth=(neo4j_user, neo4j_password))
            logger.info("Neo4j 连接成功")
        except Exception as e:
            logger.error(f"Neo4j 连接失败: {str(e)}")
            raise

    def create_or_update_work(self, work_name):
        """创建或更新作品节点"""
        work_node = Node("Work", name=work_name)
        self.graph.merge(work_node, "Work", "name")
        return work_node

    def create_or_update_character(self, name, description, faction, work_name):
        """创建或更新人物节点"""
        character_node = Node("Character", 
                            name=name,
                            description=description,
                            faction=faction,
                            work=work_name)
        self.graph.merge(character_node, "Character", "name")
        return character_node

    def create_or_update_faction(self, name, description, work_name):
        """创建或更新势力节点"""
        faction_node = Node("Faction",
                          name=name,
                          description=description,
                          work=work_name)
        self.graph.merge(faction_node, "Faction", "name")
        return faction_node

    def create_relationship(self, source_node, target_node, rel_type, description):
        """创建关系"""
        rel = Relationship(source_node, rel_type, target_node, description=description)
        self.graph.merge(rel)

    def import_analysis_result(self, analysis_result):
        """导入分析结果到 Neo4j"""
        try:
            # 创建作品节点
            work_name = analysis_result.get('work_name', '未知作品')
            if not work_name:
                work_name = '未知作品'
                
            work_node = Node("Work", 
                           name=work_name,
                           description=f"《{work_name}》相关人物关系")
            self.graph.merge(work_node, "Work", "name")
            logger.info(f"创建作品节点: {work_name}")

            # 创建势力节点
            faction_nodes = {}
            for faction in analysis_result.get('forces', []):
                if not faction.get('name'):
                    continue
                    
                faction_node = Node("Faction",
                                  name=faction['name'],
                                  description=faction.get('description', ''),
                                  work_name=work_name)
                self.graph.merge(faction_node, "Faction", "name")
                faction_nodes[faction['name']] = faction_node
                logger.info(f"创建势力节点: {faction['name']}")
                
                # 创建势力与作品的关系
                rel = Relationship(faction_node, "BELONGS_TO", work_node)
                rel['description'] = "所属作品"
                self.graph.merge(rel)

            # 创建人物节点
            character_nodes = {}
            for character in analysis_result.get('characters', []):
                if not character.get('name'):
                    continue
                    
                character_node = Node("Character",
                                    name=character['name'],
                                    description=character.get('description', ''),
                                    faction=character.get('faction', ''),
                                    work_name=work_name)
                self.graph.merge(character_node, "Character", "name")
                character_nodes[character['name']] = character_node
                logger.info(f"创建人物节点: {character['name']}")
                
                # 创建人物与作品的关系
                rel = Relationship(character_node, "BELONGS_TO", work_node)
                rel['description'] = "所属作品"
                self.graph.merge(rel)

                # 创建人物与势力的关系
                if character.get('faction') and character['faction'] in faction_nodes:
                    faction_node = faction_nodes[character['faction']]
                    rel = Relationship(character_node, "BELONGS_TO", faction_node)
                    rel['description'] = f"属于{character['faction']}"
                    self.graph.merge(rel)
                    logger.info(f"创建人物-势力关系: {character['name']} -> {character['faction']}")

            # 创建人物关系
            for rel in analysis_result.get('relationships', []):
                if not (rel.get('source') and rel.get('target') and rel.get('type')):
                    continue
                    
                source = character_nodes.get(rel['source'])
                target = character_nodes.get(rel['target'])
                
                if source and target:
                    rel_obj = Relationship(source, rel['type'], target)
                    rel_obj['description'] = rel.get('description', '')
                    self.graph.merge(rel_obj)
                    logger.info(f"创建人物关系: {rel['source']} -> {rel['target']} ({rel['type']})")

            logger.info(f"成功导入作品《{work_name}》的分析结果到 Neo4j")
            return True

        except Exception as e:
            logger.error(f"导入分析结果到 Neo4j 失败: {str(e)}")
            return False

    def get_graph_data(self, work_name=None):
        """获取知识图谱数据"""
        try:
            # 构建基础查询
            if work_name:
                # 如果指定了作品，只获取该作品相关的节点和关系
                query = """
                MATCH (w:Work {name: $work_name})
                WITH w
                
                // 获取所有相关节点(包括人物和势力)
                OPTIONAL MATCH (n)-[:BELONGS_TO]->(w)
                WHERE (n:Character OR n:Faction)
                WITH COLLECT(DISTINCT n) as nodes, w
                
                // 获取所有关系(包括人物-人物和人物-势力)
                OPTIONAL MATCH (n1)-[r]-(n2)
                WHERE (n1)-[:BELONGS_TO]->(w) AND (n2)-[:BELONGS_TO]->(w)
                AND (
                    // 人物-人物关系
                    (n1:Character AND n2:Character)
                    OR 
                    // 人物-势力关系
                    (n1:Character AND n2:Faction)
                    OR
                    (n1:Faction AND n2:Character)
                )
                WITH nodes, COLLECT(DISTINCT {
                    start: n1,
                    end: n2,
                    rel: r,
                    type: type(r)
                }) as relationships
                
                RETURN nodes, relationships, w.name as work_name
                """
                result = self.graph.run(query, work_name=work_name).data()
            else:
                # 获取所有有效的节点和关系
                query = """
                // 获取所有节点
                MATCH (n)
                WHERE (n:Character OR n:Faction)
                AND n.name IS NOT NULL
                WITH COLLECT(DISTINCT n) as nodes
                
                // 获取所有关系
                OPTIONAL MATCH (n1)-[r]-(n2)
                WHERE (n1:Character OR n1:Faction) AND (n2:Character OR n2:Faction)
                AND n1.name IS NOT NULL AND n2.name IS NOT NULL
                AND (
                    // 人物-人物关系
                    (n1:Character AND n2:Character)
                    OR 
                    // 人物-势力关系
                    (n1:Character AND n2:Faction)
                    OR
                    (n1:Faction AND n2:Character)
                )
                WITH nodes, COLLECT(DISTINCT {
                    start: n1,
                    end: n2,
                    rel: r,
                    type: type(r)
                }) as relationships
                
                RETURN nodes, relationships
                """
                result = self.graph.run(query).data()
            
            # 如果没有结果，返回空数据结构
            if not result:
                logger.warning("没有找到任何图谱数据")
                return {
                    'nodes': [],
                    'links': [],
                    'work_name': work_name
                }
            
            nodes = []
            edges = []
            nodes_set = set()  # 用于去重
            
            # 处理节点
            for node in result[0].get('nodes', []) or []:
                if node and node.get('name') and str(node.identity) not in nodes_set:
                    # 获取节点类型
                    node_type = list(node.labels)[0].lower()
                    
                    # 构建节点数据
                    node_data = {
                        'id': str(node.identity),
                        'name': node['name'],
                        'type': node_type,
                        'description': node.get('description', ''),
                        'work_name': node.get('work_name', work_name)
                    }
                    
                    # 如果是人物节点，添加势力信息
                    if node_type == 'character' and node.get('faction'):
                        node_data['faction'] = node['faction']
                        
                    nodes.append(node_data)
                    nodes_set.add(str(node.identity))
                    logger.info(f"添加节点: {node_data['name']} ({node_data['type']})")
            
            # 处理关系
            for rel_data in result[0].get('relationships', []) or []:
                if not rel_data:
                    continue
                    
                start_node = rel_data.get('start')
                end_node = rel_data.get('end')
                rel = rel_data.get('rel')
                rel_type = rel_data.get('type')
                
                if not all([start_node, end_node, rel, rel_type]):
                    continue
                
                if str(start_node.identity) in nodes_set and str(end_node.identity) in nodes_set:
                    edge_data = {
                        'source': str(start_node.identity),
                        'target': str(end_node.identity),
                        'type': rel_type,
                        'description': rel.get('description', '')
                    }
                    edges.append(edge_data)
                    logger.info(f"添加关系: {start_node['name']} -> {end_node['name']} ({rel_type})")
            
            logger.info(f"获取到 {len(nodes)} 个节点和 {len(edges)} 个关系")
            if nodes:
                logger.info(f"节点示例: {nodes[:2]}")
            if edges:
                logger.info(f"关系示例: {edges[:2]}")
            
            return {
                'nodes': nodes,
                'links': edges,
                'work_name': result[0].get('work_name', work_name)
            }
            
        except Exception as e:
            logger.error(f"获取知识图谱数据失败: {str(e)}")
            # 返回空数据结构而不是 None
            return {
                'nodes': [],
                'links': [],
                'work_name': work_name
            }

    def run_query(self, query, parameters=None):
        """执行 Cypher 查询"""
        try:
            return self.graph.run(query, parameters or {})
        except Exception as e:
            logger.error(f"Neo4j 查询失败: {str(e)}")
            raise

    def delete_article_data(self, article_id):
        """删除文章相关的所有数据"""
        try:
            # 首先获取文章节点
            article_node = self.graph.nodes.match("Article", id=article_id).first()
            if not article_node:
                logger.warning(f"未找到文章节点: article_id={article_id}")
                return

            # 获取文章所属的作品
            work_node = list(self.graph.match((article_node, None), "BELONGS_TO"))[0].end_node
            
            # 删除文章的所有关系和节点
            query = """
            MATCH (a:Article {id: $article_id})
            OPTIONAL MATCH (a)-[r]-()
            DELETE a, r
            """
            self.graph.run(query, article_id=article_id)
            
            # 检查作品是否还有其他文章
            article_count = len(list(self.graph.match((None, work_node), "BELONGS_TO").where("startNode:Article")))
            
            if article_count == 0:
                # 如果作品没有其他文章了，删除作品相关的所有数据
                query = """
                MATCH (w:Work {id: $work_id})
                OPTIONAL MATCH (n)-[r]-()
                WHERE (n)-[:BELONGS_TO]->(w)
                DELETE n, r, w
                """
                self.graph.run(query, work_id=work_node['id'])
                logger.info(f"删除作品数据: work_id={work_node['id']}")
            
            logger.info(f"删除文章数据完成: article_id={article_id}")
        except Exception as e:
            logger.error(f"删除文章数据失败: {str(e)}")
            raise

    def clean_test_data(self, keep_article_id):
        """清理测试数据，保留指定的文章"""
        try:
            query = """
            MATCH (n)
            WHERE NOT (n:Article AND n.id = $keep_article_id)
            AND NOT EXISTS((n)<-[:BELONGS_TO]-(:Article {id: $keep_article_id}))
            DETACH DELETE n
            """
            self.graph.run(query, keep_article_id=str(keep_article_id))
            logger.info(f"清理测试数据完成，保留文章: {keep_article_id}")
        except Exception as e:
            logger.error(f"清理测试数据失败: {str(e)}")
            raise

    def clean_invalid_nodes(self):
        """清理无效的节点"""
        try:
            # 首先删除所有关系
            query = """
            MATCH ()-[r]-()
            DELETE r
            """
            self.graph.run(query)
            logger.info("清理所有关系完成")

            # 删除所有节点
            query = """
            MATCH (n)
            DELETE n
            """
            self.graph.run(query)
            logger.info("清理所有节点完成")

            # 验证清理结果
            query = """
            MATCH (n)
            RETURN count(n) as node_count
            """
            result = self.graph.run(query).data()
            node_count = result[0]['node_count'] if result else 0
            logger.info(f"数据库中剩余节点数量: {node_count}")

            return True
        except Exception as e:
            logger.error(f"清理节点失败: {str(e)}")
            raise

    def check_work_data(self, work_id):
        """检查作品的数据完整性"""
        try:
            # 检查作品节点及其关联的数据
            query = """
            MATCH (w:Work {id: $work_id})
            OPTIONAL MATCH (n)-[:BELONGS_TO]->(w)
            RETURN w.name as work_name,
                   count(DISTINCT n) as related_nodes
            """
            result = self.graph.run(query, work_id=str(work_id)).data()
            if result:
                logger.info(f"作品数据检查: {result[0]}")
            return result
        except Exception as e:
            logger.error(f"检查作品数据失败: {str(e)}")
            raise

    def create_or_update_character_relationships(self, work_id, article_id, characters, relationships):
        """创建或更新人物关系"""
        # 创建势力节点和关系
        for character in characters:
            if character.get('faction'):
                # 创建势力节点
                force_query = """
                MERGE (f:Force {name: $faction, work_id: $work_id})
                ON CREATE SET f.type = 'force', f.description = '未知势力'
                RETURN f
                """
                self.graph.run(force_query, faction=character['faction'], work_id=work_id)
                
                # 创建人物与势力的关系
                belongs_query = """
                MATCH (c:Character {name: $char_name, work_id: $work_id})
                MATCH (f:Force {name: $faction, work_id: $work_id})
                MERGE (c)-[r:BELONGS_TO]->(f)
                ON CREATE SET r.description = $description
                """
                description = f"{character['name']}属于{character['faction']}"
                self.graph.run(belongs_query, 
                         char_name=character['name'],
                         faction=character['faction'],
                         work_id=work_id,
                         description=description)

        # 创建人物之间的关系
        for rel in relationships:
            query = """
            MATCH (c1:Character {name: $source, work_id: $work_id})
            MATCH (c2:Character {name: $target, work_id: $work_id})
            MERGE (c1)-[r:%s]->(c2)
            ON CREATE SET r.description = $description
            """ % rel['type']
            
            self.graph.run(query, 
                     source=rel['source'],
                     target=rel['target'],
                     work_id=work_id,
                     description=rel['description'])
        
        return True 