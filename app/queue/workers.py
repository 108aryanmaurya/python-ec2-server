from mem0 import Memory
from ..db.collections.files import files_collection
import socketio
from pdf2image import convert_from_path
from ..graph.video_indexing_graph import run_video_indexing_workflow  # assuming 'workflow' is your LangGraph StateGraph
from ..graph.query_response_generation import run_query_response_generation_workflow  # assuming 'workflow' is your LangGraph StateGraph
import os
from bson import  ObjectId
from openai import OpenAI
import base64
import json
from  dotenv import load_dotenv
load_dotenv()
client =OpenAI()
from .q import redis_connection
from ..utils.publish import publish_video_process_status,publish_query_status,publish_stream
from ..utils.retrieval.qdrant_search import qdrant_semantic_search
from ..utils.indexing_modules.topic_extraction import extract_topics_gpt
from ..utils.indexing_modules.similar_question_generation import generate_similar_questions_gpt
from ..utils.retrieval.neo4j_search import neo4j_text_search

sio_client = socketio.Client()
def encode_image(image_path): 
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


async def process_file(id:str,file_path:str):
    await files_collection.update_one({"_id":ObjectId(id)}
                                     ,{"$set":{"status":"processing"} }
                                      )
    print("I am processing file")
    pages=convert_from_path(file_path)
    images=[]
    for i,page in enumerate(pages):
        image_save_path=f"/mnt/uploads/images/{id}/images-{i}.jpg"
        os.makedirs(os.path.dirname(image_save_path), exist_ok=True)
        images.append(image_save_path)
        page.save(image_save_path,"JPEG")
        
    await files_collection.update_one({"_id":id},{
        "$set":{
            "status":"converting to images success"
        }
    })
    print("Imag saved sucess")
    images_base64=[encode_image(img) for img in images ]
    result = client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text",
                        "text": "Based on the resume below, Roast this resume"},
                    {
                        # flake8: noqa
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{images_base64[0]}",
                    },
                ],
            }
        ],
    )
    
    print(result)
    await files_collection.update_one({"_id":ObjectId(id)}
                                     ,{"$set":{"status":"processed",
                                               "result":result.output_text} }
                                      )
    
    
    
    
    
async def process_message_job(message: str, user_id: str, message_id: str):
    print("content generation start ---------------------------")
    print(message_id)
    stream = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": message}],
        stream=True
    )

    full_output = ""
    for chunk in stream:
        delta = chunk.choices[0].delta
        content = getattr(delta, "content", "")
        print(content)
        if content:
            full_output += content
            # Optional: store partial stream (for real-time polling)
            data = {
            "user_id": user_id,
            "message_id": message_id,
            "chunk": content
        }
            redis_connection.publish("stream_channel", json.dumps(data))
    print(full_output)
    await files_collection.update_one(
        {"_id": ObjectId(message_id)},
        {"$set": {"status": "done", "result": full_output}}
    )
    print("content generation Done ---------------------------")


async def process_video_indexing_job(data ):
    print("Stasritng job----------------------------")
    
     # Prepare hierarchical metadata as dicts for state
    state = {
        "user_id":data.user_id,
        "course_info": {
            "course_id": data.course_id,
            "course_name": data.course_name,
        },
        "section_info": {
            "section_id": data.section_id,
            "section_name": data.section_name,
        },
        "lesson_info": {
            "lesson_id": data.lesson_id,
            "lesson_name": data.lesson_name,
        },
        "video_info": {
            "video_id": data.video_id,
            "video_url": data.video_url,
        }
        # 'segments' and 'chunks' will be added by the workflow
    }

    workflow = run_video_indexing_workflow()
    workflow.stream(state)
    for event in run_video_indexing_workflow().stream(state, stream_mode="values"):
                if 'messages' in event:
                  event['messages'][-1].pretty_print()
                  print("From Stream")
    print("job Done----------------------------")
    
    publish_video_process_status(data.user_id,step="transcripting to text")



            
async def query_response_generation(data, message_id: str):
    print("Starting job query response generation----------------------------")
    
    state={
        "user_id":data.user_id,
        "course_id":data.course_id,
        "message":data.message
    }
    workflow = run_query_response_generation_workflow()
    workflow.stream(state)
    for event in run_query_response_generation_workflow().stream(state, stream_mode="values"):
                if 'messages' in event:
                  event['messages'][-1].pretty_print()
                  print("From Stream")
    print("Job Done----------------------------")


    
    
