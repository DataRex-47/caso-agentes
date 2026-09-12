import json
import requests
from pathlib import Path


def llamar_api_scoring(
    payload, url="http://127.0.0.1:8000/predict"
):  # URL del endpoint de predicción

    response = requests.post(url, json=payload)  # Enviamos el payload como JSON
    response.raise_for_status()  # Si la respuesta no es 200, lanzará una excepción
    return response.json()


if __name__ == "__main__":

    BASE_DIR = Path(__file__).parent  # Carpeta actual del script (cliente_scoring.py)

    # 1) cargar el payload
    payload_path = BASE_DIR / "payload_ejemplo.json"
    with open(payload_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    # 2) Llamar a la API
    resultado = llamar_api_scoring(payload)

    # 3) Mostrar respuesta
    print("Respuesta de la API:")
    print(resultado)
