import json, os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from source.llm_pipeline import generate_example_queries
from source.text_class import LoadingAnimation
import pandas as pd

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 
warnings.filterwarnings("ignore", category=Warning) 

SCHEMA_FILE = "mongo_schema/mongo_schema.json"
FAISS_INDEX = "faiss_mongo_schema"
EXCEL_FILE = "faiss_mongo_schema/queries_for_rag.xlsx"

FAISS_DB = None


def load_schema_into_faiss(method):
    """MongoDB şemasını FAISS içine yükler ve örnek sorguları ekler."""
    if os.path.exists(FAISS_INDEX):
        print("\nFAISS index already exists. This process is skipped")
        global FAISS_DB 
        loading = LoadingAnimation("Loading FAISS schema")
        loading.start()
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        FAISS_DB = FAISS.load_local(FAISS_INDEX, embeddings, allow_dangerous_deserialization=True)
        loading.stop()
        return
    
    loading = LoadingAnimation("Generating FAISS schema")
    loading.start()

    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        schema_data = json.load(f)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    docs = []
    metadata = []
    
    loading.stop()
    loading = LoadingAnimation("Generating example queries for FAISS schema")
    loading.start()

    for db_name, collections in schema_data.items():
        for collection_name, structure in collections.items():
            doc_text = f"Database: {db_name}, Collection: {collection_name}, Schema: {json.dumps(structure, indent=2)}"
            docs.append(doc_text)
            metadata.append({"database": db_name, "collection": collection_name, "schema": structure, "queries": generate_example_queries(method, db_name, collection_name, structure)})

    split_texts = []
    split_metadata = []
    
    loading.stop()
    print("Loading schema into FAISS...")
    loading = LoadingAnimation("Indexing Schema")
    loading.start()

    for i, doc in enumerate(docs):
        split_parts = text_splitter.split_text(doc)
        split_texts.extend(split_parts)
        split_metadata.extend([metadata[i]] * len(split_parts))

    faiss_db = FAISS.from_texts(split_texts, embeddings, metadatas=split_metadata)
    faiss_db.save_local(FAISS_INDEX)

    loading.stop()
    print("Schema successfully loaded into FAISS.\n")


def get_relevant_schema(user_query, k=5):
    #K bir DB'deki maksimum collection sayısı olabilir
    """FAISS veritabanından uygun MongoDB şemalarını ve DB + koleksiyon bilgilerini getirir."""
    print("\nGetting relevant schema for your query...")
    loading = LoadingAnimation("Searching Schema")

    docs = FAISS_DB.similarity_search_with_score(user_query, k=k)

    if not docs:
        return []

    schema_info_list = [] 

    for doc, _ in docs:
        schema_info = {} 
        schema_info["DBName"] = doc.metadata["database"]
        schema_info["Collection"] = doc.metadata["collection"]

        full_page_content = doc.page_content
        schema_part = full_page_content.split("Schema: ", 1) 

        if len(schema_part) > 1: 
            schema_info["Schema"] = schema_part[1]
        else:
            schema_info["Schema"] = full_page_content 


        schema_info_list.append(schema_info)
            
    loading.stop()
    return schema_info_list

def save_query_to_excel(db_names, collection_names, query):
    db_str = ", ".join(db_names)
    collection_str = ", ".join(collection_names)
    
    new_data = pd.DataFrame([[db_str, collection_str, query]], columns=["DB", "Collections", "Query"])

    if not os.path.exists(EXCEL_FILE):
        new_data.to_excel(EXCEL_FILE, index=False)
    else:
        existing_data = pd.read_excel(EXCEL_FILE)

        if existing_data.empty:
            new_data.to_excel(EXCEL_FILE, index=False)
        else:
            updated_data = pd.concat([existing_data, new_data], ignore_index=True)
            updated_data.to_excel(EXCEL_FILE, index=False)

        print(f"Data save success. Thank you!")
