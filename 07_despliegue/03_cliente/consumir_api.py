"""
Cliente de pruebas de la API de scoring.

NO importa nada del proyecto: habla con la API por HTTP, igual que lo haría
un CRM, una app móvil o cualquier otro sistema externo. Esa es justo la
gracia — si importase `scoring.py` no estaría probando la API, se la estaría
saltando.

USO — hacen falta DOS terminales:

    TERMINAL 1 (desde 07_despliegue/) — se queda ocupada sirviendo:
       uv run uvicorn api:api --reload --app-dir 02_api

    TERMINAL 2 (desde 07_despliegue/03_cliente/):
       uv run python consumir_api.py

Requiere:
    uv add requests
"""

# ── Imports ─────────────────────────────────────────────────────────
import json
from pathlib import Path

import requests

# ── Constantes ──────────────────────────────────────────────────────
# Lo único que habría que cambiar para apuntar a un servidor real.
URL_BASE = "http://127.0.0.1:8000"
TIMEOUT = 10

# Umbral de decisión. Vive en el CLIENTE, no en la API: la API devuelve
# una probabilidad, quien consume decide dónde está el corte.
UMBRAL = 0.5

# El caso de prueba va en un JSON aparte para poder cambiarlo sin tocar
# código. Se resuelve desde la ubicación de este fichero, así funciona
# se lance desde donde se lance.
PAYLOAD_PATH = Path(__file__).resolve().parent / "payload.json"


# ── Carga del caso de prueba ────────────────────────────────────────
def cargar_payload(ruta=PAYLOAD_PATH):
    """Lee el JSON de prueba. Debe respetar el esquema de /predict."""
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Comprobación de salud ───────────────────────────────────────────
def comprobar_salud():
    """Primero esto: no toca el modelo, solo confirma que el servidor vive."""
    respuesta = requests.get(f"{URL_BASE}/health", timeout=TIMEOUT)
    respuesta.raise_for_status()
    return respuesta.json()


# ── Llamada de scoring ──────────────────────────────────────────────
def puntuar(registro):
    """
    Manda un registro a /predict y devuelve el JSON de respuesta.

    Un 422 significa que Pydantic rechazó el JSON: no es un fallo del
    servidor, es la validación haciendo su trabajo. Merece un mensaje
    distinto porque el cuerpo dice exactamente qué campo falló.
    """
    respuesta = requests.post(
        f"{URL_BASE}/predict", json=registro, timeout=TIMEOUT
    )

    if respuesta.status_code == 422:
        raise ValueError(f"Datos inválidos: {respuesta.json()}")

    respuesta.raise_for_status()
    return respuesta.json()


# ── Regla de negocio ────────────────────────────────────────────────
def decidir(score, umbral=UMBRAL):
    """El criterio de negocio es del cliente, no del modelo."""
    if score >= umbral:
        return "CONTACTAR"
    return "DESCARTAR"


# ── Varios registros de una tanda ───────────────────────────────────
def puntuar_lote(registros):
    """
    Una llamada por registro. Sirve para probar varias simulaciones
    seguidas; para volúmenes grandes, el camino es el batch, no la API.
    """
    resultados = []
    for registro in registros:
        resultados.append(puntuar(registro))
    return resultados


# ── Ejecución ───────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Salud:", comprobar_salud())

    payload = cargar_payload()
    resultado = puntuar(payload)
    score = resultado["score_contratacion"]

    print(f"Registro  : {resultado['registro_id']}")
    print(f"Score     : {score:.4f}")
    print(f"Decisión  : {decidir(score)}")
