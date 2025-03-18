import yaml, time
from decouple import config
from google import genai
from google.genai import types
from source.utils.logger import RichLogger

logger = RichLogger()

class GeminiProcess:
    def __init__(self):
        with open("prompts.yaml", "r", encoding="utf-8") as file:
            self.prompts = yaml.safe_load(file)
        self.GEMINI_TOKEN = config('GEMINI_KEY')
        if not self.GEMINI_TOKEN: 
            logger.panel("ERROR LOADING .ENV", "Missing 'GEMINI_KEY' in config file! Please check your configuration", style= "bold red")
        else:
            logger.panel("LOADING .ENV", "GEMINI_KEY INJECTED")
        self.SYSTEM_MESSAGE = self.prompts["system_message"]
        self.client = genai.Client(api_key=self.GEMINI_TOKEN)
        self.types = types
        self.chat = self.client.chats.create(
            model="gemini-1.5-flash", 
            config=types.GenerateContentConfig(system_instruction=self.SYSTEM_MESSAGE)
        )
    
    def start_new_chat(self):
        self.chat = self.client.chats.create(
            model="gemini-1.5-flash",
            config=self.types.GenerateContentConfig(system_instruction=self.SYSTEM_MESSAGE)
        )
    
    def generate_gemini(self, prompts, new_chat=False):
        if new_chat:
            prompts.insert(0, {'role': "system", "content": self.SYSTEM_MESSAGE})
            self.start_new_chat()
        prompt = self._format_message(prompts)
        response = self.chat.send_message(prompt.strip())
        # Replace streaming prints with formatted log output
        logger.log("Agent: " + response.text)
        return response.text

    def _format_message(self, prompts):
        last_user_message = None
        for message in reversed(prompts):
            if message['role'] == 'user':
                last_user_message = message['content']
                break
        return last_user_message
