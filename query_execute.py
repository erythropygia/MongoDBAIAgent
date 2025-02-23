import json
from pymongo import MongoClient

from pymongo import MongoClient
import json
from bson import ObjectId

def execute_dynamic_mongo_query(connection_string, query, db_name, collection_name):
    print(f"Query: {query}, Database: {db_name}, Collection: {collection_name}")

    if isinstance(query, str):
        try:
            query = json.loads(query)
        except json.JSONDecodeError:
            print("Invalid JSON format.")
            return []

    client = MongoClient(connection_string)
    db = client[db_name]
    collection = db[collection_name]

    query_filter = {}
    if "filter" in query.get("query", {}):
        for condition in query["query"]["filter"]:
            key = condition.get("key")
            value = condition.get("value")
            if key and value:
                query_filter[key] = value

    sort_list = []
    sort = query.get("query", {}).get("sort", [])
    for item in sort:
        if "key" in item and "order" in item:
            sort_list.append((item["key"], item["order"]))

    limit = query.get("limit", 0)

    select = query.get("select", [])

    projection = {field: 1 for field in select} if select else None

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



def clear_mongo_query(query):
    mongo_query = query.replace("```json", "").replace("```", "")
    print(mongo_query)
    errors = []
    start_index = mongo_query.find('{')
    end_index = mongo_query.rfind('}')
    
    if start_index == -1 or end_index == -1:
        errors.append("Invalid Mongo Query format")
    
    mongo_query = mongo_query[start_index:end_index + 1]

    open_count = 0
    close_count = 0
    
    for char in mongo_query:
        if char == '{':
            open_count += 1
        elif char == '}':
            close_count += 1
        if close_count > open_count: 
            errors.append("Unbalanced brackets: More closing braces than opening braces.")
    
    if open_count != close_count:
        errors.append("Unbalanced brackets: Opening and closing braces do not match.")
    
    while close_count > open_count:
        mongo_query = mongo_query[:-1]
        close_count -= 1

    try:
        if mongo_query.startswith("{") and mongo_query.endswith("}"):
            return mongo_query
    except:
        errors.append("Invalid JSON format.")
        if errors:
            for error in errors:
                print(error)
            return None



