import os
import json
from generate_mongo_schema import extract_mongo_schema
from rag import load_schema_into_faiss, get_relevant_schema
from process import generate_mongo_query_local, generate_mongo_query_gemini
from query_execute import execute_dynamic_mongo_query, clear_mongo_query

SCHEMA_FILE = "mongo_schema.json"
CONNECTION_STRING = "mongodb+srv://noreplyemotion4u:45kVomOnb38h3VFU@emotion4u-basecluster.5gbds.mongodb.net/admin?retryWrites=true&loadBalanced=false&replicaSet=atlas-xp4kqi-shard-0&readPreference=primary&srvServiceName=mongodb&connectTimeoutMS=10000&authSource=admin&authMechanism=SCRAM-SHA-1"

# Şema yoksa oluştur
if not os.path.exists(SCHEMA_FILE):
    print("Schema file not found. Generating schema...")
    extract_mongo_schema(CONNECTION_STRING)

print("Loading schema into FAISS...")
load_schema_into_faiss()

while True:
    user_query = input("\nQuery (write 'exit' for exit): ")
    if user_query.lower() == "exit":
        break

    schema_text, db_name, collection_name = get_relevant_schema(user_query)
    
    if not schema_text or not db_name or not collection_name:
        print("No suitable schema found!")
        continue

    #mongo_query = clear_mongo_query(generate_mongo_query_local(user_query, schema_text))
    mongo_query = clear_mongo_query(generate_mongo_query_gemini(user_query, schema_text))

    if(mongo_query == None):
        print("MongoDB Query parse error")
        continue
    else:
        print(f"\nMongoDB Query:\n{mongo_query}")

    result = execute_dynamic_mongo_query(CONNECTION_STRING, mongo_query, db_name, collection_name)

    print("\nQuery Result:\n")
    print(result)
