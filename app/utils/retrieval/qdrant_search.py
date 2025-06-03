from qdrant_client import QdrantClient
from qdrant_client.http import models
from openai import OpenAI
from  dotenv import load_dotenv
load_dotenv()

def qdrant_semantic_search(query, collection_name, qdrant_host="qdrant", qdrant_port=6333, top_k=5):
    # Step 1: Embed the query using OpenAI
    client = OpenAI()
    embedding_response = client.embeddings.create(
        input=query,
        model="text-embedding-3-small"
    )
    query_vector = embedding_response.data[0].embedding
    
    # Step 2: Query Qdrant
    qdrant = QdrantClient(host=qdrant_host, port=qdrant_port)
    hits = qdrant.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=top_k,
        
        
    )
    # Each hit contains .payload (your metadata), .score, .id, etc.
    results = []
    for hit in hits:
        results.append({
            "text": hit.payload.get("text", ""),  # assumes you stored your chunk text as 'text'
            "score": hit.score,
            "payload": hit.payload,
        })
    return results
