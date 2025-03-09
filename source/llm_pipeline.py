import subprocess, time, re, os, yaml, sys
from source.text_class import LoadingAnimation
from source.process.qwen_process import generate_local
from source.process.gemini_process import generate_gemini

GENERATED_SCRIPT_PATH = "run_script/generated_mongo_query.py"

with open("prompts.yaml", "r", encoding="utf-8") as file:
    prompts = yaml.safe_load(file)

def select_generate_method(method, user_query = None, schema = None, script = None, execution_query = None, error_feedbacks = None):
    loading = LoadingAnimation("Generating Query...")
    print("Generating Query...")
    loading.start()
    if method == 0:
        loading.stop()
        prompt = prompts["generate_mongo_query_qwen"].format(schema=schema, user_query=user_query)
        return generate_local(prompt)
    elif method == 1:
        loading.stop()
        prompt = prompts["generate_mongo_query_gemini"].format(schema=schema, user_query=user_query)
        return generate_gemini(prompt)
    elif method == 2:
        loading.stop()
        return repair_response(0 ,user_query, script, execution_query, schema, error_feedbacks)
    elif method == 3:
        loading.stop()
        return repair_response(1, user_query, script, execution_query, schema, error_feedbacks)
    
def repair_response(method, user_query, script, execution_query, schema, error_feedbacks):
    if(method == 0):
        prompt = prompts["failed_response_repair_qwen"].format(schema=schema, script=script, user_query=user_query, execution_query=execution_query, error_feedbacks=error_feedbacks)
        response = generate_local(prompt.strip())
        return response
    elif(method == 1):
        prompt = prompts["failed_response_repair_gemini"].format(schema=schema, script=script, user_query=user_query, execution_query=execution_query, error_feedbacks=error_feedbacks)
        response = generate_gemini(prompt.strip()) 
        return response

def generate_example_queries(method, db_name, collection, structure):
    try:
        if(method == 0):
            prompt = prompts["generate_example_queries_qwen"].format(db_name=db_name, collection=collection, structure=structure)
            response = generate_local(prompt.strip()) 
        elif(method == 1):
            prompt = prompts["generate_example_queries_gemini"].format(db_name=db_name, collection=collection, structure=structure)
            response = generate_gemini(prompt.strip()) 
    except Exception as e:
        print("ERROR: Example queries not valid")
        return []
    
    json_data = re.findall(r'\[.*\]', response, re.DOTALL)
        
    if json_data:
        time.sleep(5)
        return eval(json_data[0])
    else:
        time.sleep(5)
        print("ERROR: Example queries not valid")
        return []
    

def extract_and_update_mongodb_connection_string(text, connection_string):
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

def execute_generated_code(code, connection_string):
    loading = LoadingAnimation("Running script")
    loading.start()

    code, status= extract_and_update_mongodb_connection_string(code, connection_string)

    if status == False:
        loading.stop()
        return code
    else:
        with open(GENERATED_SCRIPT_PATH, "w", encoding="utf-8") as f:
            f.write(code)

        try:
            script_dir = os.path.dirname(os.path.abspath(GENERATED_SCRIPT_PATH))
            python_cmd = "python" if sys.platform.startswith("win") else "python3"
            result = subprocess.run([python_cmd, GENERATED_SCRIPT_PATH], capture_output=True, text=True, timeout=60)
            loading.stop()
            return result.stdout.strip()
        
        except subprocess.TimeoutExpired:
            loading.stop()
            return "Query execution timed out!"
        
        except Exception as e:
            loading.stop()
            return f"Execution error: {str(e)}"