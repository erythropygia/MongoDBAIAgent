import subprocess, time, re, os, yaml, sys, json
from source.process.qwen_process import QwenProcess
from source.process.gemini_process import GeminiProcess
from source.process.gemma_process import GemmaProcess
from source.code_executor import CodeExecutor
from source.utils.logger import RichLogger

logger = RichLogger()

class LLMPipeline:
    def __init__(self, model_type):
        self.conservations = []
        self.schema_conservations = []
        self.code_executor = CodeExecutor()
        self.model_type = model_type  # 0: Qwen, 1: Gemini 2: Gemma3

        if model_type == 0:
            logger.panel("BUILD MODEL", "Selected Query Type: Local Qwen model. Building the local model...", style="bold yellow")
            self.model_process = QwenProcess()
            self.model_process.initialize_model()
        elif model_type == 1:
            self.model_process = GeminiProcess()
        elif model_type == 2:
            logger.panel("BUILD MODEL", "Selected Query Type: Local Gemma3 model. Building the local model...", style="bold yellow")
            self.model_process = GemmaProcess()
            self.model_process.initialize_model()

        with open("prompts.yaml", "r", encoding="utf-8") as file:
            self.prompts = yaml.safe_load(file)

    def check_found_schema(self, query, schema=None):

        if self.model_type == 0:
            prompt_key = "check_schema_local_r1"
        elif self.model_type == 1:
            prompt_key = "check_schema_gemini"
        elif self.model_type == 2 and self.model_process.get_model_type() == "Gemma3-R1":
            prompt_key = "check_schema_local_r1"
        elif self.model_type == 2 and self.model_process.get_model_type() == "Gemma3-Base":
            prompt_key = "check_schema_gemini"
            
        prompt = self.prompts[prompt_key].format(schema=schema, user_query=query)
        self.schema_conservations.append({'role': "user", "content": prompt, 'model_type': self.model_type})

        if self.model_type == 0:
            response = self.model_process.generate_qwen(self.schema_conservations, new_chat=True)
        elif self.model_type == 1:
            response = self.model_process.generate_gemini(self.schema_conservations, new_chat=True)
        elif self.model_type == 2:
            response = self.model_process.generate_gemma(self.schema_conservations, new_chat=True)

        self.schema_conservations.append({'role': "assistant", "content": response, 'model_type': self.model_type})
        return response

    def generate(self, query, schema=None, retry_reason=None, is_first=True, is_schema_error=False):
        try_count = 0
        if is_first:
            self.conservations = [] 

        logger.log("Generating Query...")

        if is_first:
            if self.model_type == 0:
                prompt_key = "generate_mongo_query_local_r1"
            elif self.model_type == 1:
                prompt_key = "generate_mongo_query_gemini"
            elif self.model_type == 2 and self.model_process.get_model_type() == "Gemma3-R1":
                prompt_key = "generate_mongo_query_with_system_message_local_r1"
            elif self.model_type == 2 and self.model_process.get_model_type() == "Gemma3-Base":
                prompt_key = "system_message_with_user_request"

            prompt = self.prompts[prompt_key].format(schema=schema, user_query=query)
        else:
            if is_schema_error:
                prompt = retry_reason + "\n" + str(schema)
            else:
                prompt = retry_reason

        self.conservations.append({'role': "user", "content": prompt, 'model_type': self.model_type})

        if self.model_type == 0:
            response = self.model_process.generate_qwen(self.conservations, new_chat=is_first)
        elif self.model_type == 1:
            response = self.model_process.generate_gemini(self.conservations, new_chat=is_first)
        elif self.model_type == 2:
            response = self.model_process.generate_gemma(self.conservations, new_chat=is_first)

        self.conservations.append({'role': "assistant", "content": response, 'model_type': self.model_type})

        while try_count < 3:
            result, is_successful = self.code_executor.execute_generated_code(response)

            if is_successful:
                return result
            else:
                logger.log(f"Code execution failed. Trying again {try_count + 1}", style="bold yellow")
                self.conservations.append({'role': "user", "content": result, 'model_type': self.model_type})

                if self.model_type == 0:
                    response = self.model_process.generate_qwen(self.conservations, new_chat=False)
                elif self.model_type == 1:
                    response = self.model_process.generate_gemini(self.conservations, new_chat=False)
                elif self.model_type == 2:
                    response = self.model_process.generate_gemma(self.conservations, new_chat=False)

                self.conservations.append({'role': "assistant", "content": response, 'model_type': self.model_type})

                result, is_successful = self.code_executor.execute_generated_code(response)

                if is_successful:
                    return result
                else:
                    try_count += 1
                    continue

        logger.log("\nCode execution attempts failed. Please try again.\n", style="bold red")
        return None
    
    def save_chat_history(self):
        if(len(self.conservations)) != 0:
            folder_path = "chat_history"
            file_path = os.path.join(folder_path, "chat_history.jsonl")

            with open(file_path, "a", encoding="utf-8") as file:
                file.write(json.dumps(self.conservations, ensure_ascii=False) + "\n")
            
            self.conservations = []
    
    def save_schema_history(self):
        if(len(self.schema_conservations)) != 0:
            folder_path = "chat_history"
            file_path = os.path.join(folder_path, "schema_history.jsonl")

            with open(file_path, "a", encoding="utf-8") as file:
                file.write(json.dumps(self.schema_conservations, ensure_ascii=False) + "\n")
            
            self.schema_conservations = []