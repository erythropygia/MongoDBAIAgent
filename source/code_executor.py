import subprocess, os, sys
import time, random, string
from source.utils.logger import RichLogger

logger = RichLogger()

CONNECTION_STRING = ""

class CodeExecutor:
    def __init__(self):
        pass
    
    def extract_and_update_mongodb_connection_string(self, text):
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

        script, status = self.extract_and_update_mongodb_connection_string(code)

        if status == False:
            return "Script execution failed. Reason: Python script was not found in response's ```python ``` structure.", False 
        
        random_str = ''.join(random.choices(string.ascii_lowercase, k=5))
        unique_file_name = f"generated_scripts/generated_mongo_query_{int(time.time())}_{random_str}.py"

        # Kullanıcının kodunu try-except bloğuna saran yeni kod yapısı
        wrapped_script = f"""
    import sys
    import traceback

    try:
    {script}
        print("SCRIPT_EXECUTION_SUCCESS")  # Başarıyla tamamlandı mesajı
    except Exception as e:
        print("Handled Exception:", str(e), file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)  # Hata olduğunu belirtmek için exit code 1
    """

        with open(unique_file_name, "w", encoding="utf-8") as f:
            f.write(wrapped_script)

        try:
            script_dir = os.path.dirname(os.path.abspath(unique_file_name))
            python_cmd = "python" if sys.platform.startswith("win") else "python3"
            result = subprocess.run(
                [python_cmd, unique_file_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60
            )

            stdout_output = result.stdout.strip()
            stderr_output = result.stderr.strip()

            if result.returncode != 0:
                error_message = (
                    f"Script execution failed with exit code {result.returncode}.\n"
                    f"STDOUT:\n{stdout_output}\n\n"
                    f"STDERR:\n{stderr_output}"
                )
                return error_message, False  
            else:
                # SCRIPT_EXECUTION_SUCCESS mesajı var mı kontrol edelim
                if "SCRIPT_EXECUTION_SUCCESS" in stdout_output:
                    return stdout_output.replace("SCRIPT_EXECUTION_SUCCESS", "").strip(), True  
                else:
                    return (
                        f"Script executed, but success confirmation was not found.\n"
                        f"STDOUT:\n{stdout_output}\n\n"
                        f"STDERR:\n{stderr_output}",
                        False
                    )

        except subprocess.TimeoutExpired:
            return "Query execution timed out!", False  

        except Exception as e:
            return f"Execution error: {str(e)}", False  

    def save_mongo_cs_for_execute(self, connection_string):
        global CONNECTION_STRING
        CONNECTION_STRING = connection_string
