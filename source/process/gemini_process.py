import yaml, sys
from decouple import config
from google import genai
from google.genai import types
from source.utils.logger import RichLogger

logger = RichLogger()

class GeminiProcess:
    def __init__(self):
        try:
            with open("prompts.yaml", "r", encoding="utf-8") as file:
                self.prompts = yaml.safe_load(file)
        except:
            logger.panel("ERROR LOADING prompts.yaml", "Missing prompts.yaml in project folder! Please check your configuration.", style= "bold red")
            sys.exit(1)
            
        try:
            self.GEMINI_TOKEN = config('GEMINI_KEY')
            logger.panel("LOADING .ENV", "GEMINI_KEY INJECTED")
        except:
            logger.panel("ERROR LOADING .ENV", "Missing 'GEMINI_KEY' in config file! Please check your configuration.", style= "bold red")
            self.GEMINI_TOKEN = "API_KEY_REQUIRED"
        self.SYSTEM_MESSAGE = self.prompts["system_message"]
        self.client = genai.Client(api_key=self.GEMINI_TOKEN)
        self.types = types
        self.chat = self.client.chats.create(
            model="gemini-1.5-flash", 
            config=types.GenerateContentConfig(system_instruction=self.SYSTEM_MESSAGE)
        )
    
    def start_new_chat(self):
        try:
            self.chat = self.client.chats.create(
                model="gemini-1.5-flash",
                config=self.types.GenerateContentConfig(system_instruction=self.SYSTEM_MESSAGE)
            )
        except Exception as e:
            logger.panel("GEMINI PROCESS ERROR", f"{repr(e)}")
            sys.exit(1)

    
    def generate_gemini(self, prompts, new_chat=False):
        try:
            if new_chat:
                prompts.insert(0, {'role': "system", "content": self.SYSTEM_MESSAGE, 'model_type': 1})
                self.start_new_chat()
            prompt = self._format_message(prompts)
            response = self.chat.send_message(prompt.strip())
            # Replace streaming prints with formatted log output
            logger.log("Agent: \n\n " + response.text, style="white")
            return response.text
        except Exception as e:
            logger.panel("GEMINI PROCESS ERROR", f"{repr(e)}")
            sys.exit(1)

    def _format_message(self, prompts):
        last_user_message = None
        for message in reversed(prompts):
            if message['role'] == 'user':
                last_user_message = message['content']
                break
        return last_user_message
