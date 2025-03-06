import json, os
from pymongo import MongoClient
from langchain_community.llms import LlamaCpp
import google.generativeai as genai
from decouple import config
import subprocess
import time
import re
import yaml
from source.text_class import LoadingAnimation

GEMINI_TOKEN = config('GEMINI_KEY')
genai.configure(api_key=GEMINI_TOKEN)

MODEL_PATH = "model/qwen2.5-coder-3b-instruct-fp16.gguf"

GENERATED_SCRIPT_PATH = "run_script/generated_mongo_query.py"

with open("prompts.yaml", "r", encoding="utf-8") as file:
    prompts = yaml.safe_load(file)

"""
llm = LlamaCpp(
    model_path=MODEL_PATH,
    temperature=0.7,          # --temp 0.7
    max_tokens=512,           # Çıktı uzunluğunu artırdım (default 256'ydı)
    top_p=0.95,               # Modelin olasılık seçimlerini dengelemek için
    repeat_penalty=1.1,       # --repeat-penalty 1.1
    n_ctx=8192,               # --ctx-size 8192
    n_threads=32,             # --threads 32
    n_gpu_layers=45,          # --n-gpu-layers 45 (GPU hızlandırması için)
    rope_freq_base=10000,     # --rope-freq-base 10000 (Uzun bağlam frekansı)
    rope_freq_scale=0.5,      # --rope-freq-scale 0.5 (Bağlam ölçekleme)
    use_mlock=True,          # --mlock (Belleği kilitle)
)
"""

def analysis_gemini(request):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(request)
    return response.text

def select_generate_method(method, user_query = None, schema = None, script = None, execution_query = None, error_feedbacks = None):
    loading = LoadingAnimation("Generating Query...")
    loading.start()
    if method == 0:
        loading.stop()
        return generate_mongo_query_local(user_query, schema)
    elif method == 1:
        loading.stop()
        return generate_mongo_query_gemini(user_query, schema)
    elif method == 2:
        loading.stop()
        return failed_response_repair(user_query, script, execution_query, schema, error_feedbacks)

    
def generate_example_queries(db_name, collection, structure):
    prompt = prompts["generate_example_queries"].format(db_name=db_name, collection=collection, structure=structure)
    try:
        response = analysis_gemini(prompt.strip())
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
    
def generate_mongo_query_local(user_query, schema):
    """LLaMA veya GGUF modeli ile doğal dildeki sorguyu MongoDB query'ye çevirir."""
    prompt = prompts["generate_mongo_query"].format(schema=schema, user_query=user_query)
    # response = llm.invoke(prompt)
    # return response

def generate_mongo_query_gemini(user_query, schema):
    prompt = prompts["generate_mongo_query"].format(schema=schema, user_query=user_query)
    response = analysis_gemini(prompt.strip())
    return response

def failed_response_repair(user_query, script, execution_query, schema, error_feedbacks):
    prompt = prompts["failed_response_repair"].format(schema=schema, script=script, user_query=user_query, execution_query=execution_query, error_feedbacks=error_feedbacks)
    response = analysis_gemini(prompt.strip()) 
    return response

def clean_and_replace_connection_string(code, connection_string):
    """Kodun başındaki ```python ve ``` işaretlerini temizler, bağlantı dizisini değiştirir."""
    code = code.replace("```python", "").replace("```", "").strip()
    
    code = code.replace('pymongo.MongoClient("mongodb://localhost:27017/")', 
                        f'pymongo.MongoClient("{connection_string}")')
    
    return code

def execute_generated_code(code, connection_string):
    loading = LoadingAnimation("Running script")
    loading.start()

    code = clean_and_replace_connection_string(code, connection_string)

    with open(GENERATED_SCRIPT_PATH, "w", encoding="utf-8") as f:
        f.write(code)

    try:
        script_dir = os.path.dirname(os.path.abspath(GENERATED_SCRIPT_PATH))

        result = subprocess.run(["python", GENERATED_SCRIPT_PATH], capture_output=True, text=True, timeout=20)
        loading.stop()
        return result.stdout.strip()
    
    except subprocess.TimeoutExpired:
        loading.stop()
        return "Query execution timed out!"
    
    except Exception as e:
        loading.stop()
        return f"Execution error: {str(e)}"

