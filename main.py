import os
import argparse
import time
import sys
import threading
from generate_mongo_schema import extract_mongo_schema
from rag import load_schema_into_faiss, get_relevant_schema
from process import select_generate_method, execute_generated_code

class LoadingAnimation:
    def __init__(self, message="Processing"):
        self.message = message
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.animate)
        self.thread.start()

    def animate(self):
        chars = ["|", "/", "-", "\\"]
        i = 0
        while self.running:
            sys.stdout.write(f"\r{self.message} {chars[i % len(chars)]} ")
            sys.stdout.flush()
            i += 1
            time.sleep(0.2)

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        sys.stdout.write("\r" + " " * 50 + "\r")  # Temizle
        sys.stdout.flush()

parser = argparse.ArgumentParser(description="MongoDB Query Generator")
parser.add_argument("--connection-string", type=str, required=True, help="MongoDB Connection String")
parser.add_argument("--query-type", type=int, choices=[0, 1], required=True, help="Specify query type: 'local(0)' or 'gemini(1)'")
args = parser.parse_args()

CONNECTION_STRING = args.connection_string
QUERY_TYPE = args.query_type
SCHEMA_FILE = "mongo_schema.json"

if not os.path.exists(SCHEMA_FILE):
    print("\nDatabase schema file not found. Generating schema...")
    loading = LoadingAnimation("Extracting Schema")
    loading.start()
    
    extract_mongo_schema(CONNECTION_STRING)
    
    loading.stop()
    print("Schema extraction completed.\n")

print("Loading schema into FAISS...")
loading = LoadingAnimation("Indexing Schema")
loading.start()

load_schema_into_faiss()

loading.stop()
print("Schema successfully loaded into FAISS.\n")

# 🔍 Kullanıcıdan Sorgu Alma
while True:
    user_query = input("\nEnter your query (type 'exit' to quit): ")
    
    if user_query.lower() == "exit":
        print("\nExiting program. Goodbye!")
        break

    print("\nGetting relevant schema for your query...")
    loading = LoadingAnimation("Searching Schema")
    loading.start()

    schema_text, db_name, collection_name = get_relevant_schema(user_query)

    loading.stop()

    if not schema_text or not db_name or not collection_name:
        print("No suitable schema found. Please try again.")
        continue

    print(f"Relevant Schema Found: `{db_name}.{collection_name}`")

    loading = LoadingAnimation("Generating Query...")
    loading.start()

    script = select_generate_method(QUERY_TYPE, user_query, schema_text)

    loading.stop()

    if not script:
        print("Script generation failed.")
        continue

    loading = LoadingAnimation("Running script")
    loading.start()

    execution_result = execute_generated_code(script, CONNECTION_STRING)

    loading.stop()

    print("\nQuery Execution Result:\n")
    print(execution_result)

    if "Traceback" in execution_result or "Error" in execution_result or "Exception" in execution_result:
        print("\nAn error occurred while executing the script.")
        print("Sending error back to the model to generate a new query...\n")

        new_script = select_generate_method(QUERY_TYPE, f"Fix this error {execution_result} for this code: {script}", schema_text)

        if new_script:
            print("\nRetrying with the corrected script...\n")
            execution_result = execute_generated_code(new_script, CONNECTION_STRING)
            print("\nQuery Execution Result (After Fix):\n")
            print(execution_result)
        else:
            print("\nThe model couldn't generate a valid fix. Please try again.")
