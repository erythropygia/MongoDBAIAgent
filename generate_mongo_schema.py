import os
import json
from pymongo import MongoClient

def get_field_type(value):
    """MongoDB belgelerindeki veri tipini döndürür."""
    if isinstance(value, dict):
        return "dict"
    elif isinstance(value, list):
        return "list"
    elif isinstance(value, str):
        return "str"
    elif isinstance(value, int):
        return "int"
    elif isinstance(value, float):
        return "float"
    elif isinstance(value, bool):
        return "bool"
    elif "ObjectId" in str(type(value)):
        return "ObjectId"
    elif "datetime" in str(type(value)):
        return "datetime"
    else:
        return "unknown"

def analyze_document_structure(document):
    """Bir belge içindeki tüm alanları ve veri tiplerini analiz eder."""
    field_types = {}

    for key, value in document.items():
        field_type = get_field_type(value)

        if isinstance(value, dict):
            field_types[key] = {"type": "dict", "structure": analyze_document_structure(value)}
        elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
            field_types[key] = {"type": "list", "items": analyze_document_structure(value[0])}
        else:
            field_types[key] = field_type

    return field_types

def extract_mongo_schema(connection_string, schema_file="mongo_schema.json"):
    """Tüm veritabanlarını ve koleksiyonları analiz eder ve şemayı JSON olarak kaydeder."""
    if os.path.exists(schema_file):
        print(f"Schema already exists: {schema_file}")
        return

    client = MongoClient(connection_string)
    schema_info = {}

    for db_name in client.list_database_names():
        if db_name in ["admin", "config", "local"]: 
            continue
        
        db = client[db_name]
        schema_info[db_name] = {}

        for collection_name in db.list_collection_names():
            collection = db[collection_name]
            sample_data = collection.find_one()
            if sample_data:
                schema_info[db_name][collection_name] = analyze_document_structure(sample_data)

    with open(schema_file, "w", encoding="utf-8") as f:
        json.dump(schema_info, f, indent=4, ensure_ascii=False)

    print(f"Schema saved as {schema_file}")
