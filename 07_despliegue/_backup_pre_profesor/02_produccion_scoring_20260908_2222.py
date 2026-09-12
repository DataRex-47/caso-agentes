# ── Imports ─────────────────────────────────────────────────────────
import argparse
from pathlib import Path
import pandas as pd
import cloudpickle

# ── Constantes ──────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARTEFACTO_PATH = PROJECT_ROOT / "07_despliegue" / "artefacto_pipeline.pkl"
TARGET = "contrata_fondos"

# ── Función de filas (idéntica a 01_reentrenamiento.py) ─────────────
def prepara_datos(df):
    # Eliminación de duplicados completos y conservación del índice (id).
    return df.drop_duplicates(keep='first')

# ── Argumentos de línea de comandos ─────────────────────────────────
parser = argparse.ArgumentParser(description='Scoring en producción con el pipeline guardado.')
parser.add_argument('--input', required=True, help='Ruta al CSV de datos nuevos.')
parser.add_argument('--output', required=True, help='Ruta al CSV de salida con scores.')
parser.add_argument('--sep', default=',', help="Separador del CSV de entrada (default ',').")
args = parser.parse_args()

# ── Carga de datos nuevos ───────────────────────────────────────────
df = pd.read_csv(args.input, index_col=0, encoding='utf-8', sep=args.sep)
df = prepara_datos(df)
if TARGET in df.columns:
    df = df.drop(columns=[TARGET])
print(f'✅ Datos de entrada: {df.shape[0]} filas x {df.shape[1]} columnas')

# ── Carga del pipeline serializado ──────────────────────────────────
with open(ARTEFACTO_PATH, 'rb') as f:
    pipe = cloudpickle.load(f)

# ── Scoring (sin reentrenamiento) ───────────────────────────────────
proba = pipe.predict_proba(df)[:, 1]

# ── Guardado del resultado ──────────────────────────────────────────
salida = pd.DataFrame({'id_cliente': df.index, 'score': proba})
salida.to_csv(args.output, index=False, encoding='utf-8')
print(f'✅ Scoring completado: {len(salida)} registros -> {args.output}')
