import json
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

SCHEMA_FILE = "mongo_schema.json"
FAISS_INDEX = "faiss_mongo_schema"

def load_schema_into_faiss():
    """MongoDB şemasını FAISS içine yükler."""
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        schema_data = json.load(f)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    docs = []
    metadata = []

    for db_name, collections in schema_data.items():
        for collection_name, structure in collections.items():
            doc_text = f"Database: {db_name}, Collection: {collection_name}, Schema: {json.dumps(structure, indent=2)}"
            docs.append(doc_text)
            metadata.append({"database": db_name, "collection": collection_name})

    split_texts = []
    split_metadata = []

    for i, doc in enumerate(docs):
        split_parts = text_splitter.split_text(doc)
        split_texts.extend(split_parts)
        split_metadata.extend([metadata[i]] * len(split_parts))

    faiss_db = FAISS.from_texts(split_texts, embeddings, metadatas=split_metadata)
    faiss_db.save_local(FAISS_INDEX)

def get_relevant_schema(user_query, k=10):
    """FAISS veritabanından uygun MongoDB şemalarını ve DB + koleksiyon bilgilerini getirir."""
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    faiss_db = FAISS.load_local(FAISS_INDEX, embeddings, allow_dangerous_deserialization=True)

    docs = faiss_db.similarity_search_with_score(user_query, k=k)

    if not docs:
        return None, None, None

    matched_schemas = []
    matched_dbs = []
    matched_collections = []

    for doc, _ in docs:
        matched_schemas.append(doc.page_content)
        matched_dbs.append(doc.metadata["database"])
        matched_collections.append(doc.metadata["collection"])

    return matched_schemas, matched_dbs, matched_collections
