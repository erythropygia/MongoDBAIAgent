import json, os, yaml, re, sys
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pandas as pd
from source.utils.logger import RichLogger

import warnings, logging
warnings.filterwarnings("ignore", category=DeprecationWarning) 
warnings.filterwarnings("ignore", category=Warning)
warnings.filterwarnings('ignore',category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)
logging.getLogger("tensorflow").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

os.environ["TRANSFORMERS_VERBOSITY"] = "error" 
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

logger = RichLogger()

class RagHandler:
    def __init__(self):
        self.SCHEMA_FILE = "mongo_schema/mongo_schema.json"
        self.SCHEMA_DOC_FILE = "mongo_schema/mongo_schema_doc.yaml"
        self.FAISS_INDEX = "faiss_mongo_schema"
        self.FAISS_DB = None
        self.MAX_COLLECTION_COUNTS = 0
        self.EXCEL_FILE = "faiss_mongo_schema/queries_for_rag.xlsx"

    def load_schema_into_faiss(self):
        """YAML şemasını FAISS içine yükler ve örnek sorguları ekler."""
        if os.path.exists(self.FAISS_INDEX):
            logger.panel("INFO", "FAISS index already exists. This process is skipped.. Loading FAISS schema", style="bold blue")
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            self.FAISS_DB = FAISS.load_local(self.FAISS_INDEX, embeddings, allow_dangerous_deserialization=True)
            return

        logger.log("Generating FAISS schema")
        logger.log("Checking YAML File")
        if not os.path.exists(self.SCHEMA_DOC_FILE):
            logger.log(f"ERROR: YAML file not found: {self.SCHEMA_DOC_FILE}. Please ensure you have created the file and it is in the correct path.", style="bold red")
            return

        with open(self.SCHEMA_DOC_FILE, "r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)

        logger.log("YAML Data Loaded")

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

        docs = []
        metadata = []

        for entry_number, entry_string in yaml_data.items():
            try:
                entry_dict = yaml.safe_load(entry_string)  
            except yaml.YAMLError as e:
                logger.log(f"ERROR: YAML parsing failed for entry {entry_number}: {e}", style="bold red")
                return

            if isinstance(entry_dict, dict) and entry_dict:
                db_name = entry_dict.get("DBName", "")
                collection_name = entry_dict.get("Collection", "")
                description = entry_dict.get("Description", "")

                enums = entry_dict.get("Enums", {})
                enums_explain = entry_dict.get("EnumsDescription", {})

                enums_str = " | ".join([f"{key}: {', '.join(value)}" for key, value in enums.items()]) if enums else None
                enums_description_str = " | ".join([f"{key}: {value}" for key, value in enums_explain.items()]) if enums_explain else None

                doc_text = f"DBName: {db_name}, Collection: {collection_name}, Description: {description}"
                if enums_str:
                    doc_text += f", Enums: {enums_str}"
                if enums_description_str:
                    doc_text += f", EnumsDescription: {enums_description_str}"

                docs.append(doc_text)

                meta_entry = {
                    "DBName": db_name,
                    "Collection": collection_name,
                    "Description": description,
                }
                if enums_str:
                    meta_entry["Enums"] = enums_str
                if enums_description_str:
                    meta_entry["EnumsDescription"] = enums_description_str

                metadata.append(meta_entry)

        split_texts = []
        split_metadata = []

        logger.log("Loading schema into FAISS... Indexing Schema")

        for i, doc in enumerate(docs):
            split_parts = text_splitter.split_text(doc)
            split_texts.extend(split_parts)
            split_metadata.extend([metadata[i]] * len(split_parts))

        faiss_db = FAISS.from_texts(split_texts, embeddings, metadatas=split_metadata)
        faiss_db.save_local(self.FAISS_INDEX)

        logger.log("Schema successfully loaded into FAISS.\n")
        self.FAISS_DB = FAISS.load_local(self.FAISS_INDEX, embeddings, allow_dangerous_deserialization=True)

    def get_relevant_schema(self, user_query, similarity_threshold=0.55):
        logger.panel("SEARCHING SCHEMA", f"Getting relevant schema for your query... (threshold: %{similarity_threshold*100})", style= "bold yellow")

        if self.MAX_COLLECTION_COUNTS == 0:
            self.MAX_COLLECTION_COUNTS = self.get_max_collection_counts()
            if self.MAX_COLLECTION_COUNTS == 0:
                logger.log("ERROR: Maximum collection count not found. Please check the YAML schema file.", style="bold red")
                sys.exit(1)
        
        docs = self.FAISS_DB.similarity_search_with_score(user_query, k=self.MAX_COLLECTION_COUNTS)

        if not docs:
            return []

        schema_info_list = []

        for doc, score in docs:
            similarity_score = 1 / (1 + score) 
            
            if similarity_score < similarity_threshold:
                continue  

            schema_info = {
                "DBName": doc.metadata.get("DBName", ""), 
                "Collection": doc.metadata.get("Collection", ""),
                "Description": doc.metadata.get("Description", ""),
                "Enums": doc.metadata.get("Enums", "None"), 
                "EnumsDescription": doc.metadata.get("EnumsDescription", None),
                "Schema": self.get_mongo_schema(doc.metadata.get("DBName", ""), doc.metadata.get("Collection", "")),
                "SimilarityScore": similarity_score 
            }

            schema_info_list.append(schema_info)

        for schema_info in schema_info_list:
            logger.table("Found Schema Information", schema_info)
        
        formatted_schema = json.dumps(schema_info_list, indent=4, ensure_ascii=False)
        return formatted_schema

    def get_max_collection_counts(self):
        try:
            with open(self.SCHEMA_DOC_FILE, 'r', encoding='utf-8') as file:
                content = file.read()

            matches = re.findall(r'^(\d+):', content, re.MULTILINE)

            if matches:
                max_count = max(map(int, matches))
                return max_count
            else:
                return 0 

        except FileNotFoundError:
            logger.log(f"ERROR: '{self.SCHEMA_DOC_FILE}' not found.", style="bold red")
            return 0
        except Exception as e:
            logger.log(f"ERROR: An error occurred while reading the YAML file: {e}", style="bold red")
            return 0
        
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
