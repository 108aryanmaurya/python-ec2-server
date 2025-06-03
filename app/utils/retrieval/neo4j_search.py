from neo4j import GraphDatabase

def neo4j_text_search(keywords, neo4j_url="bolt://neo4j:7687", username="neo4j", password="password123", top_k=5):
    driver = GraphDatabase.driver(neo4j_url, auth=(username, password))
    with driver.session() as session:
        # Example: search for transcript chunks mentioning the keyword (case-insensitive)
        cypher = """
        WITH $keywords AS keywords
MATCH (c:TranscriptChunk)
WHERE ANY(kw IN keywords WHERE toLower(c.text) CONTAINS toLower(kw))
RETURN c
LIMIT 10
        """
        results = session.run(cypher, keywords=keywords, top_k=top_k)
        return [r.data() for r in results]
