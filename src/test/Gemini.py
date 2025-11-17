import google.generativeai as genai
from config.settings import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

print("🔍 Listando modelos Gemini disponíveis:")
print("="*50)

try:
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"✅ {model.name}")
            print(f"   Descrição: {model.description}")
            print(f"   Métodos: {model.supported_generation_methods}")
            print("-" * 30)
except Exception as e:
    print(f"❌ Erro ao listar modelos: {e}")