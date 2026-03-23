"""
Test de conexión a Azure OpenAI
"""
from openai import AzureOpenAI
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

print("=" * 60)
print("TEST DE CONEXIÓN A AZURE OPENAI")
print("=" * 60)

# Verificar que las variables estén cargadas
print("\n🔍 Verificando configuración...")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_GPT4O_MINI")

print(f"Endpoint: {endpoint}")
print(f"Deployment: {deployment}")

if not endpoint or not os.getenv("AZURE_OPENAI_API_KEY"):
    print("\n❌ ERROR: Falta configurar el archivo .env")
    print("Asegúrate de copiar tu API Key y Endpoint")
    exit(1)

# Crear cliente
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=endpoint
)

try:
    print("\n🚀 Enviando mensaje de prueba...")
    
    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": "Eres un asistente útil en español."},
            {"role": "user", "content": "Di 'Hola desde South Central US hacia Argentina!' en una frase corta y amigable."}
        ],
        max_tokens=100,
        temperature=0.7
    )
    
    print("\n" + "=" * 60)
    print("✅ ¡CONEXIÓN EXITOSA!")
    print("=" * 60)
    
    print(f"\n🤖 Respuesta del modelo:")
    print(f"   {response.choices[0].message.content}")
    
    print(f"\n📊 Información del uso:")
    print(f"   Tokens de entrada: {response.usage.prompt_tokens}")
    print(f"   Tokens de salida: {response.usage.completion_tokens}")
    print(f"   Tokens totales: {response.usage.total_tokens}")
    
    # Cálculo de costo (gpt-4o-mini)
    cost = (response.usage.prompt_tokens * 0.00000015) + (response.usage.completion_tokens * 0.0000006)
    print(f"   Costo estimado: ${cost:.8f}")
    
    print("\n✅ Todo funciona correctamente. Puedes continuar con el desarrollo.")
    
except Exception as e:
    print("\n" + "=" * 60)
    print("❌ ERROR DE CONEXIÓN")
    print("=" * 60)
    print(f"\nDetalles del error:\n{e}")
    print("\n🔧 Posibles soluciones:")
    print("1. Verifica que la API Key sea correcta (sin espacios)")
    print("2. Verifica que el Endpoint termine en /")
    print("3. Verifica que el deployment name sea exacto")
    print("4. Espera 2-3 minutos si acabas de crear el deployment")
    print("5. Revisa que el deployment esté en estado 'Succeeded' en Foundry")
