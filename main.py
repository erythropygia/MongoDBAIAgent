import os
import json
import argparse
import time
import sys
from generate_mongo_schema import extract_mongo_schema
from rag import load_schema_into_faiss, get_relevant_schema
from process import select_generate_method
from query_execute import execute_dynamic_mongo_query, clear_mongo_query

def print_loading_message():
    chars = ['/', '-', '\\', '|']
    for _ in range(120): 
        for char in chars:
            print(f"Generating schema {char}", end="\r")
            time.sleep(0.2)

# Argümanları almak için argparse kullanıyoruz
parser = argparse.ArgumentParser(description="MongoDB Connection String and Query Type")
parser.add_argument('--connection-string', type=str, required=True, help="MongoDB Connection String")
parser.add_argument('--query-type', type=int, choices=[0, 1], required=True, help="Specify query type: 'local(0)' or 'gemini(1)'")
args = parser.parse_args()

CONNECTION_STRING = args.connection_string
QUERY_TYPE = args.query_type
SCHEMA_FILE = "mongo_schema.json"

if not os.path.exists(SCHEMA_FILE):
    print("DB Schema file not found. Generating schema...")
    print_loading_message()
    extract_mongo_schema(CONNECTION_STRING)

print("Loading schema into FAISS...")
load_schema_into_faiss()

while True:
    user_query = input("\nQuery (write 'exit' for exit): ")
    if user_query.lower() == "exit":
        break

    print("Getting relevant schema for the query...")
    schema_text, db_name, collection_name = get_relevant_schema(user_query)
    
    if not schema_text or not db_name or not collection_name:
        print("No suitable schema found!", delay=0.1)
        continue

    if QUERY_TYPE == 0:
        print("Generating MongoDB Query using local llm method...")
        mongo_query = clear_mongo_query(select_generate_method(0, user_query, schema_text))
    elif QUERY_TYPE == 1:
        print("Generating MongoDB Query using local llm method...")
        mongo_query = clear_mongo_query(select_generate_method(1, user_query, schema_text))

    if mongo_query is None:
        print("MongoDB Query parse error", delay=0.1)
        continue
    else:
        print(f"\nMongoDB Query:\n{mongo_query}")

    print("Executing MongoDB Query...")
    result = execute_dynamic_mongo_query(CONNECTION_STRING, mongo_query, db_name, collection_name)

    print("\nQuery Result:\n")
    print(result)
