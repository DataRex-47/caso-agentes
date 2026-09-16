"""
Motor de scoring para campañas de fondos.

Versión autocontenida para el paquete de despliegue `api_render`.
Adaptación directa de `02_produccion_scoring.py` para uso en memoria.

Resolución del artefacto: primero en `artefactos/` del propio paquete
(si existe); si no, en `07_despliegue/artefacto_pipeline.pkl` del repo.
"""

import unicodedata
from pathlib import Path

import cloudpickle
import numpy as np
import pandas as pd

# ── Configuración ─────────────────────────
BASE_DIR = Path(__file__).resolve().parent  # deploy-ready/api_render/api
DEPLOY_DIR = BASE_DIR.parent  # deploy-ready/api_render
PROJECT_ROOT = DEPLOY_DIR.parent.parent.parent  # raíz del proyecto

# Se usa el artefacto local del paquete si existe; si no, el del repo.
# Así NO es obligatorio duplicar el .pkl dentro de artefactos/.
ARTEFACTO_LOCAL = DEPLOY_DIR / "artefactos" / "artefacto_pipeline.pkl"
ARTEFACTO_REPO = PROJECT_ROOT / "07_despliegue" / "artefacto_pipeline.pkl"

if ARTEFACTO_LOCAL.exists():
    ARTEFACTO_PATH = ARTEFACTO_LOCAL
else:
    ARTEFACTO_PATH = ARTEFACTO_REPO


# ── Preparación de filas ─────────────────────────
def prepara_datos(df):
    if "Fomación" in df.columns:
        df = df.rename(columns={"Fomación": "Formación"})

    def limpiar_nombre(col):
        col = "".join(
            c
            for c in unicodedata.normalize("NFD", col)
            if unicodedata.category(c) != "Mn"
        )
        col = col.lower().replace(" ", "_").replace("-", "_")
        col = (
            col.replace("á", "a")
            .replace("é", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ú", "u")
            .replace("ñ", "n")
        )
        while "__" in col:
            col = col.replace("__", "_")
        return col.strip("_")

    df.columns = [limpiar_nombre(c) for c in df.columns]

    if "dia_de_la_semana" in df.columns:
        df = df.drop(columns=["dia_de_la_semana"])

    return df


# ── Categorización de negocio ─────────────────────────
def categorizar_score(score):
    if score >= 0.7:
        return "ALTA_PROBABILIDAD"
    elif score >= 0.4:
        return "MEDIA_PROBABILIDAD"
    else:
        return "BAJA_PROBABILIDAD"


# ── Carga del artefacto ─────────────────────────
if not ARTEFACTO_PATH.exists():
    raise FileNotFoundError(
        f"No se encontró el artefacto en {ARTEFACTO_PATH}. "
        "Ejecuta primero 01_reentrenamiento.py o copia el .pkl a artefactos/."
    )

with open(ARTEFACTO_PATH, "rb") as f:
    artefacto = cloudpickle.load(f)

pipe = artefacto["pipeline"]
te = artefacto["target_encoder"]
columnas_te = artefacto["columnas_te"]


# ── Motor de scoring en memoria ─────────────────────────
def scoring_df(df: pd.DataFrame, id_col: str | None = None) -> pd.DataFrame:
    """
    Contrato: DataFrame -> DataFrame.

    Devuelve: registro_id, score_contratacion, prediccion_binaria, percentil,
    categoria.
    """
    # ── Guardar columna ID ─────────────────────────
    if id_col and id_col in df.columns:
        df_ids = df[[id_col]].copy()
        df_ids.columns = ["registro_id"]
    else:
        df_ids = pd.DataFrame({"registro_id": range(len(df))})

    # ── Preparación de datos ─────────────────────────
    df = prepara_datos(df)

    # ── TargetEncoder (solo transform) ─────────────────────────
    X_te = te.transform(df[columnas_te])
    X_te.columns = [f"{c}__te" for c in columnas_te]

    X = pd.concat([df, X_te], axis=1)

    # ── Scoring ─────────────────────────
    proba = pipe.predict_proba(X)[:, 1]
    pred_class = pipe.predict(X)

    # ── Construcción del output ─────────────────────────
    df_output = df_ids.copy()
    df_output["score_contratacion"] = proba
    df_output["prediccion_binaria"] = pred_class

    # `percentil` es relativo al lote: con 1 registro o scores constantes
    # `pd.qcut` fallaría, así que se degrada a 1.
    if len(proba) > 1 and len(np.unique(proba)) > 1:
        df_output["percentil"] = (
            pd.qcut(proba, q=10, labels=False, duplicates="drop") + 1
        )
    else:
        df_output["percentil"] = 1

    df_output["categoria"] = df_output["score_contratacion"].apply(categorizar_score)

    return df_output
