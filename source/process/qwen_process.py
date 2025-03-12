from llama_cpp import Llama
import yaml, sys, os

os.environ["TOKENIZERS_PARALLELISM"] = "false"
MODEL_PATH = "model/unsloth_r1_.Q4_K_M.gguf"
LLM = None

with open("prompts.yaml", "r", encoding="utf-8") as file:
    prompts = yaml.safe_load(file)


def wake_up_qwen():
    max_context_window = 8192
    global LLM
    LLM = Llama(model_path= MODEL_PATH,
                n_gpu_layers=100,
                n_ctx=max_context_window)
    

chat_history = []

def generate_local(prompt):
    """LLaMA veya GGUF modeli ile doğal dildeki sorguyu MongoDB query'ye çevirir."""
    global chat_history

    if "r1" in MODEL_PATH:
        system_message = prompts["system_message_r1"]
    else:
        system_message = prompts["system_message"]

    if len(chat_history) >= 9:
        chat_history.clear()

    if len(chat_history) == 0:
        chat_history.append(f"<|im_start|>system\n{system_message}<|im_end|>")

    formatted_user_message = f"<|im_start|>user\n{prompt}<|im_end|>"
    chat_history.append(formatted_user_message)

    context = "\n".join(chat_history) + "\n<|im_start|>assistant\n"

    stream = LLM(context, 
                 max_tokens=1024,
                 repeat_penalty=1.05, 
                 temperature=0.7,                
                 top_k=40,
                 top_p=0.95,
                 stop=["<|im_end|>"], 
                 stream=True)  

    print("Agent: ", end="", flush=True)

    assistant_message = ""  

    for output in stream:
        token_text = output["choices"][0]["text"]
        print(token_text, end="", flush=True)
        assistant_message += token_text  

    sys.stdout.write("\n")  
    sys.stdout.flush()
    
    formatted_assistant_message = f"<|im_start|>assistant\n{assistant_message}<|im_end|>"
    chat_history.append(formatted_assistant_message)

    return assistant_message

