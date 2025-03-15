from google import genai
from google.genai import types
from decouple import config
import yaml, time

with open("prompts.yaml", "r", encoding="utf-8") as file:
    prompts = yaml.safe_load(file)

GEMINI_TOKEN = config('GEMINI_KEY')
SYSTEM_MESSAGE = prompts["system_message"]


client = genai.Client(api_key= GEMINI_TOKEN)
chat = client.chats.create(model="gemini-1.5-flash", 
                               config=types.GenerateContentConfig(
                               system_instruction=SYSTEM_MESSAGE))


def start_new_chat():
    global chat
    chat = client.chats.create(
        model="gemini-1.5-flash",
        config=types.GenerateContentConfig(system_instruction=SYSTEM_MESSAGE)
    )

def generate_gemini(prompts, new_chat=False):
    global SYSTEM_MESSAGE

    if new_chat == True:
        prompts.insert(0, {'role': "system", "content": SYSTEM_MESSAGE})
        start_new_chat()

    prompt = format_message(prompts)
    response = chat.send_message(prompt.strip())

    print("Agent: ", end="", flush=True)
    print(response.text)

    return response.text
    

def format_message(prompts):
    last_user_message = None
    for message in reversed(prompts):
        if message['role'] == 'user':
            last_user_message = message['content']
            break
    return last_user_message
