
# config.py
import os

# URL base de tu servidor, sin "/" al final.
SERVIDOR_URL = os.getenv(
    "AINSA_SERVIDOR_URL",
    "http://127.0.0.1:8000"
).rstrip("/")

# Token compartido entre el servidor y el agente.
AGENT_TOKEN = os.getenv("AINSA_AGENT_TOKEN", "")

# Modelo instalado localmente con Ollama.
OLLAMA_MODEL = os.getenv("AINSA_OLLAMA_MODEL", "llava")

# Tiempo máximo para las peticiones HTTP al servidor.
HTTP_TIMEOUT = 10

# Directorios locales.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
