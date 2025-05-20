from ..db.collections.files import files_collection
from pdf2image import convert_from_path
import os
from bson import  ObjectId
from openai import OpenAI
import base64
from ..graphs.resume_graph import call_graph

client =OpenAI()


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
                        "image_url": f"data:image/jpeg;base64,{images_base64[2]}",
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
    
    
    
    
    

async def proccess_file_with_jd(id:str,file_path:str,jd_path:str):
            await files_collection.update_one({"_id":ObjectId(id)}
                                     ,{"$set":{"status":"processing"} }
                                      )
            print("I am processing file")
            file_pages=convert_from_path(file_path)
            jd_pages=convert_from_path(jd_path)
            file_images=[]
            jd_images=[]
            for i,page in enumerate(file_pages):
                image_save_path=f"/mnt/uploads/images/{id}/file-images-{i}.jpg"
                os.makedirs(os.path.dirname(image_save_path), exist_ok=True)
                file_images.append(image_save_path)
                page.save(image_save_path,"JPEG")
             
            for i,page in enumerate(jd_pages):
                image_save_path=f"/mnt/uploads/images/{id}/jd-images-{i}.jpg"
                os.makedirs(os.path.dirname(image_save_path), exist_ok=True)
                jd_images.append(image_save_path)
                page.save(image_save_path,"JPEG")
                
            await files_collection.update_one({"_id":id},{
                "$set":{
                    "status":"converting to images success"
                }
            })
            print("Imag saved sucess")
            file_images_base64=[encode_image(img) for img in file_images ]
            jd_images_base64=[encode_image(img) for img in jd_images ]
            
            call_graph(id,jd_images_base64,file_images_base64)            
            
            
            

            