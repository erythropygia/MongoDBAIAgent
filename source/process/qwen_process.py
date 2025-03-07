from llama_cpp import Llama
import yaml
import sys

MODEL_PATH = "model/Qwen2.5.1-Coder-7B-Instruct-Q6_K.gguf"
LLM = None

with open("prompts.yaml", "r", encoding="utf-8") as file:
    prompts = yaml.safe_load(file)


def wake_up_qwen():
    max_context_window = 4096
    global LLM
    LLM = Llama(model_path="model/Qwen2.5.1-Coder-7B-Instruct-Q6_K.gguf",
                n_gpu_layers=100,
                n_ctx=max_context_window)


def generate_local(prompt, chat_history=None):
    """LLaMA veya GGUF modeli ile doğal dildeki sorguyu MongoDB query'ye çevirir."""
    system_message = prompts["system_message"]
    prompt_template = f"<|im_start|>system\n{system_message}<|im_end|>\n"
    formatted_user_message = f"<|im_start|>user\n{prompt}<|im_end|>"

    context = prompt_template
    if chat_history:
        for message in chat_history:
            context += message + "\n"
    context += formatted_user_message + "\n<|im_start|>assistant\n"

    stream_text = ""
    stream = LLM(context, max_tokens=4096, temperature=0.7, stop=["<|im_end|>"], stream=True)  

    sys.stdout.write("Agent: ")  # print() yerine sys.stdout.write() kullanıyoruz
    sys.stdout.flush()  # Tamponu zorla boşalt

    for output in stream:
        token_text = output["choices"][0]["text"]
        sys.stdout.write(token_text)  # Daha hızlı yazdırma
        sys.stdout.flush()  # Buffer'ı hemen temizle, gecikme olmasın
        stream_text += token_text

    sys.stdout.write("\n")  # Yeni satır ekleyerek formatı düzgün tut
    sys.stdout.flush()
    
    return stream_text


    