
# servidor_client.py
import httpx
from datetime import datetime

from config import SERVIDOR_URL, AGENT_TOKEN, HTTP_TIMEOUT

HEADERS = {
    "X-Agent-Token": AGENT_TOKEN
}


def log(mensaje: str) -> None:
    """Muestra el mensaje localmente e intenta enviarlo al dashboard."""
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{fecha}] {mensaje}", flush=True)

    if not AGENT_TOKEN:
        print(
            "[Dashboard] No se configuró AINSA_AGENT_TOKEN.",
            flush=True
        )
        return

    try:
        response = httpx.post(
            f"{SERVIDOR_URL}/api/agente/publicidad/log",
            json={
                "mensaje": mensaje,
                "fecha": fecha
            },
            headers=HEADERS,
            timeout=HTTP_TIMEOUT
        )
        response.raise_for_status()

    except httpx.HTTPError as error:
        print(
            f"[Dashboard] No se pudo enviar el log: {error}",
            flush=True
        )


def obtener_estado() -> dict | None:
    """Consulta el estado del agente en el servidor."""
    if not AGENT_TOKEN:
        log("No se configuró el token del agente.")
        return None

    try:
        response = httpx.get(
            f"{SERVIDOR_URL}/api/agente/publicidad/estado",
            headers=HEADERS,
            timeout=HTTP_TIMEOUT
        )
        response.raise_for_status()

        datos = response.json()
        if not isinstance(datos, dict):
            raise ValueError("El servidor no devolvió un objeto JSON.")

        return datos

    except (httpx.HTTPError, ValueError) as error:
        print(
            f"[Dashboard] Error consultando estado: {error}",
            flush=True
        )
        return None


def debe_ejecutarse() -> bool:
    """
    Compatibilidad con el diseño antiguo.
    En la nueva arquitectura, el servidor programa la ejecución.
    """
    estado = obtener_estado()

    if not estado or not estado.get("activo", False):
        return False

    proxima = estado.get("proxima_ejecucion")
    if not proxima:
        return False

    try:
        fecha_programada = datetime.fromisoformat(
            proxima.replace("Z", "+00:00").replace(" ", "T")
        )

        ahora = datetime.now(
            fecha_programada.tzinfo
        ) if fecha_programada.tzinfo else datetime.now()

        return ahora >= fecha_programada

    except (TypeError, ValueError) as error:
        log(f"Fecha de programación inválida: {error}")
        return False


def notificar_completado(archivo: str) -> None:
    """Informa al dashboard que se generó una publicación."""
    log(f"PUBLICIDAD_GENERADA: {archivo}")
