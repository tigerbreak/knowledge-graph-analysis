from neo4j import GraphDatabase
from django.conf import settings

class Neo4jConnection:
    def __init__(self):
        self._driver = GraphDatabase.driver(
            settings.NEO4J_CONFIG['uri'],
            auth=settings.NEO4J_CONFIG['auth']
        )

    def close(self):
        self._driver.close()

    def create_character(self, character):
        with self._driver.session() as session:
            session.run(
                "MERGE (c:Character {name: $name}) "
                "SET c.alias = $alias, c.description = $description, "
                "c.force = $force, c.birth_death = $birth_death",
                name=character.name,
                alias=character.alias,
                description=character.description,
                force=character.force,
                birth_death=character.birth_death
            )

    def create_relationship(self, relationship):
        with self._driver.session() as session:
            session.run(
                "MATCH (source:Character {name: $source_name}) "
                "MATCH (target:Character {name: $target_name}) "
                "MERGE (source)-[r:RELATES {type: $relation_type}]->(target) "
                "SET r.description = $description",
                source_name=relationship.source.name,
                target_name=relationship.target.name,
                relation_type=relationship.relation_type,
                description=relationship.description
            )

    def get_character_relationships(self, character_name):
        with self._driver.session() as session:
            result = session.run(
                "MATCH (c:Character {name: $name})-[r:RELATES]-(other) "
                "RETURN other.name as name, r.type as type, r.description as description",
                name=character_name
            )
            return [dict(record) for record in result]

    def get_all_relationships(self):
        with self._driver.session() as session:
            result = session.run(
                "MATCH (source:Character)-[r:RELATES]->(target:Character) "
                "RETURN source.name as source, target.name as target, "
                "r.type as type, r.description as description"
            )
            return [dict(record) for record in result] 