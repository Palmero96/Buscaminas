import os
import google.generativeai as genai
from dotenv import load_dotenv

# Cargar entorno
load_dotenv()

# Configurar API
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ Error: No se encontró GOOGLE_API_KEY en el archivo .env")
    exit()

genai.configure(api_key=api_key)

print("🔍 Consultando a Google qué modelos tienes disponibles...")
print("-------------------------------------------------------")

try:
    # Listar modelos
    for m in genai.list_models():
        # Filtramos solo los que sirven para generar texto (chat)
        if 'generateContent' in m.supported_generation_methods:
            print(f"👉 Nombre real: {m.name}")
except Exception as e:
    print(f"❌ Error de conexión: {e}")