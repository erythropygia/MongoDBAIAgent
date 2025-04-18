import subprocess, os, sys
import time, random, string
from source.utils.logger import RichLogger

logger = RichLogger()

CONNECTION_STRING = ""

class CodeExecutor:
    def __init__(self):
        pass
    
    def _extract_and_update_mongodb_connection_string(self, text):
        start_marker = "```python"
        end_marker = "```"
        start_index = text.find(start_marker)
        if start_index != -1:
            end_index = text.find(end_marker, start_index + len(start_marker))
            if end_index != -1:
                python_code = text[start_index + len(start_marker):end_index].strip()
                updated_code = python_code.replace('("mongodb://localhost:27017/")',
                                                    f'("{CONNECTION_STRING}")')
                return updated_code, True

        return text, False

    def execute_generated_code(self, code):

        logger.log("Running script")
        script, status = self._extract_and_update_mongodb_connection_string(code)

        if status == False:
            return "Script execution failed. Reason: Python script was not found in response's ```python ``` structure.", False 
        else:
            random_str = ''.join(random.choices(string.ascii_lowercase, k=5))
            unique_file_name = f"generated_scripts/generated_mongo_query_{int(time.time())}_{random_str}.py"

            with open(unique_file_name, "w", encoding="utf-8") as f:
                f.write(script)

            try:
                script_dir = os.path.dirname(os.path.abspath(unique_file_name))
                python_cmd = "python" if sys.platform.startswith("win") else "python3"
                result = subprocess.run([python_cmd, unique_file_name], capture_output=True, text=True, timeout=60)
                
                stdout_output = result.stdout.strip()
                stderr_output = result.stderr.strip()
                combined_output = f"{stdout_output}\n{stderr_output}".lower()

                error_keywords = ["traceback", "exception", "error", "failed"]

                if result.returncode != 0 or any(keyword in combined_output for keyword in error_keywords):
                    error_message = f"Script execution failed with exit code: {result.returncode}. Error details:\n{result.stderr.strip()}"
                    return error_message, False 
                else:
                    return result.stdout.strip(), True  

            except subprocess.TimeoutExpired:
                return "Query execution timed out!", False  

            except Exception as e:
                return f"Execution error: {str(e)}", False 

    def save_mongo_cs_for_execute(self, connection_string):
        global CONNECTION_STRING
        CONNECTION_STRING = connection_string
