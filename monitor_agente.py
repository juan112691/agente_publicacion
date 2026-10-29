
# monitor_agente.py

import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

import httpx
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Tu archivo de configuración se llama .env
load_dotenv(BASE_DIR / ".env", override=True)

SERVIDOR_URL = os.getenv(
    "AINSA_SERVIDOR_URL",
    "http://127.0.0.1:8000"
).rstrip("/")

TOKEN = (
    os.getenv("AINSA_AGENT_TOKEN")
    or os.getenv("AGENT_TOKEN", "")
).strip()

HEADERS = {"X-Agent-Token": TOKEN}

AGENTE_SCRIPT = BASE_DIR / "agente.py"

# Prioriza el Python del entorno virtual de AINSA
if os.name == "nt":
    PYTHON_AGENTE = BASE_DIR / "env" / "Scripts" / "python.exe"
else:
    PYTHON_AGENTE = BASE_DIR / "env" / "bin" / "python"

if not PYTHON_AGENTE.exists():
    PYTHON_AGENTE = Path(sys.executable)

INTERVALO_SEGUNDOS = 60
TIMEOUT = 15

# Evita lanzar varias ejecuciones simultáneas en este monitor
ultima_ejecucion = None


def log(mensaje: str):
    """Registra el mensaje localmente y lo envía al panel."""
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ahora}] {mensaje}", flush=True)

    if not TOKEN:
        print("[Dashboard] Falta configurar el token.", flush=True)
        return

    try:
        respuesta = httpx.post(
            f"{SERVIDOR_URL}/api/agente/publicidad/log",
            json={"mensaje": mensaje},
            headers=HEADERS,
            timeout=TIMEOUT
        )
        respuesta.raise_for_status()
    except httpx.HTTPError as error:
        print(
            f"[Dashboard] No se pudo enviar el log: {error}",
            flush=True
        )


def obtener_estado():
    """Consulta la configuración actual guardada en el servidor."""
    if not TOKEN:
        raise RuntimeError("No se configuró el token del agente.")

    respuesta = httpx.get(
        f"{SERVIDOR_URL}/api/agente/publicidad/estado",
        headers=HEADERS,
        timeout=TIMEOUT
    )
    respuesta.raise_for_status()
    return respuesta.json()


def debe_ejecutarse(config: dict) -> bool:
    """Comprueba si el agente está activo y ya llegó su hora."""
    if not config.get("activo"):
        return False

    proxima = config.get("proxima_ejecucion")
    if not proxima:
        return False

    # Acepta fechas con espacio o con T entre fecha y hora
    fecha = datetime.fromisoformat(str(proxima).replace("Z", "+00:00"))

    # Evita comparar fechas con zona horaria contra fechas sin zona
    if fecha.tzinfo is not None:
        ahora = datetime.now(fecha.tzinfo)
    else:
        ahora = datetime.now()

    return ahora >= fecha


def ejecutar_publicidad():
    """Lanza el agente real que ya tienes desarrollado."""
    if not AGENTE_SCRIPT.is_file():
        log(f"ERROR: No se encontró {AGENTE_SCRIPT}")
        return False

    log("MarketingAgent iniciado.")
    log("Iniciando procesamiento de fotografías...")

    try:
        
        resultado = subprocess.run(
            [str(PYTHON_AGENTE), str(AGENTE_SCRIPT)],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=3600,
            check=False,
            env={
                **os.environ,
                "PYTHONIOENCODING": "utf-8",
                "PYTHONUTF8": "1"
            }
        )


        if resultado.stdout:
            for linea in resultado.stdout.splitlines():
                print(linea, flush=True)

        if resultado.stderr:
            for linea in resultado.stderr.splitlines():
                print(f"[Agente] {linea}", flush=True)

        if resultado.returncode == 0:
            log("Procesamiento de publicidad finalizado correctamente.")
            return True

        log(
            f"ERROR: agente.py terminó con código "
            f"{resultado.returncode}."
        )
        return False

    except subprocess.TimeoutExpired:
        log("ERROR: el agente superó el tiempo máximo de ejecución.")
        return False
    except OSError as error:
        log(f"ERROR al iniciar el agente: {error}")
        return False


def main():
    global ultima_ejecucion

    log("Monitor de AINSAC iniciado.")

    while True:
        try:
            config = obtener_estado()

            if debe_ejecutarse(config):
                proxima = str(config["proxima_ejecucion"])

                # No repetir la misma ejecución en cada consulta
                if proxima != ultima_ejecucion:
                    # Marcar antes de iniciar para evitar duplicados
                    ultima_ejecucion = proxima
                    ejecutar_publicidad()

            time.sleep(INTERVALO_SEGUNDOS)

        except KeyboardInterrupt:
            log("Monitor detenido por el usuario.")
            break
        except (httpx.HTTPError, ValueError, RuntimeError) as error:
            log(f"Error consultando la programación: {error}")
            time.sleep(INTERVALO_SEGUNDOS)
        except Exception as error:
            log(f"Error inesperado: {error}")
            time.sleep(INTERVALO_SEGUNDOS)


if __name__ == "__main__":
    main()
