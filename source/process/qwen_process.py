from llama_cpp import Llama
import yaml, sys, os
from transformers import AutoTokenizer

os.environ["TOKENIZERS_PARALLELISM"] = "false"
with open("prompts.yaml", "r", encoding="utf-8") as file:
    prompts = yaml.safe_load(file)


MODEL_PATH = "model/unsloth_r1_.Q4_K_M.gguf"
LLM = None
TOKENIZER = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")


SYSTEM_MESSAGE = ""
SYSTEM_MESSAGE_SHORT = ""

if "r1" or "R1" in MODEL_PATH:
    SYSTEM_MESSAGE = prompts["system_message_r1"]
    SYSTEM_MESSAGE_SHORT = prompts["system_message_short"]
else:
    SYSTEM_MESSAGE = prompts["system_message"]


def wake_up_qwen():
    max_context_window = 32000
    global LLM
    LLM = Llama(model_path= MODEL_PATH,
                n_gpu_layers=100,
                n_ctx=max_context_window)
    

def generate_local(prompts, new_chat=False):
    """LLaMA veya GGUF modeli ile doğal dildeki sorguyu MongoDB query'ye çevirir."""
    global SYSTEM_MESSAGE
    global SYSTEM_MESSAGE_SHORT

    if new_chat == True:
        prompts.insert(0, {'role': "system", "content": SYSTEM_MESSAGE})
    else:
        prompts.insert(len(prompts) - 1, {'role': "system", "content": SYSTEM_MESSAGE_SHORT})

    context = format_chat_template(prompts)

    stream = LLM(context, 
                 max_tokens=512,
                 repeat_penalty=1.05, 
                 temperature=0.8,                
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

    
