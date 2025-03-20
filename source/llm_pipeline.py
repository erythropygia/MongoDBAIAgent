import subprocess, time, re, os, yaml, sys, json
from source.process.qwen_process import QwenProcess
from source.process.gemini_process import GeminiProcess
from source.code_executor import CodeExecutor
from source.utils.logger import RichLogger

logger = RichLogger()

class LLMPipeline:
    def __init__(self, model_type):
        self.conservations = []
        self.code_executor = CodeExecutor()
        self.model_type = model_type  # 0: Qwen, 1: Gemini

        if model_type == 0:
            logger.panel("BUILD MODEL", "Selected Query Type: Local Model. Building the local model...", style="bold yellow")
            self.model_process = QwenProcess()
            self.model_process.initialize_model()
        else:
            self.model_process = GeminiProcess()

        with open("prompts.yaml", "r", encoding="utf-8") as file:
            self.prompts = yaml.safe_load(file)

    def generate(self, query, schema=None, retry_reason=None, is_first=True):
        try_count = 0
        if is_first:
            self.conservations = [] 

        logger.log("Generating Query...")

        if is_first:
            prompt_key = "generate_mongo_query_qwen" if self.model_type == 0 else "generate_mongo_query_gemini"
            prompt = self.prompts[prompt_key].format(schema=schema, user_query=query)
        else:
            prompt = retry_reason

        self.conservations.append({'role': "user", "content": prompt})

        if self.model_type == 0:
            response = self.model_process.generate_local(self.conservations, new_chat=is_first)
        else:
            response = self.model_process.generate_gemini(self.conservations, new_chat=is_first)

        self.conservations.append({'role': "assistant", "content": response})

        while try_count < 3:
            result, is_successful = self.code_executor.execute_generated_code(response)

            if is_successful:
                return result
            else:
                logger.log(f"Code execution failed. Trying again {try_count + 1}", style="bold yellow")
                self.conservations.append({'role': "user", "content": result})

                if self.model_type == 0:
                    response = self.model_process.generate_local(self.conservations, new_chat=False)
                else:
                    response = self.model_process.generate_gemini(self.conservations, new_chat=False)

                self.conservations.append({'role': "assistant", "content": response})

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