import subprocess
import time
import re
import os
import yaml
import sys
import json
from source.process.qwen_process import QwenProcess
from source.process.gemini_process import GeminiProcess
from source.process.gemma_process import GemmaProcess
from source.process.litellm_process import LiteLLMProcess
from source.code_executor import CodeExecutor
from source.utils.logger import RichLogger

logger = RichLogger()

class LLMPipeline:
    def __init__(self, model_type):
        self.conservations = []
        self.schema_conservations = []
        self.code_executor = CodeExecutor()
        self.model_type = model_type  # 0: Qwen, 1: Gemini, 2: Gemma3, 3: Ollama

        self._initialize_model()

        # Load prompts from YAML file
        with open("prompts.yaml", "r", encoding="utf-8") as file:
            self.prompts = yaml.safe_load(file)

    def _initialize_model(self):
        """
        Initializes the appropriate model based on the model type.
        """
        if self.model_type == 0:
            logger.panel("BUILD MODEL", "Selected Query Type: Local Qwen model. Building the local model...", style="bold yellow")
            self.model_process = QwenProcess()
            self.model_process.initialize_model()
        elif self.model_type == 1:
            self.model_process = GeminiProcess()
        elif self.model_type == 2:
            logger.panel("BUILD MODEL", "Selected Query Type: Local Gemma3 model. Building the local model...", style="bold yellow")
            self.model_process = GemmaProcess()
            self.model_process.initialize_model()
        elif self.model_type == 3:
            logger.panel("BUILD MODEL", "Selected Query Type: Ollama. Building the Ollama API...", style="bold yellow")
            self.model_process = LiteLLMProcess()

    def check_found_schema(self, query, schema=None):
        """
        Check for schema validation using the respective model type.
        """
        prompt_key = self._get_schema_prompt_key(schema)
        prompt = self.prompts[prompt_key].format(schema=schema, user_query=query)

        self.schema_conservations.append({'role': "user", "content": prompt, 'model_type': self.model_type})

        response = self._generate_response(self.schema_conservations)

        self.schema_conservations.append({'role': "assistant", "content": response, 'model_type': self.model_type})
        return response

    def _get_schema_prompt_key(self, schema):
        """
        Determines the appropriate prompt key for schema checking based on the model type.
        """
        if self.model_type == 0:
            return "check_schema_local_r1"
        elif self.model_type == 1:
            return "check_schema_gemini"
        elif self.model_type == 2 and self.model_process.get_model_type() == "Gemma3-R1":
            return "check_schema_local_r1"
        elif self.model_type == 2 and self.model_process.get_model_type() == "Gemma3-Base":
            return "check_schema_gemini"
        elif self.model_type == 3:
            return "check_schema_gemini"

    def generate(self, query, schema=None, retry_reason=None, is_first=True, is_schema_error=False):
        """
        Generates a query and executes the generated code with retries in case of failure.
        """
        try_count = 0
        if is_first:
            self.conservations = [] 

        logger.log("Generating Query...")

        prompt = self._generate_prompt(query, schema, retry_reason, is_first, is_schema_error)

        self.conservations.append({'role': "user", "content": prompt, 'model_type': self.model_type})

        response = self._generate_response(self.conservations, is_first)

        self.conservations.append({'role': "assistant", "content": response, 'model_type': self.model_type})

        # Retry logic for code execution
        while try_count < 3:
            result, is_successful = self.code_executor.execute_generated_code(response)

            if is_successful:
                return result
            else:
                logger.log(f"Code execution failed. Trying again {try_count + 1}", style="bold yellow")
                self.conservations.append({'role': "user", "content": result, 'model_type': self.model_type})

                response = self._generate_response(self.conservations, is_first=False)

                self.conservations.append({'role': "assistant", "content": response, 'model_type': self.model_type})

                result, is_successful = self.code_executor.execute_generated_code(response)

                if is_successful:
                    return result
                else:
                    try_count += 1
                    continue

        logger.log("\nCode execution attempts failed. Please try again.\n", style="bold red")
        return None

    def _generate_prompt(self, query, schema, retry_reason, is_first, is_schema_error):
        """
        Generates the prompt based on the model type and other parameters.
        """
        if is_first:
            prompt_key = self._get_prompt_key_for_query(schema)
            return self.prompts[prompt_key].format(schema=schema, user_query=query)
        else:
            if is_schema_error:
                return retry_reason + "\n" + str(schema)
            else:
                return retry_reason

    def _get_prompt_key_for_query(self, schema):
        """
        Determines the appropriate prompt key for query generation based on the model type.
        """
        if self.model_type == 0:
            return "generate_mongo_query_local_r1"
        elif self.model_type == 1:
            return "generate_mongo_query_gemini"
        elif self.model_type == 2 and self.model_process.get_model_type() == "Gemma3-R1":
            return "generate_mongo_query_with_system_message_local_r1"
        elif self.model_type == 2 and self.model_process.get_model_type() == "Gemma3-Base":
            return "system_message_with_user_request"
        elif self.model_type == 3:
            return "generate_mongo_query_gemini"

    def _generate_response(self, conservations, is_first=True):
        """
        Generates the response from the model based on the conversation history.
        """
        if self.model_type == 0:
            return self.model_process.generate_qwen(conservations, new_chat=is_first)
        elif self.model_type == 1:
            return self.model_process.generate_gemini(conservations, new_chat=is_first)
        elif self.model_type == 2:
            return self.model_process.generate_gemma(conservations, new_chat=is_first)
        elif self.model_type == 3:
            return self.model_process.generate_ollama(conservations, new_chat=is_first)

    def save_chat_history(self):
        """
        Saves the conversation history to a JSONL file.
        """
        if self.conservations:
            folder_path = "chat_history"
            file_path = os.path.join(folder_path, "chat_history.jsonl")

            with open(file_path, "a", encoding="utf-8") as file:
                file.write(json.dumps(self.conservations, ensure_ascii=False) + "\n")
            
            self.conservations = []

    def save_schema_history(self):
        """
        Saves the schema conversation history to a JSONL file.
        """
        if self.schema_conservations:
            folder_path = "chat_history"
            file_path = os.path.join(folder_path, "schema_history.jsonl")

            with open(file_path, "a", encoding="utf-8") as file:
                file.write(json.dumps(self.schema_conservations, ensure_ascii=False) + "\n")
            
            self.schema_conservations = []