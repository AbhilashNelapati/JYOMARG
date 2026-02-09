import google.generativeai as genai

# మీ Gemini API key ఇక్కడ పెట్టండి
genai.configure(api_key="your api key")

print("Available Gemini Models:\n")

for model in genai.list_models():
    print(model.name)
