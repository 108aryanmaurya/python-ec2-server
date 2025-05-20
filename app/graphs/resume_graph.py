from ..db.collections.files import files_collection
from typing_extensions import TypedDict
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langsmith.wrappers import wrap_openai
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel
import json
from bson import  ObjectId


load_dotenv()

client =OpenAI()


class State(TypedDict):
      id:str
      jd_base64:list
      file_base64:list
      detailed_jd:str
      

def analyse_jd(state:State) -> State:
     jd=state.get("jd","")
     id=state.get("id","")
     jd_base64=state.get("jd_base64","")
     
     
     SYSTEM_PROMPT="""
     You are AI assistant. Your job is to elaborate, analyse the given job description.
     Respond ONLY with a specified JSON oject.
     
     Rules:
 1. Follow the Output JSON Format.
 2. Always perform one step at a time and wait for next input.
 3. Carefully analyse the user query.

For given Job description do following:
- Write job description in details in a manner which is easy to understand.
 
     """
     
     messages=[
         {
             "role":"system","content":SYSTEM_PROMPT
         }
     ]
     messages.append({"role":"user","content":jd})
     document_summary = ""

     for i, b64 in enumerate(jd_base64):
      messages = [
        {"role": "system", "content": "You are analyzing a multi-page document."},
        {"role": "user", "content": [
            # {"type": "image_url", "image_url": {"url": base64_to_data_uri(b64)}},
            {"type": "text", "text": f"This is page {i+1}. Summary so far: {document_summary}"}
        ]}
    ]

      response =client.responses.create(
        model="gpt-4.1",
        messages=messages,
    )

      summary = response.choices[0].message["content"]
    #   document_summary += f"\nPage {i+1}:\n{summary}
    #   state["detailed_jd"]=s
                                 
                                #  )
     
        
     
            
            
            
async def analyse_file(state:State) -> State:
     detaild_jd=state.get("detailed_jd","")
     file_base64=state.get("file_base64","")
     id=state.get("jd","")
     
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
                        "image_url": f"data:image/jpeg;base64,{file_base64[0]}",
                    },
                ],
            }
        ],
    )
    #   images_base64[2]
     print(result)
     await files_collection.update_one({"_id":ObjectId(id)}
                                     ,{"$set":{"status":"processed",
                                               "result":result.output_text} }
                                      )
    
     
    
      
graph_builder = StateGraph(State)      
graph = graph_builder.compile()
      
def call_graph(id:str,jd_base64:str,file_base64:str):
    state = {
        "id": id,
        "jd_base64": jd_base64,
        "file_base64":file_base64,
        "detailed_jd":""
    }
    result = graph.invoke(state)
    print("\nFinal Result:")
    print(result)

call_graph()
