import os, sys, time, json, re
from decouple import config
from source.generate_schemas import SchemaExtractor
from source.rag import RagHandler
from source.llm_pipeline import LLMPipeline
from source.code_executor import CodeExecutor
from source.utils.logger import RichLogger

logger = RichLogger()

class MongoAgent:
    def __init__(self, model_type):
        try:
            self.connection_string = config('CONNECTION_STRING')
            logger.panel("LOADING .ENV", "CONNECTION_STRING INJECTED")
        except:
            logger.panel("ERROR LOADING .ENV", "Missing 'CONNECTION_STRING' in config file! Please check your configuration. Default using: mongodb://localhost:27017/", style= "bold red")
            self.connection_string = "mongodb://localhost:27017/"
        
        self.model_type = model_type
        self.schema_extractor = SchemaExtractor()
        self.rag_handler = RagHandler()
        self.llm_pipeline = LLMPipeline(model_type = model_type)
        self.code_executor = CodeExecutor()
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.folders_to_create = ['generated_scripts', 'model', 'mongo_schema', 'chat_history']
        self._initialize_folders()

    def _initialize_folders(self):
        for folder in self.folders_to_create:
            folder_path = os.path.join(self.current_dir, folder)
            if not os.path.exists(folder_path):
                logger.panel("INFO", f"{folder} folder not found. Creating...", style="bold blue")
                os.makedirs(folder_path)

    def _connection_check(self):
        model_type_str = (
            "Local Model (Qwen)" if self.model_type == 0 else
            "Gemini" if self.model_type == 1 else
            "Local Model (Gemma3)" if self.model_type == 2 else
            "Ollama" if self.model_type == 3 else
            "Unknown"
        )
        conn_result = self.schema_extractor.db_connection_check(self.connection_string)
        
        if conn_result:
            logger.show_panel(
                title="BUILD SCHEMA",
                content=f"""
                MongoDB Connection Status: [bold cyan]{conn_result}[/bold cyan]
                Model Type: [bold cyan]{model_type_str}[/bold cyan]
                """,
                style="bold blue"
            )

        else:
            logger.show_panel(
                title="WARNING",
                content=f"""
                [bold red]MongoDB connection failed! Please check your connection string[/bold red]
                Model Type: [bold cyan]{model_type_str}[/bold cyan]
                """,
                style="bold blue"
            )
    
    def _initialize_schema(self):
        schema_file = "./mongo_schema/mongo_schema.json"
        yaml_schema_file = "./mongo_schema/mongo_schema_doc.yaml"
        if not os.path.exists(schema_file) or not os.path.exists(yaml_schema_file):
            logger.panel("INFO", "Database schema file not found. Generating schema...", style="bold blue")
            self.schema_extractor.extract_schemas(self.connection_string)
            logger.panel("INFO", "Schema extraction completed.", style="bold green")
        else:
            logger.panel("INFO", "Database schema file found. Loading schema...", style="bold blue")

    def _extract_json_blocks(self, text):
        if not isinstance(text, str):
            return None
        
        results = []
        json_blocks = re.findall(r'```json\s*([\s\S]*?)\s*```', text)
        
        for block in json_blocks:
            try:
                cleaned_block = block.strip()
                if cleaned_block:
                    parsed = json.loads(cleaned_block)
                    if isinstance(parsed, (list, dict)):
                        results.append(parsed)
            except json.JSONDecodeError as e:
                return None
            except Exception as e:
                return None
        
        return results

    def _process_query(self, query):

        schema_data = self.rag_handler.get_relevant_schema(query)

        if not schema_data:
            logger.panel("RESULT", "No suitable schema found. Please try again.", style="bold red")
            return
        
        found_schemas = self.llm_pipeline.check_found_schema(query, schema_data)

        if found_schemas:
            final_schemas =  self._extract_json_blocks(found_schemas)
            if final_schemas is None:
                logger.panel("SCHEMA RESULT", "LLM failed to generate correct schema, proceeding from RAG output", style="bold red")
                final_schemas = schema_data     
        else:
            logger.panel("SCHEMA RESULT", "LLM failed to generate correct schema, proceeding from RAG output", style="bold red")
            final_schemas = schema_data
        
        self.llm_pipeline.save_schema_history()

        response = self.llm_pipeline.generate(query, final_schemas, None, True)
        if response is not None:
            logger.panel("EXECUTING RESULT", response, style= "bold green")
            for i in range(1, 3):
                is_schema_error = False
                while True:
                    confirmation = input("\nIs the response correct? (y/N) (type 'exit' to quit) : ").strip().lower()
                    if confirmation == "y":
                        self.llm_pipeline.save_chat_history()
                        return
                    elif confirmation == "exit":
                        logger.panel("EXIT", "Exiting program. Goodbye!", style="bold purple")
                        sys.exit(1)
                    elif confirmation == "n":
                        retry_reason_select = input("\n1. Wrong schema, 2. Describe the issue: ").strip()
                        if retry_reason_select == "1":
                            schema_list = self.schema_extractor.get_all_collections()
                            selected_schema_input = input("\nSelect the schemas you want to use (comma or space separated): ").strip()
                            selected_schema_indices = [int(i.strip()) - 1 for i in re.split('[, ]+', selected_schema_input) if i.strip().isdigit()]
                            selected_schemas = [schema_list[i] for i in selected_schema_indices]

                            schema_data = self.rag_handler.get_collection_data_from_yaml(selected_schemas)
                            is_schema_error = True

                            if len(schema_data) == 0:
                                logger.panel("SCHEMA RESULT", "No suitable schema found. Please try again.", style="bold red")
                                break

                            retry_reason = query

                        elif retry_reason_select == "2":
                            retry_reason = input("\nWhat was incorrect? Please describe the issue: ").strip()
                        break
                    else:
                        logger.log("Please type y/n or exit.")
                        continue
                    
                response = self.llm_pipeline.generate(query, schema_data, retry_reason, is_first = False, is_schema_error = is_schema_error)
                if response is not None:
                    logger.panel("EXECUTING RESULT",response, style= "bold green")
                else:
                    logger.panel("NEW REQUEST", "Request process terminated transitioning to a new one", style= "bold green")

    def run(self):
        self.code_executor.save_mongo_cs_for_execute(self.connection_string)
        self._connection_check()
        self._initialize_schema()
        self.rag_handler.load_schema_into_faiss()

        load_first = True
        while True:
            if load_first:
                load_first = False
            else:
                logger.panel("NEW REQUEST", "Request process terminated transitioning to a new one", style= "bold green")
                self.llm_pipeline.save_chat_history()
                time.sleep(1)

            user_query = input("Enter your query (type 'exit' to quit): ").strip()
            if user_query.lower() == "exit":
                logger.panel("EXIT", "Exiting program. Goodbye!", style="bold purple")
                sys.exit(1)
            self._process_query(user_query)


def main():
    version_info = {
        "Name": "Mongo Agent",
        "Version": "0.1.0",
        "Author": "erythropygia",
    }
    logger.table("Information", version_info)

    model_info = {
        "Local Model (Qwen)": 0,
        "Gemini": 1,
        "Local Model (Gemma3)": 2,
        "Ollama": 3,
    }
    logger.table("Model Type", model_info)

    model_type = logger.prompt_panel(
        question="Select Model Type (0, 1, 2 or 3)",
        choices=[0, 1, 2, 3]
    )

    generator = MongoAgent(model_type)
    generator.run()


if __name__ == "__main__":
    main()
