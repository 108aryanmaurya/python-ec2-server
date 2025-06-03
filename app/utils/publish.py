from ..queue.q import redis_connection
import json
def publish_video_process_status(user_id, step, details=None):
    status_data = {
        "user_id": user_id,
        "step": step,           # e.g. "queued", "transcribing", "chunking", "indexing_qdrant", "indexing_neo4j", "done"
        "details": details or {}
    }
    redis_connection.publish("video_process_status_channel", json.dumps(status_data))
    
    
    
def publish_query_status(user_id, step, details=None):
    status_data = {
        "user_id": user_id,
        "step": step,           # e.g. "queued", "searching mem0", "searching qdrant", "exracting keywords","searching neo4j", "genearating response", "typing","done"
        "details": details or {}
    }
    redis_connection.publish("query_status_channel", json.dumps(status_data))

def publish_stream(user_id, message_id, content):
    status_data = {
        "user_id": user_id,
                    "message_id": message_id,
                    "chunk": content
    }
    redis_connection.publish("stream_channel", json.dumps(status_data))
    
       