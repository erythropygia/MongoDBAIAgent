import os
import sys
import argparse
from source.generate_mongo_schema import extract_mongo_schema
from source.rag import load_schema_into_faiss, get_relevant_schema, save_query_to_excel
from source.llm_pipeline import select_generate_method, execute_generated_code
from source.process.qwen_process import wake_up_qwen

current_dir = os.path.dirname(os.path.abspath(__file__))
folders_to_create = ['run_script', 'model', 'mongo_schema']

for folder in folders_to_create:
    folder_path = os.path.join(current_dir, folder)
    if not os.path.exists(folder_path):
        print(f"{folder} folder not found. Creating...")
        os.makedirs(folder_path)


def initialize_schema(connection_string, schema_file="./mongo_schema/mongo_schema.json"):
    if not os.path.exists(schema_file):
        print("\nDatabase schema file not found. Generating schema...")
        extract_mongo_schema(connection_string)
        print("Schema extraction completed.\n")
    else:
        print("\nDatabase schema file found. Loading schema...\n")


def process_query(query, connection_string, query_type):
    schema_data = get_relevant_schema(query)
    if not schema_data:
        print("No suitable schema found. Please try again.")
        return

    print(f"Relevant Schema(s) Found: `{schema_data[0]['DBName']}`, `{schema_data[0]['Collection']}`")

    script = select_generate_method(query_type, query, schema_data)
    if not script:
        print("Script generation failed.")
        return
    
    execution_result = execute_generated_code(script, connection_string)
    print("\nQuery Execution Result:\n", execution_result)

    refine_query_if_needed(schema_data[0]["DBName"] , schema_data[0]["Collection"], query, script, execution_result, connection_string, schema_data[0]["Schema"],query_type)


def refine_query_if_needed(db_name, collection_name, query, script, execution_result, connection_string, schema_text, query_type):
    error_feedback_history = []
    for i in range(3): 
        confirmation = input("\nIs the response correct? (y/N) (type 'exit' to quit) : ").strip().lower()
        
        if confirmation == "y":
            save_query_to_excel(db_name, collection_name, query)
            return
        if confirmation == "exit":
            sys.exit("\nExiting program. Goodbye!")

        retry_reason = input("\nWhat was incorrect? Please describe the issue: ").strip()
        error_feedback_history.append(retry_reason)
        
        print("\nRetrying with the corrected script...\n")

        if(query_type == 0):
            query_type = 2
        else:
            query_type = 3
            
        new_script = select_generate_method(
            query_type, user_query=query, script=script, execution_query=execution_result, schema=schema_text, error_feedbacks = retry_reason
        )
        
        if new_script:
            execution_result = execute_generated_code(new_script, connection_string)

            if ("Traceback" in execution_result or 
                "Error" in execution_result or 
                "Exception" in execution_result or
                "Query execution timed out!" in execution_result or 
                "Execution error" in execution_result in execution_result):
                
                print(f"\nAn error occurred while executing the script.\n")
            else:
                print("\nQuery Execution Result (After Fix):\n", execution_result)
        else:
            print(f"\nThe model couldn't generate a valid fix.\n")

    print("\nUnable to resolve the issue after 3 attempts. Moving on to the next request...")
        

def main():
    parser = argparse.ArgumentParser(description="MongoDB Query Generator")
    parser.add_argument("--connection-string", type=str, required=True, help="MongoDB Connection String")
    parser.add_argument("--query-type", type=int, choices=[0, 1], required=True, help="Specify query type: 'local(0)' or 'gemini(1)'")
    args = parser.parse_args()

    if(args.query_type == 0):
        print("\nSelected Query Type: Local Model")
        print("\nBuilding the local model...")
        wake_up_qwen()

    initialize_schema(args.connection_string)
    load_schema_into_faiss(args.query_type)

    while True:
        user_query = input("\nEnter your query (type 'exit' to quit): ").strip()
        if user_query.lower() == "exit":
            sys.exit("\nExiting program. Goodbye!")
        process_query(user_query, args.connection_string, args.query_type)


if __name__ == "__main__":
    main()
