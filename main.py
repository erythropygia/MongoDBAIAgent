import os, sys, time
from decouple import config
from source.generate_schemas import SchemaExtractor
from source.rag import RagHandler
from source.llm_pipeline import LLMPipeline
from source.code_executor import CodeExecutor
from source.process.qwen_process import QwenProcess
from source.utils.logger import RichLogger

logger = RichLogger()

class MongoAgent:
    def __init__(self, model_type):
        self.connection_string = config('CONNECTION_STRING')
        if not self.connection_string: 
            logger.panel("ERROR LOADING .ENV", "Missing 'CONNECTION_STRING' in config file! Please check your configuration", style= "bold red")
        else:
            logger.panel("LOADING .ENV", "CONNECTION_STRING INJECTED")

        
        self.model_type = model_type
        self.schema_extractor = SchemaExtractor()
        self.rag_handler = RagHandler()
        self.llm_pipeline = LLMPipeline()
        self.code_executor = CodeExecutor()
        if(model_type == 0):
            self.qwen_process = QwenProcess()
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.folders_to_create = ['generated_scripts', 'model', 'mongo_schema', 'chat_history']
        self.initialize_folders()

    def initialize_folders(self):
        for folder in self.folders_to_create:
            folder_path = os.path.join(self.current_dir, folder)
            if not os.path.exists(folder_path):
                logger.panel("INFO", f"{folder} folder not found. Creating...", style="bold blue")
                os.makedirs(folder_path)

    def connection_check(self):
        model_type_str = "Local Model (Qwen)" if self.model_type == 0 else "Gemini"
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
                title="ERROR",
                content=f"""
                MongoDB connection failed! Please check your connection string[/bold cyan]
                Model Type: [bold cyan]{model_type_str}[/bold cyan]
                """,
                style="bold blue"
            )
            return

    def initialize_schema(self):
        schema_file = "./mongo_schema/mongo_schema.json"
        yaml_schema_file = "./mongo_schema/mongo_schema_doc.yaml"
        if not os.path.exists(schema_file) or not os.path.exists(yaml_schema_file):
            logger.panel("INFO", "Database schema file not found. Generating schema...", style="bold blue")
            self.schema_extractor.extract_schemas(self.connection_string)
            logger.panel("INFO", "Schema extraction completed.", style="bold green")
        else:
            logger.panel("INFO", "Database schema file found. Loading schema...", style="bold blue")

    def process_query(self, query):
        schema_data = self.rag_handler.get_relevant_schema(query)
        if not schema_data:
            logger.panel("RESULT", "No suitable schema found. Please try again.", style="bold red")
            return

        logger.log(str(schema_data))
        response = self.llm_pipeline.generate(self.model_type, query, schema_data, None, True)
        if response is not None:
            logger.panel("EXECUTING RESULT", response, style= "bold green")
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
                        logger.log("Please type y/n or exit.")
                        continue

                retry_reason = input("\nWhat was incorrect? Please describe the issue: ").strip()

                if self.model_type == 0:
                    self.model_type = 2
                elif self.model_type == 1:
                    self.model_type = 3

                response = self.llm_pipeline.generate(self.model_type, query, schema_data, retry_reason, False)
                logger.panel("EXECUTING RESULT",response, style= "bold green")


    def run(self):
        self.code_executor.save_mongo_cs_for_execute(self.connection_string)
        self.connection_check()

        if self.model_type == 0:
            logger.panel("BUILD MODEL", "Selected Query Type: Local Model. Building the local model...", style= "bold yellow")
            self.qwen_process.initialize_model()

        self.initialize_schema()
        self.rag_handler.load_schema_into_faiss()

        load_first = True
        while True:
            if load_first:
                load_first = False
            else:
                logger.clear()
                logger.panel("NEW REQUEST", "Request process terminated transitioning to a new one", style= "bold green")
                self.llm_pipeline.save_chat_history()
                time.sleep(1)

            user_query = input("Enter your query (type 'exit' to quit): ").strip()
            if user_query.lower() == "exit":
                sys.exit("\nExiting program. Goodbye!")
            self.process_query(user_query)


def main():
    version_info = {
        "Name": "Mongo Agent",
        "Version": "0.1.0",
        "Author": "erythropygia",
    }
    logger.table("Information", version_info)

    model_info = {
        "Local Model (Qwen)": 0,
        "Gemini": 1
    }
    logger.table("Model Type", model_info)

    model_type = logger.prompt_panel(
        question="Select Model Type (0 or 1)",
        choices=[0, 1]
    )

    generator = MongoAgent(model_type)
    generator.run()


if __name__ == "__main__":
    main()
