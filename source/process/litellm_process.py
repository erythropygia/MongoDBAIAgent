import yaml, sys
from decouple import config
from source.utils.logger import RichLogger
import litellm

logger = RichLogger()

class LiteLLMProcess:
    def __init__(self):
        try:
            self.model_name = config("OLLAMA_MODEL")
            logger.panel("LOADING CONFIG", f"Model: {self.model_name}")
        except Exception as e:
            logger.panel("ERROR LOADING .ENV", str(e), style="bold red")
            sys.exit(1)

        self.llm_config = {
            "model": self.model_name,
        }

        try:
            with open("prompts.yaml", "r", encoding="utf-8") as file:
                self.prompts = yaml.safe_load(file)
        except:
            logger.panel("ERROR LOADING prompts.yaml", "Missing prompts.yaml in project folder! Please check your configuration.", style= "bold red")
            sys.exit(1)

        self.SYSTEM_MESSAGE = self.prompts["system_message"]
        self.SYSTEM_MESSAGE_SHORT = self.prompts["system_message"]

    def generate_ollama(self, prompts, new_chat=False):
        try:
            if new_chat:
                prompts.insert(0, {'role': "system", "content": self.SYSTEM_MESSAGE, 'model_type': 3})
            else:
                prompts.insert(len(prompts) - 1, {'role': "system", "content": self.SYSTEM_MESSAGE_SHORT, 'model_type': 3})
        
            response = litellm.completion(
                **self.llm_config,
                messages= prompts
            )

            assistant_reply = response["choices"][0]["message"]["content"]
            logger.log("Agent:\n\n" + assistant_reply, style="white")
            return assistant_reply

        except Exception as e:
            logger.panel("LLM ERROR", f"{repr(e)}", style="bold red")
            sys.exit(1)