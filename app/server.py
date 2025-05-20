from fastapi import FastAPI
from fastapi import UploadFile,Path
from uuid import uuid4
from .utils.file import save_to_disk
from .db.collections.files import files_collection,FileSchema
from .queue.q import  q
from .queue.workers import  process_file,proccess_file_with_jd
from bson import ObjectId
app = FastAPI() 


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
                   
                   
@app.post("/analyse-resume-with-jd")
async def upload_file(file: UploadFile, jd:UploadFile):
    db_file=await files_collection.insert_one(
        document=FileSchema(
            name=file.filename,
            jd_name=jd.filename,
            status="saving",
            jd=jd
        )
    ) 
    file_path = f"/mnt/uploads/{str(db_file.inserted_id)}/{file.filename}"
    jd_path = f"/mnt/uploads/{str(db_file.inserted_id)}/{jd.filename}"
    await save_to_disk(file=await file.read() , path=file_path)
    await save_to_disk(file=await jd.read() , path=jd_path)

    q.enqueue(proccess_file_with_jd,str(db_file.inserted_id),file_path,jd_path)

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

                    