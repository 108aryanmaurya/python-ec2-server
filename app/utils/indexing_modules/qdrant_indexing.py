from langchain_qdrant import QdrantVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain.docstore.document import Document
from dotenv import load_dotenv

load_dotenv() 


def index_chunks_in_qdrant(course_info, section_info, lesson_info, video_info, chunks):
    collection_name = course_info.course_id  # One collection per course

    # Create collection if not exists
    # if not qdrant.collection_exists(collection_name=collection_name):
    #     qdrant.recreate_collection(collection_name=collection_name, vector_size=1536, distance="Cosine")

    embedder = OpenAIEmbeddings(
        model="text-embedding-3-small",
            )
    

    # 2. Prepare chunk(s) as Document objects (LangChain format)
    docs = []
    for chunk in chunks:
        # Extract text and the rest as metadata
        if hasattr(chunk, "dict"):
            chunk_dict = chunk.dict()
        elif hasattr(chunk, "_asdict"):  # namedtuple
            chunk_dict = chunk._asdict()
        else:
            chunk_dict = dict(chunk)
        # Separate text from metadata
        text = chunk_dict["text"]
        metadata = {k: v for k, v in chunk_dict.items() if k != "text"}
        print(metadata)
        # Prepare Document object (for Qdrant/Langchain)
        docs.append(Document(page_content=text, metadata=metadata))

    # 3. Connect to Qdrant
    print(docs)
    vector_store = QdrantVectorStore.from_documents(
        documents=[],
        collection_name=collection_name,
        url="http://qdrant:6333",
        embedding=embedder
        )
    vector_store.add_documents(documents=docs)
    print("Done injection")
    print("No documents to index!")