async def query_search(data, message_id: str):
    try:
        print(data)
        OPENAI_API_KEY = "sk-..."

        QUADRANT_HOST = "qdrant"

        NEO4J_URL = "bolt://neo4j:7687"
        NEO4J_USERNAME = "neo4j"
        NEO4J_PASSWORD = "password123"

        config = {
            "version": "v1.1",
            "embedder": {
                "provider": "openai",
                "config": {"api_key":  OPENAI_API_KEY, "model": "text-embedding-3-small"},
            },
            "llm": {"provider": "openai", "config": {"api_key": OPENAI_API_KEY, "model": "gpt-4.1"}},
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "host": QUADRANT_HOST,
                    "port": 6333,
                },
            },
            "graph_store": {
                "provider": "neo4j",
                "config": {"url": NEO4J_URL, "username": NEO4J_USERNAME, "password": NEO4J_PASSWORD},
            },
        }
        print("ANALYSIS START----------------------------------------------------")
        publish_query_status(user_id=data["user_id"], step="Analysis Query")

        mem_client = Memory.from_config(config)
        questions = generate_similar_questions_gpt(data["message"])
        questions_str = "\n".join(questions)+ "\n"+data["message"]
        print("ANALYSIS END----------------------------------------------------")

        print(questions_str)
        print("MEMORY START----------------------------------------------------")
        publish_query_status(user_id=data["user_id"], step="Searching mem0")
        
        mem_result = mem_client.search(query=questions_str, user_id=data["user_id"])

        print("mem_result", mem_result)

        memories = "\n".join([m["memory"] for m in mem_result.get("results")])

        print(f"\n\nMEMORY:\n\n{memories}\n\n")
        print("MEMORY DONE----------------------------------------------------")
        # Qdrant
        publish_query_status(user_id=data["user_id"], step="Searching qdrant")

        qdrant_results = qdrant_semantic_search(
            query=questions_str,
            collection_name=data["course_id"],
            qdrant_host="qdrant",  # Or your container name/IP
            qdrant_port=6333,
            top_k=5
        )

        # Neo4j
        publish_query_status(user_id=data["user_id"], step="Extracting keywords from query")
        topics = extract_topics_gpt(questions_str, n_topics=5)
        print("Topics: ", topics)
        publish_query_status(user_id=data["user_id"], step="Searching neo4j")

        neo4j_results = neo4j_text_search(
            keywords=topics,
            neo4j_url="bolt://neo4j:7687",  # Or docker network address
            username="neo4j",
            password="password123",
            top_k=5
        )

        # Combine/aggregate as needed for your RAG pipeline!
        print("Qdrant Results:", qdrant_results)
        print("Neo4j Results:", neo4j_results)
        publish_query_status(user_id=data["user_id"], step="Generating Resposne")

        SYSTEM_PROMPT = f"""
            You are a helpful AI tutor, an advanced AI designed to
            systematically analyze input content. Your primary function is resolving user query under given information 
            and knowledge preservation with contextual awareness.
            
            Tone: Friendly teacher, Chill, Caring, Helpful.

            Output Format:
            Your response should be in Strictly Markdown Format 
            - Use Headers and sub-headers to reposnse .
            - use proper spacing.
            - Try to keep repsonse in pointers.
            - Give Real-world analogy if fits to context.
            - Use Emojis, diffenrent fonts, bold texts, tables if necessary.
            - If there are references for the response give it like Section name > Lesson Name > video start_time - end_time .
            - If there are Multiple Question in user query start each question's resposne  with a header. 

            Other rules:
            If no sufficent-content is found  response with somthing like this course doesn't cover this topic.  
            If name of user is present in Memory start resposne with user's name.
            if user asks for any code snippet provide it in Javascript or preffered programming langauage  Markdown Format. 
            
            
            User Data from Memory:
            {memories }
            
            Content for Response generation:
            {qdrant_results," ", neo4j_results}
        """
        messages = [
            { "role": "system", "content": SYSTEM_PROMPT },
            { "role": "user", "content": data["message"] }
        ]

        publish_query_status(user_id=data["user_id"], step="Typing")
        
        stream = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            stream=True
        )

        full_output = ""
        for chunk in stream:
            delta = chunk.choices[0].delta
            content = getattr(delta, "content", "")
            print(content)
            if content:
                full_output += content
                publish_stream(user_id=data["user_id"], message_id=message_id, content=content)

        print(full_output)
        publish_query_status(user_id=data["user_id"], step="Done")
        
        await files_collection.update_one(
            {"_id": ObjectId(message_id)},
            {"$set": {"status": "done", "result": full_output}}
        )
        print("content generation Done ---------------------------")
        
        mem_client.add(messages, user_id=data["user_id"])

    except Exception as e:
        print("ERROR in query_search:", e)
        # Publish error status
        publish_query_status(user_id=data["user_id"], step=f"Error in generating response: {str(e)}")
        # Optionally: log or update DB to reflect error
        await files_collection.update_one(
            {"_id": ObjectId(message_id)},
            {"$set": {"status": "error", "error_message": str(e)}}
        )

            

def generate_quiz_question(data):
    
    pass

def generate_quiz_answer(data):
    
    pass