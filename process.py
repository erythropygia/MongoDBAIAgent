import json
from pymongo import MongoClient
from langchain_community.llms import LlamaCpp
import google.generativeai as genai
from decouple import config
import subprocess
import time
import re
from text_class import LoadingAnimation

GEMINI_TOKEN = config('GEMINI_KEY')
genai.configure(api_key=GEMINI_TOKEN)

MODEL_PATH = "model/qwen2.5-coder-3b-instruct-fp16.gguf"

GENERATED_SCRIPT_PATH = "run_script/generated_mongo_query.py"

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

def select_generate_method(method, user_query, schema, script = None, execution_query = None):
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
        return failed_response_repair(script, execution_query, schema)

    
def generate_example_queries(db_name, collection, structure):
    prompt = f"""
    Aşağıdaki MongoDB Database {db_name} ve Collection {collection} isimlerine dikkat ederek ve aşağıdaki şemaya uyarak:
    {structure}

    Bana Türkçe metinsel olarak örnek güzel üret ve json formatında ver:

    Örnek sorgu: 
    abc@example.com mailli kişi en son ne zaman analiz yapmıştır?

    Cevabın da aşağıdaki gibi bir string json listesi olmalı 
    Örneğin: 
    [
        "ÖRNEK QUERY (METİN OLARAK)",
        "ÖRNEK QUERY2 (METİN OLARAK)",
        "ÖRNEK QUERY3 (METİN OLARAK)",
        .
        .
        .
    ]

    10 adet örnek üret ve sadece JSON listesi verisini senden istediğim gibi döndür.
    """
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
    prompt = f"""
    Given the following MongoDB schema:
    {schema}

    Convert the following user query into a MongoDB query:
    "{user_query}"

    Return only the JSON query without any explanation.
    """

    #response = llm.invoke(prompt)
    #return response

def generate_mongo_query_gemini(user_query, schema):
    prompt = f"""
    Aşağıdaki MongoDB şema(lar)ına dayanarak:
    {schema}

    Kullanıcının şu sorgusunu gerçekleştiren bir Python kodu yaz (bu query eğer veri analizi dışında bir yazma ya da silme işlemi istiyorsa en bu işlemi gerçekleştirme mesajımın en sonundaki işlemi gerçekleştir):
    {user_query}
    
    Sadece Python kodunu döndür ve datalardaki objectId'leri gösterme. Kodda try-catch bloklarıyla birlikte client = pymongo.MongoClient("mongodb://localhost:27017/") yapısını kullan. 
    Eğer kod catch'e düşerse hata mesajı olarak ekrana "Exception" yaz ve kod çalışmayı bitirdiğinde ekrana mutlaka bir response yaz başka hiçbir açıklama ekleme. 

    Eğer gelen query kötü niyetliyse, bir data silme, değiştirme ya da istekteki schema ile alakasızsa bunu gerçekleştirmek ekrana "Bu işlemi gerçekleştirmeye yetkim yok" yazan bir python scripti yaz
    """

    response = analysis_gemini(prompt.strip())
    return response

def failed_response_repair(script, execution_query, schema):
    prompt = f"""
    Aşağıdaki MongoDB şema(lar)ına dayanarak:
    {schema}

    Ürettiğin kodda {script} 
    Aşağıdaki hatayı alıyorum:
    {execution_query}
    
    Bu kodu düzenle ve düzenlerken sadece python kodunu döndür ve kodda try-catch bloklarıyla birlikte client = pymongo.MongoClient("mongodb://localhost:27017/") yapısını kullan. 
    Eğer kod catch'e düşerse hata mesajı olarak ekrana "Exception" yaz ve kod başarıyla çalışırsa ekrana mutlaka bir response yaz başka hiçbir açıklama ekleme. 
    """

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
        result = f"""
        Generated Script:
        {code}
        """
        result = subprocess.run(["python", GENERATED_SCRIPT_PATH], capture_output=True, text=True, timeout=20)
        loading.stop()
        return result.stdout.strip()
    
    except subprocess.TimeoutExpired:
        loading.stop()
        return "Query execution timed out!"
    
    except Exception as e:
        loading.stop()
        return f"Execution error: {str(e)}"
    
