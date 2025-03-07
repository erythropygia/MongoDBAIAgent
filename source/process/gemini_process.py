import google.generativeai as genai
from decouple import config
import yaml

GEMINI_TOKEN = config('GEMINI_KEY')
genai.configure(api_key=GEMINI_TOKEN)

def generate_gemini(prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt.strip())
    return response.text



