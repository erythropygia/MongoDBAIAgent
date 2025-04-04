import yaml
import sys
import os
from llama_cpp import Llama, llama_log_set
import ctypes
from transformers import AutoTokenizer
from source.utils.logger import RichLogger

logger = RichLogger()

def disable_verbose_llama_log(level, message, user_data):
    pass

log_callback = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p, ctypes.c_void_p)(disable_verbose_llama_log)
llama_log_set(log_callback, ctypes.c_void_p())

# Preventing parallelism warnings for tokenizers
os.environ["TOKENIZERS_PARALLELISM"] = "false"

LLM = None
TOKENIZER = AutoTokenizer.from_pretrained("erythropygia/Gemma-3-1b-it-OpenR1-Turkish")

class GemmaProcess:
    def __init__(self):
        # Load prompts from YAML file
        try:
            with open("prompts.yaml", "r", encoding="utf-8") as file:
                self.prompts = yaml.safe_load(file)
        except:
            logger.panel("ERROR LOADING prompts.yaml", "Missing prompts.yaml in project folder! Please check your configuration.", style= "bold red")
            sys.exit(1)

        self.MODEL_PATH = "model/gemma3_r1.gguf"
        self.SYSTEM_MESSAGE = ""

        if "r1" in self.MODEL_PATH or "R1" in self.MODEL_PATH:
            self.SYSTEM_MESSAGE = self.prompts["system_message_with_user_request"]
        else:
            self.SYSTEM_MESSAGE = self.prompts["system_message_with_user_request"]

    def initialize_model(self):
        global LLM
        """Initialize the LLaMA model for Gemma3"""
        max_context_window = 32768
        LLM = Llama(model_path=self.MODEL_PATH,
                    n_gpu_layers=100,
                    n_ctx=max_context_window,
                    verbose=False)

    def _format_message(self, prompts):
        """Format the messages into a structure compatible with Gemma3 model"""
        last_user_message = None
        for message in reversed(prompts):
            if message['role'] == 'user':
                last_user_message = message['content']
                break
        return last_user_message

    def generate_gemma(self, prompts, new_chat=False):
        """Generate a response using the Qwen model based on input prompts"""
        global LLM

        context = self._format_chat_template(prompts)

        stream = LLM(context,
                          max_tokens=1024,
                          repeat_penalty=1.05,
                          temperature=1.0,
                          top_p=0.95,
                          top_k=128,
                          stream=True)

        assistant_message = ""
        print("Agent: \n")
        for output in stream:
            token_text = output["choices"][0]["text"]
            print(token_text, end="", flush=True)
            assistant_message += token_text

        sys.stdout.write("\n")
        sys.stdout.flush()

        return assistant_message

    def _format_chat_template(self, prompts):
        """Format the chat prompts using the tokenizer"""
        global TOKENIZER
        return TOKENIZER.apply_chat_template(
            prompts,
            tokenize=False,
            add_generation_prompt=True
        )
    
    def my_log_callback(self, level, message, user_data):
        pass

