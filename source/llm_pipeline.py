import subprocess, time, re, os, yaml, sys, json
from source.process.qwen_process import QwenProcess
from source.process.gemini_process import GeminiProcess
from source.code_executor import CodeExecutor
from source.utils.logger import RichLogger

logger = RichLogger()

class LLMPipeline:
    def __init__(self):
        self.conservations = []
        self.code_executor = CodeExecutor()
        self.qwen_process = QwenProcess()
        self.gemini_process = GeminiProcess()

        with open("prompts.yaml", "r", encoding="utf-8") as file:
            self.prompts = yaml.safe_load(file)

    def     generate(self, method, first_user_query, schema, repaired_query, is_first=False):
        try_count = 0
        if is_first:
            self.conservations = []

        logger.log("Generating Query...")

        if method == 0:
            prompt = self.prompts["generate_mongo_query_qwen"].format(schema=schema, user_query=first_user_query)
            self.conservations.append({'role': "user", "content": prompt})

            response = self.qwen_process.generate_local(self.conservations, new_chat=True)
            self.conservations.append({'role': "assistant", "content": response})

            while try_count < 3:
                result, is_successful = self.code_executor.execute_generated_code(response)

                if is_successful:
                    return result
                else:
                    logger.log(f"Code execution failed. Trying again {try_count + 1}", style="bold yellow")
                    self.conservations.append({'role': "user", "content": result})
                    response = self.qwen_process.generate_local(self.conservations)
                    result, is_successful = self.code_executor.execute_generated_code(response)
                    self.conservations.append({'role': "assistant", "content": response})

                    if is_successful:
                        return result
                    else:
                        try_count += 1
                        continue

            if not is_successful:
                logger.log("\nCode execution attempts failed. Please try again.\n", style="bold red")
                return None

        elif method == 1:  # Gemini process for method 1
            prompt = self.prompts["generate_mongo_query_gemini"].format(schema=schema, user_query=first_user_query)
            self.conservations.append({'role': "user", "content": prompt})

            response = self.gemini_process.generate_gemini(self.conservations, new_chat=True)
            self.conservations.append({'role': "assistant", "content": response})

            while try_count < 3:
                result, is_successful = self.code_executor.execute_generated_code(response)

                if is_successful:
                    return result
                else:
                    logger.log(f"Code execution failed. Trying again {try_count + 1}", style="bold yellow")
                    self.conservations.append({'role': "user", "content": result})
                    response = self.gemini_process.generate_gemini(self.conservations, new_chat=False)
                    result, is_successful = self.code_executor.execute_generated_code(response)
                    self.conservations.append({'role': "assistant", "content": response})

                    if is_successful:
                        return result
                    else:
                        try_count += 1
                        continue

            if not is_successful:
                logger.log("\nCode execution attempts failed. Please try again.\n", style="bold red")
                return None

        # Handling methods for repaired query
        elif method == 2:
            self.conservations.append({'role': "user", "content": repaired_query})
            response = self.qwen_process.generate_local(self.conservations, new_chat=False)

            while try_count < 3:
                result, is_successful = self.code_executor.execute_generated_code(response)
                self.conservations.append({'role': "assistant", "content": response})

                if is_successful:
                    return result
                else:
                    logger.log(f"Code execution failed. Trying again {try_count + 1}", style="bold yellow")
                    self.conservations.append({'role': "user", "content": result})
                    response = self.qwen_process.generate_local(self.conservations, new_chat=False)
                    self.conservations.append({'role': "assistant", "content": response})

                    result, is_successful = self.code_executor.execute_generated_code(response)

                    if is_successful:
                        return result
                    else:
                        self.conservations.append({'role': "user", "content": result})
                        try_count += 1
                        continue

            if not is_successful:
                logger.log("\nCode execution attempts failed. Please try again.\n", style="bold red")
                return None

        elif method == 3:
            self.conservations.append({'role': "user", "content": repaired_query})
            response = self.gemini_process.generate_gemini(self.conservations, new_chat=False)

            while try_count < 3:
                result, is_successful = self.code_executor.execute_generated_code(response)
                self.conservations.append({'role': "assistant", "content": response})

                if is_successful:
                    return result
                else:
                    logger.log(f"Code execution failed. Trying again {try_count + 1}", style="bold yellow")
                    self.conservations.append({'role': "user", "content": result})
                    response = self.gemini_process.generate_gemini(self.conservations, new_chat=False)
                    self.conservations.append({'role': "assistant", "content": response})

                    result, is_successful = self.code_executor.execute_generated_code(response)

                    if is_successful:
                        return result
                    else:
                        self.conservations.append({'role': "user", "content": result})
                        try_count += 1
                        continue

            if not is_successful:
                logger.log("\nCode execution attempts failed. Please try again.\n", style="bold red")
                return None

    def save_chat_history(self):
        if(len(self.conservations)) != 0:
            folder_path = "chat_history"
            file_path = os.path.join(folder_path, "chat_history.jsonl")

            with open(file_path, "a", encoding="utf-8") as file:
                file.write(json.dumps(self.conservations, ensure_ascii=False) + "\n")
            
            self.conservations = []