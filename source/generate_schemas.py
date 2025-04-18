import os
import json
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import certifi
from source.utils.logger import RichLogger

logger = RichLogger()

class SchemaExtractor:
    def __init__(self):
        self.SCHEMA_FILE = "mongo_schema/mongo_schema.json"

    def db_connection_check(self, connection_string):
        try:
            client = MongoClient(connection_string, serverSelectionTimeoutMS=3000)
            client.admin.command('ping') 
            return True
        except ConnectionFailure:
            return False

    def _get_field_type(self, value):
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

    def _analyze_document_structure(self, document):
        field_types = {}

        for key, value in document.items():
            field_type = self._get_field_type(value)

            if isinstance(value, dict):
                field_types[key] = {"type": "dict", "structure": self._analyze_document_structure(value)}
            elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                field_types[key] = {"type": "list", "items": self._analyze_document_structure(value[0])}
            else:
                field_types[key] = field_type

        return field_types

    def extract_schemas(self, connection_string, schema_file="mongo_schema.json", schema_doc_file="mongo_schema_doc.yaml", schema_path="./mongo_schema/"):
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
        logger.log("Default parameters using", style="bold red")
        logger.log("*********************************", style="bold red")


    def get_mongo_schema(self, db_name, collection_name):
        try:
            with open(self.SCHEMA_FILE, 'r', encoding='utf-8') as file:
                schema_data = json.load(file)
        except FileNotFoundError:
            logger.log(f"ERROR: Schema file '{self.SCHEMA_FILE}' not found.", style="bold red")
            return None
        except json.JSONDecodeError:
            logger.log(f"ERROR: Schema file '{self.SCHEMA_FILE}' not in a valid JSON format.", style="bold red")
            return None
        except Exception as e:
            logger.log(f"ERROR: An error occurred while reading the schema file: {e}", style="bold red")
            return None

        if db_name in schema_data:
            db_schema = schema_data[db_name]
            if collection_name in db_schema:
                return db_schema[collection_name]
        return None


    def get_all_collections(self):
        try:
            with open(self.SCHEMA_FILE, 'r', encoding='utf-8') as file:
                schema_data = json.load(file)
        except FileNotFoundError:
            logger.log(f"ERROR: Schema file '{self.SCHEMA_FILE}' not found.", style="bold red")
            return
        except json.JSONDecodeError:
            logger.log(f"ERROR: Schema file '{self.SCHEMA_FILE}' not in a valid JSON format.", style="bold red")
            return
        except Exception as e:
            logger.log(f"ERROR: An error occurred while reading the schema file: {e}", style="bold red")
            return

        table_data = []
        result_data = []
        itemno = 1 

        for db_name, collections in schema_data.items():
            for collection_name in collections:
                table_data.append({
                    "DB Name": db_name,
                    "Collection Name": collection_name
                })
                result_data.append({
                    "itemno": itemno,
                    "db_name": db_name,
                    "collection_name": collection_name
                })
                itemno += 1

        logger.table("DB-COLLECTION List", table_data)
        return result_data
