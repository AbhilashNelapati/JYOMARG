import google.generativeai as genai

# మీ Gemini API key ఇక్కడ పెట్టండి
genai.configure(api_key="AIzaSyBaiiDlkgofDurGYHDz2zjttoGL7gvG0OQ")

print("Available Gemini Models:\n")

for model in genai.list_models():
    print(model.name)
