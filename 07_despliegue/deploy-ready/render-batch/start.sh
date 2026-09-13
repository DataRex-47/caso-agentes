#!/usr/bin/env bash
# ── A_10_BatchDeploy · Render Cron Job ─────────
# Ejecuta el scoring batch en Render:
#   1) obtiene el CSV de entrada (INPUT_URL o CSV del repo como respaldo)
#   2) ejecuta 07_despliegue/02_produccion_scoring.py
#   3) entrega los resultados (OUTPUT_WEBHOOK_URL) o los deja en el contenedor
# Todos los logs van a stdout/stderr (Render los captura).

set -euo pipefail

# ── Raíz del repositorio (directorio de trabajo) ─────────
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$REPO_ROOT"

# ── Configuración ─────────
SCRIPT="07_despliegue/02_produccion_scoring.py"
ARTIFACT="07_despliegue/artefacto_pipeline.pkl"
LOCAL_INPUT="02_datos/01_Originales/contratacion_fondos.csv"

WORK_DIR="${TMPDIR:-/tmp}/caso_agentes_scoring"
INPUT_FILE="$WORK_DIR/input.csv"
OUTPUT_FILE="$WORK_DIR/resultados.csv"
HTTP_TIMEOUT="${HTTP_TIMEOUT:-60}"

mkdir -p "$WORK_DIR"
export INPUT_FILE OUTPUT_FILE HTTP_TIMEOUT

# ── Intérprete de Python ─────────
PYTHON_BIN="${PYTHON_BIN:-python}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    PYTHON_BIN="python3"
fi
echo "[INFO] Intérprete: $($PYTHON_BIN --version 2>&1)"
echo "[INFO] Repo root:  $REPO_ROOT"

# ── Validaciones ─────────
if [ ! -f "$SCRIPT" ]; then
    echo "[ERROR] No existe el script: $SCRIPT" >&2
    exit 1
fi
if [ ! -f "$ARTIFACT" ]; then
    echo "[ERROR] No existe el artefacto del pipeline: $ARTIFACT" >&2
    echo "        Asegúrate de que '07_despliegue/artefacto_pipeline.pkl' está en el repo (no ignorado por git)." >&2
    exit 1
fi

# ── 1) Origen de datos ─────────
if [ -n "${INPUT_URL:-}" ]; then
    echo "[INFO] Descargando CSV de entrada desde INPUT_URL..."
    "$PYTHON_BIN" - <<'PY'
import os
import requests

url = os.environ["INPUT_URL"]
dest = os.environ["INPUT_FILE"]
timeout = int(os.environ.get("HTTP_TIMEOUT", "60"))

resp = requests.get(url, timeout=timeout)
resp.raise_for_status()
with open(dest, "wb") as f:
    f.write(resp.content)
print(f"[OK] Input descargado en {dest} ({len(resp.content)} bytes)")
PY
elif [ -f "$LOCAL_INPUT" ]; then
    echo "[WARN] INPUT_URL no definido: usando CSV del repositorio ($LOCAL_INPUT)."
    cp "$LOCAL_INPUT" "$INPUT_FILE"
else
    echo "[ERROR] INPUT_URL no definido y no existe el CSV local '$LOCAL_INPUT'." >&2
    echo "        En Render no hay disco local persistente: configura INPUT_URL." >&2
    exit 1
fi

# ── 2) Proceso batch ─────────
echo "[INFO] Ejecutando scoring..."
"$PYTHON_BIN" "$SCRIPT" --input "$INPUT_FILE" --output "$OUTPUT_FILE"

if [ ! -f "$OUTPUT_FILE" ]; then
    echo "[ERROR] El proceso no generó el archivo de salida: $OUTPUT_FILE" >&2
    exit 1
fi
echo "[OK] Resultados generados: $OUTPUT_FILE"

# ── 3) Destino de resultados ─────────
if [ -n "${OUTPUT_WEBHOOK_URL:-}" ]; then
    echo "[INFO] Enviando resultados al webhook..."
    "$PYTHON_BIN" - <<'PY'
import os
import requests

url = os.environ["OUTPUT_WEBHOOK_URL"]
path = os.environ["OUTPUT_FILE"]
timeout = int(os.environ.get("HTTP_TIMEOUT", "60"))

with open(path, "rb") as f:
    files = {"file": (os.path.basename(path), f, "text/csv")}
    resp = requests.post(url, files=files, timeout=timeout)

resp.raise_for_status()
print(f"[OK] Resultados enviados al webhook (HTTP {resp.status_code})")
PY
else
    echo "[WARN] OUTPUT_WEBHOOK_URL no definido: el resultado queda solo en el contenedor (efímero)."
    echo "       Se muestran las primeras líneas del CSV:"
    head -n 5 "$OUTPUT_FILE"
fi

echo "[OK] Proceso batch finalizado correctamente."
