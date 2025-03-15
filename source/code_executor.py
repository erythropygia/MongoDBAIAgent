import subprocess, os, sys

GENERATED_SCRIPT_PATH = "generated_scripts/generated_mongo_query.py"
CONNECTION_STRING = ""

class CodeExecutor:
    def __init__(self):
        self.connection_string = CONNECTION_STRING 

    def extract_and_update_mongodb_connection_string(self, text):
        connection_string = self.connection_string
        start_marker = "```python"
        end_marker = "```"

        start_index = text.find(start_marker)
        if start_index != -1:
            end_index = text.find(end_marker, start_index + len(start_marker))
            if end_index != -1:
                python_code = text[start_index + len(start_marker):end_index].strip()
                updated_code = python_code.replace('("mongodb://localhost:27017/")',
                                                    f'("{connection_string}")')
                return updated_code, True

        return text, False

    def execute_generated_code(self, code):
            connection_string = self.connection_string
            print("Running script")

            script, status= self.extract_and_update_mongodb_connection_string(code)

            if status == False:
                return "Script execution failed. Reason: Python script was not found in response's ```python ``` structure.", False 
            else:
                with open(GENERATED_SCRIPT_PATH, "w", encoding="utf-8") as f:
                    f.write(script)

                try:
                    script_dir = os.path.dirname(os.path.abspath(GENERATED_SCRIPT_PATH))
                    python_cmd = "python" if sys.platform.startswith("win") else "python3"
                    result = subprocess.run([python_cmd, GENERATED_SCRIPT_PATH], capture_output=True, text=True, timeout=60)

                    if result.returncode != 0:
                        error_message = f"Script execution failed with exit code: {result.returncode}. Error details:\n{result.stderr.strip()}"
                        return error_message, False 
                    else:
                        return result.stdout.strip(), True  

                except subprocess.TimeoutExpired:
                    return "Query execution timed out!", False  

                except Exception as e:
                    return f"Execution error: {str(e)}", False 
                
def save_mongo_cs(connection_string):
    global CONNECTION_STRING
    CONNECTION_STRING = connection_string
