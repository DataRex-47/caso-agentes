- Responde siempre en español.
- Comienza cada mensaje con el emoji 🤖
- Genera el código para el script o notebook abierto, nunca para la ventana interactiva, salvo que se indique lo contrario.
- La ventana interactiva solo se usa para verificar resultados o mensajes de error.
- No expliques el código salvo que se pida.

## Convenciones de este proyecto
- Entorno gestionado con **UV**. Para añadir una dependencia: `uv add <paquete>`. Nunca `pip install`.
- Para ejecutar cualquier script: `uv run python 04_scripts/<archivo>.py`
- **Bucles tradicionales** (`for` + `append`) en lugar de comprehensions y lambdas.
- Comentarios de sección con el formato `# ── Título ─────────`
- Rutas siempre con `pathlib`, nunca concatenando strings.
- Los datos crudos de `02_datos/01_Originales/` son de **solo lectura**: nunca se sobrescriben.

## ESTADO ACTUAL DEL PROYECTO

**Fase completada**: A_10_BatchDeploy

**Tipo de proceso configurado**: Scoring

**Modo de ejecución**: AMBOS (LOCAL + RENDER)

**Sistema operativo detectado**: Windows

**Script batch principal**:
`07_despliegue/02_produccion_scoring.py`

**Origen de datos**:
- Tipo: CSV local
- Detalle: `02_datos/01_Originales/contratacion_fondos.csv` (LOCAL). En RENDER: descarga vía `INPUT_URL` (fallback: CSV del repo si existiera).

**Destino de resultados**:
- Tipo: Carpeta local (archivo fijo)
- Detalle: `07_despliegue/batch/resultados.csv` (LOCAL). En RENDER: POST a `OUTPUT_WEBHOOK_URL` (disco efímero).

**Programación configurada**:
- Frecuencia: DAILY
- Hora: 21:20 (local)
- CronSchedule (si aplica): `20 21 * * *` (UTC en Render; 21:20 local ≈ `20 19 * * *` en verano)

**Artefactos generados**:
- `07_despliegue/batch/` (config_batch.json, run_manual.bat, create_schedule.bat, remove_schedule.bat, activate_schedule.bat)
- `07_despliegue/deploy-ready/render-batch/` (start.sh, render.yaml, requirements.txt, README_RENDER_CRON.md)

**Notas Render**:
- Cron Jobs requieren plan de pago (no disponibles en free); MCP Context7 no estaba disponible en la sesión → revalidar en la documentación oficial.
- `cronSchedule` se interpreta en UTC y no aplica horario de verano.
- `*.csv` está en `.gitignore` → el CSV de entrada NO viaja al repo; usar `INPUT_URL`.
- `07_despliegue/artefacto_pipeline.pkl` está des-ignorado explícitamente → disponible en el build de Render.

**Siguiente paso recomendado**:
- Probar ejecución manual (`07_despliegue/batch/run_manual.bat`)
- Activar scheduler (`activate_schedule.bat`) si procede
- En Render: crear el Cron Job en el dashboard usando `render.yaml` / `start.sh` y el cronSchedule
- (Cadena) Continuar con agentes posteriores para API (A_11) y app Streamlit (A_12)
