import os
import argparse
from generate_mongo_schema import extract_mongo_schema
from rag import load_schema_into_faiss, get_relevant_schema, save_query_to_excel
from process import select_generate_method, execute_generated_code


parser = argparse.ArgumentParser(description="MongoDB Query Generator")
parser.add_argument("--connection-string", type=str, required=True, help="MongoDB Connection String")
parser.add_argument("--query-type", type=int, choices=[0, 1], required=True, help="Specify query type: 'local(0)' or 'gemini(1)'")
args = parser.parse_args()

CONNECTION_STRING = args.connection_string
QUERY_TYPE = args.query_type
SCHEMA_FILE = "mongo_schema.json"

if not os.path.exists(SCHEMA_FILE):
    print("\nDatabase schema file not found. Generating schema...")
    extract_mongo_schema(CONNECTION_STRING)
    print("Schema extraction completed.\n")

load_schema_into_faiss()

while True:
    user_query = input("\nEnter your query (type 'exit' to quit): ")
    
    if user_query.lower() == "exit":
        print("\nExiting program. Goodbye!")
        break

    schema_text, db_name, collection_name, matched_queries = get_relevant_schema(user_query)

    if not schema_text or not db_name or not collection_name:
        print("No suitable schema found. Please try again.")
        continue

    print(f"Relevant Schema Found: `{db_name}.{collection_name}`")

    script = select_generate_method(QUERY_TYPE, user_query, schema_text)
 
    if not script:
        print("Script generation failed.")
        continue

    execution_result = execute_generated_code(script, CONNECTION_STRING)

    print("\nQuery Execution Result:\n")
    print(execution_result)

    if ("Traceback" in execution_result or 
        "Error" in execution_result or 
        "Exception" in execution_result or
        "Query execution timed out!" in execution_result or 
        "Execution error" in execution_result in execution_result):
        
        print("\nAn error occurred while executing the script.")
        print("Sending error back to the model to generate a new query...\n")

        new_script = select_generate_method(2, script=script, execution_query=execution_result, schema=schema_text)

        if new_script:
            print("\nRetrying with the corrected script...\n")
            execution_result = execute_generated_code(new_script, CONNECTION_STRING)
            print("\nQuery Execution Result (After Fix):\n")
            print(execution_result)
        else:
            print("\nThe model couldn't generate a valid fix. Please try again.")
    
    confirmation = input("\nIs the response correct? (y/N): ").strip().lower()
    if confirmation == "y":
        save_query_to_excel(db_name, collection_name, user_query)
