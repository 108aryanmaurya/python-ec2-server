from fastapi import FastAPI
from fastapi import UploadFile,Path
from uuid import uuid4
import redis.asyncio as aioredis
from .utils.file import save_to_disk
from .db.collections.files import files_collection,FileSchema
from .queue.q import  q
from .queue.workers import  process_file,process_message_job,process_video_indexing_job,query_search,query_response_generation,generate_quiz_question,generate_quiz_answer
from  dotenv import load_dotenv
from bson import ObjectId
from pydantic import BaseModel
import socketio
import json
from .utils.publish import publish_video_process_status,publish_query_status


app = FastAPI() 
import asyncio

valkey = aioredis.from_url("redis://valkey:6379") 

load_dotenv()
@app.get("/")
def hello():
    return {"status": "healthy"}
 
  
@app.post("/upload")
async def upload_file(file: UploadFile):
    db_file=await files_collection.insert_one(
        document=FileSchema(
            name=file.filename,
            status="saving"
        )
    ) 
    file_path = f"/mnt/uploads/{str(db_file.inserted_id)}/{file.filename}"
    await save_to_disk(file=await file.read() , path=file_path)

    q.enqueue(process_file,str(db_file.inserted_id),file_path)
    
    await files_collection.update_one(
        {
        "_id":db_file.inserted_id
        },
        {
            "$set":{
                "status":"queued"
            }
        }
    )
    return {"file_id":str(db_file.inserted_id)}


@app.get("/{id}")
async def get_file_by_id(id:str=Path(...,description="iD of the file")):
                   db_file=await files_collection.find_one({"_id":ObjectId(id)})
                   print(db_file)
                   return {
                      "_id":str(db_file["_id"]),
                      "result":db_file["result"] if "result" in db_file else None,
                      "name":db_file["name"],
                      "status":db_file["status"] ,
                   }
                   
class VideoIndexingRequest(BaseModel):
    course_id: str
    course_name: str
    section_id: str
    section_name: str
    lesson_id: str
    lesson_name: str
    video_id: str
    video_url: str
    user_id:str
                   
@app.post("/index-video")
async def process_video(data:VideoIndexingRequest):
      print(data)
      await sio.emit("video_status", {"step":"API called"}, room=data.user_id)
      q.enqueue(process_video_indexing_job, data)
      publish_video_process_status(data.user_id,step="queued")
      return {"status":"Called API Successfuly"}
      



sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
sio_app = socketio.ASGIApp(sio, other_asgi_app=app)
 
@sio.event
async def join(sid, data):
    user_id = data["user_id"]
    print("Socket Connected", user_id)
    await sio.enter_room(sid, user_id)
    print(f"{sid} joined room {user_id}")

# Handle user message
@sio.event
async def user_message(sid, data):
    user_id = data["user_id"]
    message = data["message"] 
    print("M: Socket Connected", user_id)
    
    print("Socket Message Event", message)
    
    # Enqueue background job with required params
    store_message=await files_collection.insert_one(
        document=FileSchema(
            name=message,
            status="saving",
            user_id=user_id
        )
    ) 
    q.enqueue(process_message_job, message,user_id,str(store_message.inserted_id))
    await sio.emit("ack", {"status": "queued", "messageId":str(store_message.inserted_id)}, room=user_id)

@sio.event
async def user_query(sid, data):
    
    print("Socket Message Event", data)
    store_message=await files_collection.insert_one(
        document=FileSchema(
            name=data["message"],
            status="saving",
            user_id=data["user_id"]
        )
    ) 
    publish_query_status(user_id=data["user_id"],step="Request Queued")
    q.enqueue(query_search, data,str(store_message.inserted_id))
    await sio.emit("ack", {"status": "queued", "messageId":str(store_message.inserted_id)}, room=data["user_id"])


@sio.event
async def response_generation(sid, data):
    
    print("Response Generation", data)
    store_message=await files_collection.insert_one(
        document=FileSchema(
            name=data["message"],
            status="saving",
            user_id=data["user_id"]
        )
    ) 
    publish_query_status(user_id=data["user_id"],step="Request Queued")
    q.enqueue(query_response_generation, data,str(store_message.inserted_id))
    await sio.emit("ack", {"status": "queued", "messageId":str(store_message.inserted_id)}, room=data["user_id"])



@sio.event
async def quiz_question(sid, data):
    
    print("Get quiz question", data)
    
    publish_query_status(user_id=data["user_id"],step="Request Queued")
    q.enqueue(generate_quiz_question, data)
    await sio.emit("ack", {"status": "queued", "messageId":""}, room=data["user_id"])


@sio.event
async def quiz_answer(sid, data):
    
    print("Get quiz answer", data)
    
    publish_query_status(user_id=data["user_id"],step="Request Queued")
    q.enqueue(generate_quiz_answer, data)
    await sio.emit("ack", {"status": "queued", "messageId":""}, room=data["user_id"])




@app.on_event("startup")
async def startup():
    asyncio.create_task(stream_chunks_from_valkey())

async def stream_chunks_from_valkey():
    pubsub = valkey.pubsub()
    await pubsub.subscribe("stream_channel","video_process_status_channel","query_status_channel")
    print("pubsub-----------------------")
    
    async for message in pubsub.listen():
        print("message-----------------------")
        print(message)
        if message["type"] == "message":
            channel = message["channel"] if "channel" in message else None
            data = json.loads(message["data"])
            print("Sending to frontend ")
            print(data)
            user_id = data.get("user_id")
            if channel == b"stream_channel":
                print("Stream Chanel-------------------------")
                await sio.emit("stream", data, room=user_id)
            elif channel == b"video_process_status_channel":
                print("Video Chanel-------------------------")      
                await sio.emit("video_status", data, room=user_id)
            elif channel == b"query_status_channel":
                print("Query Chanel-------------------------")      
                await sio.emit("query_status", data, room=user_id)