import json, os, yaml
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pandas as pd

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 
warnings.filterwarnings("ignore", category=Warning) 

SCHEMA_FILE = "mongo_schema/mongo_schema.json"
SCHEMA_DOC_FILE = "mongo_schema/mongo_schema_doc.yaml"

FAISS_INDEX = "faiss_mongo_schema"
FAISS_DB = None


EXCEL_FILE = "faiss_mongo_schema/queries_for_rag.xlsx"


def load_schema_into_faiss():
    """YAML şemasını FAISS içine yükler ve örnek sorguları ekler."""
    if os.path.exists(FAISS_INDEX):
        print("\nFAISS index already exists. This process is skipped")
        global FAISS_DB
        print("Loading FAISS schema")
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        FAISS_DB = FAISS.load_local(FAISS_INDEX, embeddings, allow_dangerous_deserialization=True)
        return

    print("Generating FAISS schema")

    print(f"Checking YAML File")
    if not os.path.exists(SCHEMA_DOC_FILE):
        print(f"ERROR: YAML file not found: {SCHEMA_DOC_FILE}. Please ensure you have created the file and it is in the correct path.")
        return

    with open(SCHEMA_DOC_FILE, "r", encoding="utf-8") as f:
        yaml_data = yaml.safe_load(f)

    print(f"YAML Data Loaded")

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    docs = []
    metadata = []


    for entry_number, entry_string in yaml_data.items():
        try:
            entry_dict = yaml.safe_load(entry_string)  
        except yaml.YAMLError as e:
            print(f"ERROR: YAML parsing failed for entry {entry_number}: {e}")
            return

        if isinstance(entry_dict, dict) and entry_dict:
            db_name = entry_dict.get("DBName", "")
            collection_name = entry_dict.get("Collection", "")
            description = entry_dict.get("Description", "")

            enums = entry_dict.get("Enums", {})
            enums_explain = entry_dict.get("EnumsDescription", {})

            enums_str = " | ".join([f"{key}: {', '.join(value)}" for key, value in enums.items()]) if enums else None
            enums_description_str = " | ".join([f"{key}: {value}" for key, value in enums_explain.items()]) if enums_explain else None

            doc_text = f"DBName: {db_name}, Collection: {collection_name}, Description: {description}"
            if enums_str:
                doc_text += f", Enums: {enums_str}"
            if enums_description_str:
                doc_text += f", EnumsDescription: {enums_description_str}"
                docs.append(doc_text)
                meta_entry = {
                    "DBName": db_name,
                    "Collection": collection_name,
                    "Description": description,
                }
                if enums_str:
                    meta_entry["Enums"] = enums_str
                if enums_description_str:
                    meta_entry["EnumsDescription"] = enums_description_str

                metadata.append(meta_entry)

    split_texts = []
    split_metadata = []

    print("Loading schema into FAISS...")
    print("Indexing Schema")

    for i, doc in enumerate(docs):
        split_parts = text_splitter.split_text(doc)
        split_texts.extend(split_parts)
        split_metadata.extend([metadata[i]] * len(split_parts))

    faiss_db = FAISS.from_texts(split_texts, embeddings, metadatas=split_metadata)
    faiss_db.save_local(FAISS_INDEX)

    print("Schema successfully loaded into FAISS.\n")


def get_relevant_schema(user_query, k=5, similarity_threshold=0.5):
    """FAISS veritabanından uygun MongoDB şemalarını ve DB + koleksiyon bilgilerini getirir."""
    print("\nGetting relevant schema for your query...")
    print("\nSearching Schema")

    docs = FAISS_DB.similarity_search_with_score(user_query, k=k)

    if not docs:
        return []

    schema_info_list = []

    for doc, score in docs:
        similarity_score = 1 / (1 + score)  # Skoru normalize et (örn: L2 mesafesini benzerlik yüzdesine çevirmek)
        
        if similarity_score < similarity_threshold:
            continue  

        schema_info = {
            "DBName": doc.metadata["DBName"],
            "Collection": doc.metadata["Collection"],
            "Description": doc.metadata["Description"],
            "Enums": doc.metadata["Enums"],
            "EnumsDescription": doc.metadata["EnumsDescription"],
            "SimilarityScore": similarity_score 
        }

        schema_info_list.append(schema_info)

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
