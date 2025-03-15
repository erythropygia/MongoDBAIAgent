from llama_cpp import Llama
import yaml, sys, os
from transformers import AutoTokenizer

os.environ["TOKENIZERS_PARALLELISM"] = "false"
with open("prompts.yaml", "r", encoding="utf-8") as file:
    prompts = yaml.safe_load(file)


MODEL_PATH = "model/Qwen2.5.1-Coder-7B-Instruct-Q6_K.gguf"
LLM = None
SYSTEM_MESSAGE = ""
TOKENIZER = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")

if "r1" in MODEL_PATH:
    SYSTEM_MESSAGE = prompts["system_message_r1"]
else:
    SYSTEM_MESSAGE = prompts["system_message"]


def wake_up_qwen():
    max_context_window = 8192
    global LLM
    LLM = Llama(model_path= MODEL_PATH,
                n_gpu_layers=100,
                n_ctx=max_context_window)
    

def generate_local(prompts, new_chat=False):
    """LLaMA veya GGUF modeli ile doğal dildeki sorguyu MongoDB query'ye çevirir."""
    global SYSTEM_MESSAGE

    if new_chat == True:
        prompts.insert(0, {'role': "system", "content": SYSTEM_MESSAGE})

    context = format_chat_template(prompts)

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
    
    return assistant_message

def format_chat_template(prompts):
    global TOKENIZER
    global SYSTEM_MESSAGE

    text = TOKENIZER.apply_chat_template(
        prompts,
        tokenize=False,
        add_generation_prompt=True
    )

    return text

    
