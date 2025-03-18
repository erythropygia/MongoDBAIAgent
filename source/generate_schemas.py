import os
import json
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import certifi
from source.utils.logger import RichLogger

logger = RichLogger()

class SchemaExtractor:
    def __init__(self):
        pass

    def db_connection_check(self, connection_string):
        try:
            client = MongoClient(connection_string, serverSelectionTimeoutMS=3000)
            client.admin.command('ping') 
            return True
        except ConnectionFailure:
            return False

    def get_field_type(self, value):
        """MongoDB belgelerindeki veri tipini döndürür."""
        if isinstance(value, dict):
            return "dict"
        elif isinstance(value, list):
            return "list"
        elif isinstance(value, bool):
            return "bool"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, str):
            return "str"
        elif "ObjectId" in str(type(value)):
            return "ObjectId"
        elif "datetime" in str(type(value)):
            return "datetime"
        else:
            return "unknown"

    def analyze_document_structure(self, document):
        """Bir belge içindeki tüm alanları ve veri tiplerini analiz eder."""
        field_types = {}

        for key, value in document.items():
            field_type = self.get_field_type(value)

            if isinstance(value, dict):
                field_types[key] = {"type": "dict", "structure": self.analyze_document_structure(value)}
            elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                field_types[key] = {"type": "list", "items": self.analyze_document_structure(value[0])}
            else:
                field_types[key] = field_type

        return field_types

    def extract_schemas(self, connection_string, schema_file="mongo_schema.json", schema_doc_file="mongo_schema_doc.yaml", schema_path="./mongo_schema/"):
        """Tüm veritabanlarını ve koleksiyonları analiz eder, şemayı JSON olarak ve YAML dokümanını kaydeder."""
        logger.log("Extracting Schema")

        os.makedirs(schema_path, exist_ok=True)  # Klasör yoksa oluştur

        if os.path.exists(schema_path + schema_file):
            logger.log(f"JSON Schema already exists: {schema_path + schema_file}")
        if os.path.exists(schema_path + schema_doc_file):
            logger.log(f"YAML Document Schema already exists: {schema_path + schema_doc_file}")
            return

        client = MongoClient(connection_string, tlsCAFile=certifi.where())
        schema_info = {}
        yaml_doc_content = ""
        entry_counter = 1

        for db_name in client.list_database_names():
            if db_name in ["admin", "config", "local"]:
                continue

            db = client[db_name]
            schema_info[db_name] = {}

            for collection_name in db.list_collection_names():
                collection = db[collection_name]
                sample_data = collection.find_one()
                if sample_data:
                    schema_info[db_name][collection_name] = self.analyze_document_structure(sample_data)
                    yaml_doc_content += f"""{entry_counter}: |
  DBName: "{db_name}"
  Collection: "{collection_name}"
  Description: "Default Description {db_name} - {collection_name}"
  Enums: {{}}
  EnumsDescription: {{}}

"""
                    entry_counter += 1

        with open(schema_path + schema_file, "w", encoding="utf-8") as f:
            json.dump(schema_info, f, indent=4, ensure_ascii=False)
        logger.log(f"JSON Schema saved as {schema_file}")

        with open(schema_path + schema_doc_file, "w", encoding="utf-8") as f:
            f.write(yaml_doc_content)
        logger.log(f"YAML Document Schema saved as {schema_doc_file}")

        logger.log("*************WARNING*************", style="bold red")
        logger.log("Please update the YAML document with descriptions and enums (e.g., see example/mongo_schema_doc.yaml), then delete the faiss_mongo_schema folder and run the script again", style="bold red")
        logger.log("Default parameters using")
        logger.log("*********************************")
