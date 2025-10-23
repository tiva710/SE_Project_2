from neo4j import GraphDatabase

# Replace with your actual credentials and AuraDB connection URI
uri = "neo4j+s://your-database.databases.neo4j.io"
username = "neo4j"
password = "your_password"

driver = GraphDatabase.driver(uri, auth=(username, password))

def create_entity(tx, entity):
    query = f"""
    MERGE (n:{entity['type']} {{name: $name}})
    RETURN n
    """
    tx.run(query, name=entity['name'])

def create_relationship(tx, rel):
    query = f"""
    MATCH (a {{name: $source}}), (b {{name: $target}})
    MERGE (a)-[r:{rel['type']}]->(b)
    RETURN r
    """
    tx.run(query, source=rel['source'], target=rel['target'])

def add_entities_and_relationships(entities, relationships):
    with driver.session() as session:
        for e in entities:
            # assuming e is a dict or has dict() method
            entity_data = e.dict() if hasattr(e, 'dict') else e
            session.execute_write(create_entity, entity_data)
        for r in relationships:
            rel_data = r.dict() if hasattr(r, 'dict') else r
            session.execute_write(create_relationship, rel_data)
