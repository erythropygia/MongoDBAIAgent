import os
import sys
import argparse
import time
from source.generate_schemas import SchemaExtractor
from source.rag import RagHandler
from source.llm_pipeline import LLMPipeline
from source.code_executor import CodeExecutor
from source.process.qwen_process import QwenProcess
from source.text_class import print_relevant_schemas

class MongoAgent:
    def __init__(self, connection_string, query_type):
        self.connection_string = connection_string
        self.query_type = query_type
        self.schema_extractor = SchemaExtractor()
        self.rag_handler = RagHandler()
        self.llm_pipeline = LLMPipeline()
        self.code_executor = CodeExecutor()
        if(query_type == 0):
            self.qwen_process = QwenProcess()
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.folders_to_create = ['generated_scripts', 'model', 'mongo_schema', 'chat_history']
        self.initialize_folders()

    def initialize_folders(self):
        for folder in self.folders_to_create:
            folder_path = os.path.join(self.current_dir, folder)
            if not os.path.exists(folder_path):
                print(f"{folder} folder not found. Creating...")
                os.makedirs(folder_path)

    def initialize_schema(self):
        schema_file = "./mongo_schema/mongo_schema.json"
        yaml_schema_file = "./mongo_schema/mongo_schema_doc.yaml"
        if not os.path.exists(schema_file) or not os.path.exists(yaml_schema_file):
            print("\nDatabase schema file not found. Generating schema...")
            self.schema_extractor.extract_schemas(self.connection_string)
            print("Schema extraction completed.\n")
        else:
            print("\nDatabase schema file found. Loading schema...\n")

    def process_query(self, query):
        schema_data = self.rag_handler.get_relevant_schema(query)
        if not schema_data:
            print("No suitable schema found. Please try again.")
            return

        print_relevant_schemas(schema_data)
        response = self.llm_pipeline.generate(self.query_type, query, schema_data, None, True)
        if response is not None:
            print("\nExecuting result:\n")
            print(response)

            for i in range(1, 3):
                while True:
                    confirmation = input("\nIs the response correct? (y/N) (type 'exit' to quit) : ").strip().lower()
                    if confirmation == "y":
                        self.llm_pipeline.save_chat_history()
                        return
                    elif confirmation == "exit":
                        sys.exit("\nExiting program. Goodbye!")
                    elif confirmation == "n":
                        break
                    else:
                        print("Please type y/n or exit.")
                        continue

                retry_reason = input("\nWhat was incorrect? Please describe the issue: ").strip()

                if self.query_type == 0:
                    self.query_type = 2
                elif self.query_type == 1:
                    self.query_type = 3

                response = self.llm_pipeline.generate(self.query_type, query, schema_data, retry_reason, False)
                print("\nExecuting result:\n")
                print(response)

    def run(self):
        self.code_executor.save_mongo_cs(self.connection_string)

        if self.query_type == 0:
            print("\nSelected Query Type: Local Model")
            print("\nBuilding the local model...")
            self.qwen_process.initialize_model()

        self.initialize_schema()
        self.rag_handler.load_schema_into_faiss()

        load_first = True
        while True:
            if load_first:
                load_first = False
            else:
                print("\nRequest process terminated transitioning to a new one")
                self.llm_pipeline.save_chat_history()
                time.sleep(1)

            user_query = input("\nEnter your query (type 'exit' to quit): ").strip()
            if user_query.lower() == "exit":
                sys.exit("\nExiting program. Goodbye!")
            self.process_query(user_query)


def main():
    #parser = argparse.ArgumentParser(description="MongoAgent")
    #parser.add_argument("--connection-string", type=str, required=True, help="MongoDB Connection String")
    #parser.add_argument("--query-type", type=int, choices=[0, 1], required=True, help="Specify query type: 'local(0)' or 'gemini(1)'")
    #args = parser.parse_args()

    #generator = MongoAgent(args.connection_string, args.query_type)
    generator = MongoAgent("mongodb+srv://noreplyemotion4u:45kVomOnb38h3VFU@emotion4u-basecluster.5gbds.mongodb.net/admin?retryWrites=true&loadBalanced=false&replicaSet=atlas-xp4kqi-shard-0&readPreference=primary&srvServiceName=mongodb&connectTimeoutMS=10000&authSource=admin&authMechanism=SCRAM-SHA-1", 0)
    generator.run()


if __name__ == "__main__":
    main()
