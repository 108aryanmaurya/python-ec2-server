from typing import TypedDict,Optional
from pydantic import Field
from pymongo.asynchronous.collection import AsyncCollection
from ..db import database

class FileSchema(TypedDict):
    name:str=Field(...,description="name of file")
    status:str=Field(...,description="status of file")
    user_id:str=Field(...,description="user od of message")
    result:Optional[str]=Field(None, description="result from ai")
    jd:Optional[str]=Field(None, description="description of job")
    
    
COLLECTION_NAME="files"
files_collection: AsyncCollection =database[COLLECTION_NAME]