from langgraph.graph import StateGraph, END
from ..utils.indexing_modules.chunking import chunking
from ..utils.indexing_modules.neo4j_indexing import index_chunks_in_neo4j
from ..utils.indexing_modules.qdrant_indexing import index_chunks_in_qdrant
from ..utils.indexing_modules.transcribe import transcribe
from ..utils.indexing_modules.topic_extraction import extract_topics_gpt
from ..utils.publish import publish_video_process_status 
from pydantic import BaseModel
from typing import List, Optional
from .chunk import test_chunk
from pydantic import BaseModel
from typing import Optional, List

class QueryReposneGeneration(BaseModel):
    user_id: str
    course_id: str
    query: str
    message_id:str
    topics:List[str]
    mem0_result:str
    query_translation:List[str]
    
    
def searchMem0(state:QueryReposneGeneration):
    print("Searching Mem0--------------")
    print("Searching Mem0 Done--------------")
    

def queryTranslation(state:QueryReposneGeneration):
    print("Translating Query--------------")
    print("Translating Query Done--------------")

def extractTopicsFromQuery(state:QueryReposneGeneration):
    print("Topic Extraction Query--------------")
    print("Topic Extraction Done--------------")

def searchQdrantDB(state:QueryReposneGeneration):
    print("Searching QdrantDB--------------")
    print("Searching QdrantDB Done--------------")


def searchNeo4j(state:QueryReposneGeneration):
    print("Searching Neo4j--------------")
    print("Searching Neo4j Done--------------")

def generateResponse(state:QueryReposneGeneration):
    print("Generating Response--------------")
    print("Generating Response Done--------------")

def updateMem0(state:QueryReposneGeneration):
    print("Updating Mem0--------------")
    print("Updating Mem0 Done--------------")
    



def run_query_response_generation_workflow():
        workflow = StateGraph(QueryReposneGeneration)
        workflow.add_node("searchMem0",)
        workflow.add_node("queryTranslation",)
        workflow.add_node("extractTopicsFromQuery",)
        workflow.add_node("searchQdrantDB",)
        workflow.add_node("searchNeo4j",)
        workflow.add_node("generateResponse",)
        workflow.add_node("updateMem0",)    
        
        workflow.add_edge("searchMem0","queryTranslation")
        workflow.add_edge("queryTranslation","extractTopicsFromQuery")
        workflow.add_edge("searchQdrantDB","searchNeo4j")
        workflow.add_edge("generateResponse","updateMem0")
        workflow.add_edge("updateMem0",END)
        
        workflow.set_entry_point("searchMem0")
        
        workflow_compiled=workflow.compile()
        return workflow_compiled