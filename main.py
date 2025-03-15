import os
import sys
import argparse
from source.generate_schemas import extract_schemas
from source.rag import load_schema_into_faiss, get_relevant_schema, save_query_to_excel
from source.llm_pipeline import generate
from source.code_executor import save_mongo_cs
from source.process.qwen_process import wake_up_qwen
from source.text_class import print_relevant_schemas

current_dir = os.path.dirname(os.path.abspath(__file__))
folders_to_create = ['generated_scripts', 'model', 'mongo_schema']

for folder in folders_to_create:
    folder_path = os.path.join(current_dir, folder)
    if not os.path.exists(folder_path):
        print(f"{folder} folder not found. Creating...")
        os.makedirs(folder_path)


def initialize_schema(connection_string, schema_file="./mongo_schema/mongo_schema.json", yaml_schema_file="./mongo_schema/mongo_schema_doc.yaml"):
    if not os.path.exists(schema_file) or not os.path.exists(yaml_schema_file):
        print("\nDatabase schema file not found. Generating schema...")
        extract_schemas(connection_string)
        print("Schema extraction completed.\n")
    else:
        print("\nDatabase schema file found. Loading schema...\n")


def process_query(query, query_type):
    schema_data = get_relevant_schema(query)
    if not schema_data:
        print("No suitable schema found. Please try again.")
        return

    print_relevant_schemas(schema_data)
    response = generate(query_type, query, schema_data, None, True)
    if(response is not None):
        print("Executing result:\n", response)

        for i in range(1,3): 
            while(True):            
                confirmation = input("\nIs the response correct? (y/N) (type 'exit' to quit) : ").strip().lower()
                if confirmation == "y":
                    save_query_to_excel(schema_data, query)
                    return
                elif confirmation == "exit":
                    sys.exit("\nExiting program. Goodbye!")
                elif confirmation == "n":
                    break
                else:
                    print("Please type y/n or exit.")
                    continue

            retry_reason = input("\nWhat was incorrect? Please describe the issue: ").strip()

            if(query_type == 0):
                query_type = 2
            elif(query_type == 1):
                query_type = 3

            response = generate(query_type, query, schema_data, retry_reason, False)
            print("Executing result:\n", response)


def main():
    #parser = argparse.ArgumentParser(description="MongoDB Query Generator")
    #parser.add_argument("--connection-string", type=str, required=True, help="MongoDB Connection String")
    #parser.add_argument("--query-type", type=int, choices=[0, 1], required=True, help="Specify query type: 'local(0)' or 'gemini(1)'")
    #args = parser.parse_args()

    save_mongo_cs("mongodb+srv://noreplyemotion4u:45kVomOnb38h3VFU@emotion4u-basecluster.5gbds.mongodb.net/admin?retryWrites=true&loadBalanced=false&replicaSet=atlas-xp4kqi-shard-0&readPreference=primary&srvServiceName=mongodb&connectTimeoutMS=10000&authSource=admin&authMechanism=SCRAM-SHA-1")

    if(1 == 0):
        print("\nSelected Query Type: Local Model")
        print("\nBuilding the local model...")
        wake_up_qwen()

    initialize_schema("mongodb+srv://noreplyemotion4u:45kVomOnb38h3VFU@emotion4u-basecluster.5gbds.mongodb.net/admin?retryWrites=true&loadBalanced=false&replicaSet=atlas-xp4kqi-shard-0&readPreference=primary&srvServiceName=mongodb&connectTimeoutMS=10000&authSource=admin&authMechanism=SCRAM-SHA-1")
    load_schema_into_faiss()

    while True:
        user_query = input("\nEnter your query (type 'exit' to quit): ").strip()
        if user_query.lower() == "exit":
            sys.exit("\nExiting program. Goodbye!")
        process_query(user_query, 1)


if __name__ == "__main__":
    main()
