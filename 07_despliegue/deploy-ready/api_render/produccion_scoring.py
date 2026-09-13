"""
Script de producción para scoring de nuevos registros.
Carga el artefacto entrenado y genera predicciones sin reentrenar.

USO:
    - Desde terminal: python 02_produccion_scoring.py --input datos.csv --output resultados.csv
    - Desde ventana interactiva: ejecutar directamente, usa rutas por defecto

NOTA: copia de referencia dentro del paquete de despliegue api_render.
La fuente de verdad es 07_despliegue/02_produccion_scoring.py
"""

import sys
import argparse
import pandas as pd
import unicodedata
from pathlib import Path
import cloudpickle

# Configuración
try:
    PROJECT_ROOT = Path(__file__).parent.parent
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


def get_args():
    parser = argparse.ArgumentParser(
        description="Script de scoring para campañas de fondos"
    )
    parser.add_argument(
        "--input", type=str, required=True, help="Ruta al CSV de entrada"
    )
    parser.add_argument(
        "--output", type=str, required=True, help="Ruta al CSV de salida"
    )
    parser.add_argument(
        "--id-column", type=str, default=None, help="Columna identificadora"
    )

    # Si se ejecuta en entorno interactivo, usar valores por defecto
    if hasattr(sys, "ps1") or len(sys.argv) == 1:
        print(
            "⚠️ Ejecutando en modo interactivo: usando rutas por defecto para input/output."
        )

        class Args:
            pass

        args = Args()
        args.input = str(
            PROJECT_ROOT / "02_datos" / "01_Originales" / "contratacion_fondos.csv"
        )
        args.output = str(PROJECT_ROOT / "07_despliegue" / "scoring_resultados.csv")
        args.id_column = None
        return args
    else:
        return parser.parse_args()


if __name__ == "__main__":
    args = get_args()

    # Carga del artefacto
    print(f"Cargando artefacto desde: {ARTEFACTO_PATH}")

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
    metadata = artefacto.get("metadata", {})

    print(
        f"✅ Artefacto cargado: {metadata.get('metric', 'N/A')} = {metadata.get('best_score', 'N/A')}"
    )

    # Carga de datos
    print(f"\nCargando datos desde: {args.input}")
    input_path = Path(args.input)

    if not input_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {args.input}")

    df = pd.read_csv(input_path, sep=",", encoding="utf-8")
    print(f"Shape original: {df.shape}")

    # Guardar columna ID
    id_col = args.id_column
    if id_col and id_col in df.columns:
        df_ids = df[[id_col]].copy()
        print(f"Columna ID: {id_col}")
    else:
        df_ids = pd.DataFrame({"registro_id": range(len(df))})
        print("ID generado secuencialmente")

    # Preparación de datos
    print("\nAplicando preparación...")
    df = prepara_datos(df)

    # TargetEncoder (solo transform)
    print("Aplicando TargetEncoder...")
    X_te = te.transform(df[columnas_te])
    X_te.columns = [f"{c}__te" for c in columnas_te]

    X = pd.concat([df, X_te], axis=1)
    print(f"X shape final: {X.shape}")

    # Scoring
    print("\nGenerando predicciones...")
    proba = pipe.predict_proba(X)[:, 1]
    pred_class = pipe.predict(X)

    print(f"✅ Predicciones: {len(proba)} registros")
    print(
        f"   Prob media: {proba.mean():.4f}, min: {proba.min():.4f}, max: {proba.max():.4f}"
    )

    # Construcción del output
    df_output = df_ids.copy()
    df_output["score_contratacion"] = proba
    df_output["prediccion_binaria"] = pred_class
    df_output["percentil"] = pd.qcut(proba, q=10, labels=False, duplicates="drop") + 1

    def categorizar_score(score):
        if score >= 0.7:
            return "ALTA_PROBABILIDAD"
        elif score >= 0.4:
            return "MEDIA_PROBABILIDAD"
        else:
            return "BAJA_PROBABILIDAD"

    df_output["categoria"] = df_output["score_contratacion"].apply(categorizar_score)

    # Guardar resultados
    output_path = Path(args.output)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"[WARN] No se pudo crear la carpeta de salida: {e}")
    df_output.to_csv(output_path, sep=",", encoding="utf-8", index=False)

    print(f"\n✅ Resultados en: {output_path}")
    print(f"Columnas: {list(df_output.columns)}")
    print(f"\nDistribución por categoría:")
    print(df_output["categoria"].value_counts(normalize=True).to_dict())
    print("\n✅ Scoring completado")
