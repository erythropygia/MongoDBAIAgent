import subprocess, time, re, os, yaml, sys, json
from source.process.qwen_process import generate_local
from source.process.gemini_process import generate_gemini
from source.code_executor import CodeExecutor

CONSERVATIONS = []
CODE_EXECUTOR = CodeExecutor()


with open("prompts.yaml", "r", encoding="utf-8") as file:
    prompts = yaml.safe_load(file)

def generate(method, first_user_query, schema, repaired_query, is_first = False):
    global CONSERVATIONS
    global CODE_EXECUTOR
    try_count = 0
    if is_first:
        CONSERVATIONS = []

    print("Generating Query...")
    if method == 0:
        prompt = prompts["generate_mongo_query_qwen"].format(schema=schema, user_query=first_user_query)
        CONSERVATIONS.append({'role': "user", "content": prompt})

        response = generate_local(CONSERVATIONS, new_chat=True)
        CONSERVATIONS.append({'role': "assistant", "content": response})

        while(try_count < 3):
            result, is_successful = CODE_EXECUTOR.execute_generated_code(response)
            CONSERVATIONS.append({'role': "user", "content": result})
 
            if is_successful:
                CONSERVATIONS.append({'role': "assistant", "content": response})
                print(CONSERVATIONS)
                return result
            else:
                print(f"Code execution failed. Trying again {try_count + 1}")  
                response = generate_local(CONSERVATIONS)
                result, is_successful = CODE_EXECUTOR.execute_generated_code(response)
                CONSERVATIONS.append({'role': "assistant", "content": response})

                if is_successful:
                    return result
                else:
                    try_count += 1
                    continue   

        print(CONSERVATIONS)
        if not is_successful:
            print("\nCode execution attempts failed. Please try again.\n")
            return None
    
    elif method == 1:
        prompt = prompts["generate_mongo_query_gemini"].format(schema=schema, user_query=first_user_query)
        CONSERVATIONS.append({'role': "user", "content": prompt})

        response = generate_gemini(CONSERVATIONS, new_chat=True)
        CONSERVATIONS.append({'role': "assistant", "content": response})
        
        while(try_count < 3):
            result, is_successful = CODE_EXECUTOR.execute_generated_code(response) 

            if is_successful:
                print(CONSERVATIONS)
                return result
            else:
                print(f"Code execution failed. Trying again {try_count + 1}")
                CONSERVATIONS.append({'role': "user", "content": result})
                response = generate_gemini(CONSERVATIONS, new_chat=False)
                result, is_successful = CODE_EXECUTOR.execute_generated_code(response)
                CONSERVATIONS.append({'role': "assistant", "content": response})

                if is_successful:
                    return result
                else:
                    try_count += 1
                    continue

        print(CONSERVATIONS)
        if not is_successful:
            print("\nCode execution attempts failed. Please try again.\n")
            return None    
    
    elif method == 2:
        response = generate_local(CONSERVATIONS, new_chat=False)
        CONSERVATIONS.append({'role': "user", "content": repaired_query})

        while(try_count < 3):
            result, is_successful = CODE_EXECUTOR.execute_generated_code(response)
            CONSERVATIONS.append({'role': "assistant", "content": response})

            if is_successful:
                print(CONSERVATIONS)
                return result
            else:
                print(f"Code execution failed. Trying again {try_count + 1}")
                CONSERVATIONS.append({'role': "user", "content": result})
                response = generate_local(CONSERVATIONS, new_chat=False)
                CONSERVATIONS.append({'role': "assistant", "content": response})

                result, is_successful = CODE_EXECUTOR.execute_generated_code(response) 

                if is_successful:
                    return result
                else:
                    CONSERVATIONS.append({'role': "user", "content": result})
                    try_count += 1
                    continue   

        print(CONSERVATIONS)
        if not is_successful:
            print("\nCode execution attempts failed. Please try again.\n")
            return None
        
    elif method == 3:
        CONSERVATIONS.append({'role': "user", "content": repaired_query})
        response = generate_gemini(CONSERVATIONS, new_chat=False) 

        while(try_count < 3):
            result, is_successful = CODE_EXECUTOR.execute_generated_code(response) 
            CONSERVATIONS.append({'role': "assistant", "content": response})

            if is_successful:
                print(CONSERVATIONS)
                return result
            else:
                print(f"Code execution failed. Trying again {try_count + 1}")
                CONSERVATIONS.append({'role': "user", "content": result})
                response = generate_gemini(CONSERVATIONS, new_chat=False)
                CONSERVATIONS.append({'role': "assistant", "content": response})

                result, is_successful = CODE_EXECUTOR.execute_generated_code(response)

                if is_successful:
                    return result
                else:
                    CONSERVATIONS.append({'role': "user", "content": result})
                    try_count += 1
                    continue   

        print(CONSERVATIONS)
        if not is_successful:
            print("\nCode execution attempts failed. Please try again.\n")
            return None
    

def save_chat_history():
    folder_path = "chat_history"
    file_path = os.path.join(folder_path, "chat_history.jsonl")

    with open(file_path, "a", encoding="utf-8") as file:
        file.write(json.dumps(CONSERVATIONS, ensure_ascii=False) + "\n")