"""
Motor de scoring para campañas de fondos.

Derivado del script de producción batch, eliminando:
- gestión de argumentos
- lectura/escritura de ficheros
- lógica de reporting

Carga el artefacto entrenado y permite ejecutar
inferencia sobre datos en memoria mediante la
función `scoring_df`.

No realiza reentrenamiento.
"""

import pandas as pd
import unicodedata
from pathlib import Path
import cloudpickle

# Configuración
# OJO: este fichero vive en 07_despliegue/02_api/, un nivel MÁS ABAJO que
# 01_reentrenamiento.py y 02_produccion_scoring.py. Por eso necesita TRES
# .parent para llegar a la raíz del proyecto, no dos.
try:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
except NameError:
    # En modo interactivo __file__ no existe
    PROJECT_ROOT = Path.cwd()

ARTEFACTO_PATH = PROJECT_ROOT / "07_despliegue" / "artefacto_pipeline.pkl"


# Función de preparación de filas (misma que en reentrenamiento)
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


# Carga del artefacto


if not ARTEFACTO_PATH.exists():
    raise FileNotFoundError(
        f"No se encontró el artefacto en {ARTEFACTO_PATH}. "
        "Ejecuta primero 01_reentrenamiento.py"
    )

with open(ARTEFACTO_PATH, "rb") as f:
    artefacto = cloudpickle.load(f)

pipe = artefacto["pipeline"]
te = artefacto["target_encoder"]
columnas_te = artefacto["columnas_te"]


# Función preparación de datos


def scoring_df(df: pd.DataFrame) -> pd.DataFrame:

    df_out = pd.DataFrame(index=df.index)

    df_out["registro_id"] = df["Unnamed: 0"].astype(int)
    df = df.drop(columns=["Unnamed: 0"])

    df = prepara_datos(df)

    X_te = te.transform(df[columnas_te])
    X_te.columns = [f"{c}__te" for c in columnas_te]

    X = pd.concat([df, X_te], axis=1)

    df_out["score_contratacion"] = pipe.predict_proba(X)[:, 1].astype(float)

    return df_out
