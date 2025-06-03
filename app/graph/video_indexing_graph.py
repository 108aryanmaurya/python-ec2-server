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

class CourseInfo(BaseModel):
    course_id: str
    course_name: str

class SectionInfo(BaseModel):
    section_id: str
    section_name: str

class LessonInfo(BaseModel):
    lesson_id: str
    lesson_name: str

class VideoInfo(BaseModel):
    video_id: str
    video_url: str

class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str

class Chunk(BaseModel):
    chunk_id: int
    text: str
    start_time: float
    end_time: float
    topics:List[str]
    lesson_id: str
    lesson_name: str
    section_id: str
    section_name: str
    course_id: str
    course_name: str
    video_url:str

class VideoIndexingState(BaseModel):
    user_id: str
    course_info: CourseInfo
    section_info: SectionInfo
    lesson_info: LessonInfo
    video_info: VideoInfo
    segments: Optional[List[TranscriptSegment]] = None
    chunks: Optional[List[Chunk]] = None
    
    
    
def transcribe_node(state:VideoIndexingState):
        print("Trascribing-----------------------------------------------------")
        segments = transcribe(state.user_id,state.lesson_info.lesson_id, state.video_info.video_url)
        print(segments)
        state.segments = ["segments"]
        print("Transcriving done------------------------------------------")

        return state

def chunk_node(state:VideoIndexingState):
        print("Chunking-----------------------------------------------------")
    
        publish_video_process_status(state.user_id,step="Chunking Segments")
        metadata = {
    "lesson_id": state.lesson_info.lesson_id,
    "lesson_name": state.lesson_info.lesson_name,
    "section_id": state.section_info.section_id,
    "section_name": state.section_info.section_name,
    "course_id": state.course_info.course_id,
    "course_name": state.course_info.course_name,
    "video_url":state.video_info.video_url
}
        chunks=  add_topics_to_chunks(test_chunk,n_topics=5)
        chunks = chunking(state.segments, metadata=metadata, target_words=100, overlap_words=20)
        print(chunks)
        state.chunks = chunks
        print("Done done------------------------------------------")
        
        
    
        return state


def add_topics_to_chunks(chunks, n_topics=5):
    """
    For each chunk in the list, call extract_topics_func(chunk['text']) and
    add the result as chunk['topics'].

    Args:
        chunks: list of dicts, each with at least a 'text' key.
        extract_topics_func: a function that takes (text, n_topics) and returns a list of topics.
        n_topics: number of topics to extract.

    Returns:
        The same list, with each dict now containing a 'topics' key.
    """
    for chunk in chunks:
        topics = extract_topics_gpt(chunk["text"], n_topics=n_topics)
        chunk["topics"] = topics
    return chunks

def qdrant_node(state):
        print("Qdrant ------------------------------------------")
        
        publish_video_process_status(state.user_id,step="Indexing to Qdrant")
        index_chunks_in_qdrant(state.course_info, state.section_info, state.lesson_info, state.video_info, state.chunks)
        print("Qdrant done------------------------------------------")
        return state

def neo4j_node(state):
        print("neo4j------------------------------------------")
    
        publish_video_process_status(state.user_id,step="Indexing to Neo4j")
        index_chunks_in_neo4j(state.course_info, state.section_info, state.lesson_info, state.video_info, state.chunks)
        print("neo4j done------------------------------------------")
        return state

def run_video_indexing_workflow():
    """
    video_indexing_request: an instance of VideoIndexingRequest (pydantic model or dict)
    video_path: local path to downloaded video file
    """
   
    workflow = StateGraph(VideoIndexingState)
    workflow.add_node("transcribe", transcribe_node)
    workflow.add_node("chunk", chunk_node)
    workflow.add_node("qdrant", qdrant_node)
    workflow.add_node("neo4j", neo4j_node)
    workflow.add_edge("transcribe", "chunk")
    workflow.add_edge("chunk", "qdrant")
    workflow.add_edge("qdrant", "neo4j")
    workflow.add_edge("neo4j", END)
    workflow.set_entry_point("transcribe")
    workflow_compiled=workflow.compile()
    return workflow_compiled
