from google import genai; import os
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
for m in client.models.list(): 
    if "veo" in m.name.lower(): 
        print(m.name, m.supported_generation_methods) 