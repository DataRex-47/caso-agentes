import pandas as pd
import requests

BASE_URL = "https://rtvc-medios.com/"
PARAMS = {
    "PCO_WSOn": "1",
    "PCO_WSKey": "WHRNHA3PTS",
    "PCO_WSSecret": "Z5ZLT6PG3U",
    "PCO_WSId": "RTVC_Activos",
}

# Fingimos ser un navegador real para que el firewall no lo bloquee
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}


def consultar_activos():
    try:
        response = requests.get(
            BASE_URL, params=PARAMS, headers=HEADERS, timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        print(f"Error HTTP: {err}")
        print("Cuerpo de respuesta del servidor:")
        print(response.text[:500])  # Muestra los primeros 500 caracteres


if __name__ == "__main__":
    datos = consultar_activos()
    if datos:
        print("¡Conexión exitosa!")
        print(datos)
    else:
        print("No se pudo establecer conexión con el servidor.")