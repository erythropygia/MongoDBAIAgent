from google import genai
from google.genai import types
from decouple import config
import yaml, time

GEMINI_TOKEN = config('GEMINI_KEY')

with open("prompts.yaml", "r", encoding="utf-8") as file:
    prompts = yaml.safe_load(file)

system_message = prompts["system_message"]


client = genai.Client(api_key= GEMINI_TOKEN)
chat = client.chats.create(model="gemini-1.5-flash", 
                               config=types.GenerateContentConfig(
                               system_instruction=system_message))


def generate_gemini(prompt):
    response = chat.send_message(prompt.strip())
    return response.text
