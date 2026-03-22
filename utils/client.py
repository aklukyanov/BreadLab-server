import os
from dotenv import load_dotenv
from ollama import Client

load_dotenv()

ollama_api_key=os.getenv('ollama_api')
cloud_client = Client(
    host='https://ollama.com',
    headers={'Authorization': f'Bearer {ollama_api_key}'}
)
django_secret_key = os.getenv('django_secret_key')