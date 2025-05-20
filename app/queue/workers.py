from ..db.collections.files import files_collection
from pdf2image import convert_from_path
import os
from bson import  ObjectId
from openai import OpenAI
import base64

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
    
    
    
    