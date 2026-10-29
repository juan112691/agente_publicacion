
# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Carga las variables del .env ubicado junto a agente.py.
load_dotenv(BASE_DIR / ".env")

# URL del backend administrativo.
SERVIDOR_URL = os.getenv(
    "AINSA_SERVIDOR_URL",
    "http://127.0.0.1:8000"
).rstrip("/")

# Acepta el nombre del token del agente o el del administrador.
AGENT_TOKEN = (
    os.getenv("AINSA_AGENT_TOKEN")
    or os.getenv("AGENT_TOKEN", "")
)

# Modelo multimodal que utilizará el agente.
OLLAMA_MODEL = os.getenv("AINSA_OLLAMA_MODEL", "llava")

HTTP_TIMEOUT = 10

# Directorios del agente.
DIR_ENTRADA = BASE_DIR / "imagenes_brutas"
DIR_SALIDA = BASE_DIR / "publicaciones"
DIR_PROCESADAS = BASE_DIR / "procesadas"
DIR_PLANTILLAS = BASE_DIR / "plantillas"
