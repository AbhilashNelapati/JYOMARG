import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

try:
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    print("మీ సిస్టమ్ సపోర్ట్ చేసే మోడల్స్ ఇవే:")
    for m in models:
        print(f"- {m}")
except Exception as e:
    print(f"Error: {e}")