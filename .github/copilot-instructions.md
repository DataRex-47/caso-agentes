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

## Estilo de respuesta: modo TDAH (siempre activo)

Aplica a TODAS las respuestas, en todos los modos y con todos los agentes.

1. Primera línea = acción concreta (comando, ruta, snippet). Nunca preámbulo.
2. Varios pasos → lista numerada; un paso = una acción acotada.
3. Cerrar con UNA acción de menos de 2 minutos.
4. Restatar el estado al inicio de cada turno ("paso 3 de 5 hecho: ...").
5. Estimaciones en unidades concretas ("15 min"), nunca "un poco de trabajo".
6. Errores: causa + arreglo. Sin "vaya" ni "parece que hay un problema".
7. Máximo 5 ítems visibles por grupo.
8. Prohibido: "Gran pregunta", "Déjame...", "¿algo más?", recaps finales, modismos.
9. Excepción: si el usuario pide "explícame", el cuerpo puede ser largo; el formato se mantiene.

### Precedencia del estilo TDAH

- Estas reglas tienen prioridad sobre cualquier instrucción de agente que pida
  "explicar al usuario", "explicar el porqué" o "resumen ejecutivo".
- Los informes completos van a **archivo** (`06_resultados/`, `.md`, notebooks).
  Al chat solo van ≤5 ítems con lo accionable.
- Los agentes A_02, A_03, A_04, A_05, A_06 y A_07 que piden explicaciones o
  resumen ejecutivo deben comprimirlo a ese formato sin perder contenido:
  lo omitido en el chat se guarda en el informe en disco.

## ESTADO ACTUAL DEL PROYECTO

**Fase completada**: A_11_API_Deployer

**Tipo de proceso configurado**: Scoring

**Modo de ejecución**: LOCAL + RENDER_ROOT_READY

**Sistema operativo detectado**: Windows

**Entorno**: UV, Python 3.12 (`.python-version`), venv en `../.venv/Scripts/python.exe`

---

### Fuente de verdad y motor de scoring

- Script de producción (fuente de verdad): `07_despliegue/02_produccion_scoring.py`
- Artefacto: `07_despliegue/artefacto_pipeline.pkl` (cloudpickle; des-ignorado en `.gitignore`; vive fuera de `api_render/` y no se duplica)
- Motor reutilizable (regenerado desde la fuente de verdad): `07_despliegue/deploy-ready/api_render/api/scoring.py`
  - Contrato: `DataFrame -> DataFrame`
  - `scoring_df(df, id_col=None)` — si `id_col` es None genera `registro_id` secuencial 0..n-1 (comportamiento por defecto del batch)
  - Incluye `prepara_datos` (armonización temprana: typo `Fomación`, snake_case sin acentos, drop de `dia_de_la_semana`)
  - Nota: `percentil` usa `pd.qcut` sobre el lote; con 1 registro o scores constantes se degrada a 1 para no romper online
- `07_despliegue/02_api/` es el despliegue API previo (solo contraste). NO es la salida canónica de A_11.

### API generada

- Raíz desplegable (patrón del profesor): `07_despliegue/deploy-ready/api_render/`
  (`__init__.py`, `api/` con `__init__.py`+`main.py`+`scoring.py`+`schemas.py`+`test_payload.json`,
  `produccion_scoring.py`, `requirements.txt`, `runtime.txt`, `README_DEPLOY.md`)
- Instancia FastAPI: `app` en `api/main.py`
- El artefacto se resuelve en `07_despliegue/artefacto_pipeline.pkl` (fuera de `api_render/`; no se copia ni se mueve)

**Contrato final (handoff para A_12 y posteriores)**
- Endpoint de inferencia: `POST /predict`
- Comando local canónico (desde `07_despliegue/deploy-ready/api_render`): `uvicorn api.main:app --reload`
- Formato de entrada: **lista JSON de registros** `[{...}]` (siempre lista, también con 1 registro)
- Formato de salida: **lista JSON de objetos** (equivalente a `records`)
- Modalidad de salida: **salida reducida operativa**
- Columnas reales de salida: `registro_id`, `score_contratacion`, `prediccion_binaria`, `categoria`
- `percentil` se calcula en el motor pero **se omite** de la API por ser relativo al lote
- Lógica de negocio: la del motor (`categoria`: `>=0.7` ALTA_PROBABILIDAD, `>=0.4` MEDIA_PROBABILIDAD, resto BAJA_PROBABILIDAD). Sin lógica adicional.
- Campos de entrada (15, alias = nombres originales del CSV): `Edad`, `Trabajo`, `Estado Civil`, `Fomación`, `Impago`, `Prestamo hipotecario`, `Prestamo Personal`, `Canal de contacto`, `Mes`, `num contactos esta campaña`, `num días último contacto`, `num contactos otras campañas`, `resultado campaña anterior`, `variación tasa empleo`, `euribor3m`
- Exclusiones: `contrata_fondos` (target), `Unnamed: 0` (el batch genera ID), `Dia de la semana` (el flujo lo elimina; si se envía, Pydantic lo ignora)
- Endpoints de diagnóstico: `GET /health`, `GET /debug`

**Ejemplo válido de respuesta**
```json
[{"registro_id": 0, "score_contratacion": 0.61, "prediccion_binaria": 1, "categoria": "MEDIA_PROBABILIDAD"}]
```

**Configuración validada de Render (Web Service)**
```text
Root Directory: 07_despliegue/deploy-ready/api_render
Build Command: pip install -r requirements.txt
Start Command: uvicorn api.main:app --host 0.0.0.0 --port $PORT
Key: PYTHON_VERSION
Value: 3.12.13
```

Material de despliegue: `07_despliegue/deploy-ready/api_render/` (paquete autocontenido).
`07_despliegue/api/` no existe: queda descartado, no usarlo ni crearlo.

**Validación local**: HECHA.
- `GET /docs` → OK
- `GET /debug` → `"status": "OK"`, motor puntuando correctamente
- `POST /predict` → OK
- Python real del entorno validado: `3.12.13`
- Versiones de `requirements.txt` verificadas contra los paquetes instalados en `.venv` (2026-09-15): `fastapi==0.141.1`, `uvicorn==0.52.4`, `pydantic==2.13.5` + cadena ML completa. Sin pendientes.

**Notas de despliegue**
- `*.csv` está en `.gitignore` → el CSV de entrada NO viaja al repo (el batch usa `INPUT_URL`).
- `07_despliegue/artefacto_pipeline.pkl` está des-ignorado → disponible en el build de Render
  y resuelto desde `api_render/api/scoring.py` (no se duplica ni se mueve).
- `requirements.txt` de la API: cadena ML tomada de `deploy-ready/render-batch/requirements.txt` (entorno real); versiones de `fastapi`/`uvicorn`/`pydantic` coinciden con los paquetes instalados en `.venv` y con `pyproject.toml`. El artefacto usa solo sklearn + category_encoders → no hacen falta `xgboost` ni `imbalanced-learn`. **`pyarrow==25.0.1` añadido** (API y batch) tras el primer deploy en Render: el artefacto deserializa series Arrow y sin él fallaba con `ModuleNotFoundError: pyarrow`.
- MCP Context7 no estaba disponible en la sesión → revalidar `PYTHON_VERSION` y precedencia en la documentación oficial de Render.

**Siguiente paso recomendado**:
1. Commit + push y alta manual del Web Service en Render con la configuración anterior.
2. Comprobar `GET /health` y `GET /debug` en la URL de Render.
3. (Cadena) Continuar con A_12 (app Streamlit) consumiendo el contrato final de salida.
