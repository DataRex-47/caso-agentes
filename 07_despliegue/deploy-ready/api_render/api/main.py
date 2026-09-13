"""
API FastAPI de scoring (A_11) - paquete autocontenido `api_render`.

Arranque local (desde 07_despliegue/deploy-ready/api_render):
    uvicorn api.main:app --reload

En Render, Root Directory = 07_despliegue/deploy-ready/api_render
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException

from .scoring import scoring_df
from .schemas import RegistroEntrada, ScoringSalida

# ── Configuración ─────────────────────────
BASE_DIR = Path(__file__).resolve().parent
TEST_PAYLOAD_PATH = BASE_DIR / "test_payload.json"

# Modalidad de salida: reducida operativa.
COLUMNAS_SALIDA = [
    "registro_id",
    "score_contratacion",
    "prediccion_binaria",
    "categoria",
]


# ── Utilidades de serialización ─────────────────────────
def _a_tipo_nativo(valor):
    if isinstance(valor, np.integer):
        return int(valor)
    if isinstance(valor, np.floating):
        return float(valor)
    if isinstance(valor, np.bool_):
        return bool(valor)
    return valor


def _df_a_registros(df):
    registros = df.to_dict(orient="records")
    limpios = []
    for registro in registros:
        fila = {}
        for clave, valor in registro.items():
            fila[clave] = _a_tipo_nativo(valor)
        limpios.append(fila)
    return limpios


# ── Aplicación FastAPI ─────────────────────────
app = FastAPI(
    title="API Scoring - Caso Agentes",
    description="API de predicción de contratación de fondos (scoring online).",
    version="1.0.0",
)


# ── Endpoints ─────────────────────────
@app.get("/health")
def health():
    """Comprueba que la API está levantada."""
    return {"status": "ok"}


@app.post("/predict", response_model=list[ScoringSalida])
def predict(registros: list[RegistroEntrada]):
    """Endpoint principal de inferencia. Cuerpo: lista JSON `[{...}]`."""
    if not registros:
        raise HTTPException(status_code=400, detail="La lista de registros está vacía.")

    registros_dict = []
    for registro in registros:
        registros_dict.append(registro.model_dump(by_alias=True))

    df_input = pd.DataFrame(registros_dict)

    df_resultado = scoring_df(df_input)
    df_salida = df_resultado[COLUMNAS_SALIDA].copy()

    return _df_a_registros(df_salida)


@app.get("/debug")
def debug():
    """Diagnóstico rápido del motor con `test_payload.json`."""
    resultado = {
        "python_version": sys.version,
        "status": "ERROR",
        "input_columns_detected": [],
        "output_columns_detected": [],
        "sample_output": [],
        "engine_error": None,
    }

    try:
        payload_texto = TEST_PAYLOAD_PATH.read_text(encoding="utf-8")
        payload = pd.DataFrame(json.loads(payload_texto))
    except Exception as error:
        resultado["engine_error"] = f"{type(error).__name__}: {error}"
        return resultado

    resultado["input_columns_detected"] = list(payload.columns)

    try:
        df_resultado = scoring_df(payload)
    except Exception as error:
        resultado["engine_error"] = f"{type(error).__name__}: {error}"
        return resultado

    resultado["output_columns_detected"] = list(df_resultado.columns)
    df_salida = df_resultado[COLUMNAS_SALIDA].copy()
    resultado["sample_output"] = _df_a_registros(df_salida.head(1))
    resultado["status"] = "OK"

    return resultado
