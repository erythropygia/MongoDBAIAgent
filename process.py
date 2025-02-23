import json
from pymongo import MongoClient
from langchain.llms import LlamaCpp
from rag import get_relevant_schema
import google.generativeai as genai
from decouple import config

GEMINI_TOKEN = config('GEMINI_KEY')
genai.configure(api_key=GEMINI_TOKEN)

MODEL_PATH = "model/Qwen2.5.1-Coder-7B-Instruct-Q6_K.gguf"

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

def generate_mongo_query_local(user_query, schema):
    """LLaMA veya GGUF modeli ile doğal dildeki sorguyu MongoDB query'ye çevirir."""
    prompt = f"""
    Given the following MongoDB schema:
    {schema}

    Convert the following user query into a MongoDB query:
    "{user_query}"

    Return only the JSON query without any explanation.
    """

    response = llm.invoke(prompt)
    return response


def analysis_gemini(request):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(request)
    return response.text

def generate_mongo_query_gemini(user_query, schema):
    """LLaMA veya GGUF modeli ile doğal dildeki sorguyu MongoDB query'ye çevirir."""
    prompt = f"""
    Aşağıdaki mongo db collection şemasını dikkate alarak:
    {schema}

    aşağıdaki soruya ait python'da şu fonksiyonda çalıştırabileceğim bir query öner:
    
    def execute_dynamic_mongo_query(connection_string, query, db_name, collection_name):
    if isinstance(query, str):
        try:
            query = json.loads(query)
        except json.JSONDecodeError:
            print("Invalid JSON format.")
            return []

    client = MongoClient(connection_string)
    db = client[db_name]
    collection = db[collection_name]

    if "filter" in query.get("query", ):
        for condition in query["query"]["filter"]:
            key = condition.get("key")
            value = condition.get("value")
            if key and value:
                query_filter[key] = value

    sort_list = []
    sort = query.get("query", ).get("sort", [])
    for item in sort:
        if "key" in item and "order" in item:
            sort_list.append((item["key"], item["order"]))

    limit = query.get("limit", 0)

    select = query.get("select", [])

    projection = "field: 1 for field in select if select else None

    if sort_list:
        results = list(collection.find(query_filter, projection).sort(sort_list).limit(limit))
    else:
        results = list(collection.find(query_filter, projection).limit(limit))

    def convert_objectid_to_str(item):
        for key, value in item.items():
            if isinstance(value, ObjectId):
                item[key] = str(value)  
            elif isinstance(value, dict): 
                convert_objectid_to_str(value)
            elif isinstance(value, list): 
                for sub_item in value:
                    if isinstance(sub_item, dict):
                        convert_objectid_to_str(sub_item)
        return item

    results = [convert_objectid_to_str(result) for result in results]
    return results
    
    {user_query}

    Sadece query'i döndür başka herhangi bir bilgi verme.
    """

    response = analysis_gemini(prompt.strip())
    return response
