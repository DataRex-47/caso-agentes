# App Streamlit — Scoring de contratación de fondos (A_12)

Interfaz de usuario que consume la API de inferencia de A_11.
No contiene lógica de Machine Learning: envía el formulario a `POST /predict`
con formato `[{...}]` y representa la salida reducida real de la API
(`registro_id`, `score_contratacion`, `prediccion_binaria`, `categoria`).

## Estructura

```txt
07_despliegue/app/
├── app.py                 # UI + cliente HTTP (warmup y scoring)
├── .streamlit/
│   └── config.toml        # tema oscuro
├── idea/
│   └── design_spec.json   # especificación de diseño normalizada
├── assets/                # logo, favicon e imágenes (opcional)
├── requirements.txt       # dependencias exactas para despliegue
└── README.md
```

## Requisito previo: la API debe estar activa

La app no ofrece inferencia si la API no está funcionando. Arranca o
despliega primero la API y verifica que responde.

## Ejecución local (2 terminales, entorno UV del proyecto)

### Terminal 1 — API de scoring

```bash
cd 07_despliegue/deploy-ready/api_render
uv run uvicorn api.main:app --reload
```

Verifica que responde en `http://127.0.0.1:8000/docs`.

### Terminal 2 — App Streamlit (sin cerrar la terminal 1)

```bash
cd 07_despliegue/app
uv run streamlit run app.py
```

Se abre en `http://localhost:8501`. Si falta alguna dependencia del entorno
(no debería: `streamlit` y `requests` ya están en el proyecto):
`uv add streamlit requests`.

Alternativa fuera de UV: `pip install -r requirements.txt` y
`streamlit run app.py`.

## Despliegue en Render (modo guía, tras validar en local)

1. La API debe estar previamente desplegada y accesible
   (config de A_11 en `07_despliegue/deploy-ready/api_render`).
2. En `app.py`, sustituye `API_BASE_URL` por la URL pública real de la API,
   por ejemplo `https://caso-agentes-1-yhkk.onrender.com`.
   Cualquier valor local (`http://127.0.0.1:8000`) deja de ser válido en Render.
3. Crea un **Web Service** en Render con:

```text
Root Directory: 07_despliegue/app
Build Command: pip install -r requirements.txt
Start Command: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

4. En `Environment`, añade la variable manual:

```text
Key: PYTHON_VERSION
Value: 3.12.13
```

## Nota sobre cold start (plan free)

La API en Render free se suspende tras inactividad: la primera llamada puede
tardar ~50 s. La app gestiona el despertado automáticamente (warmup a
`/health` + reintentos) y muestra un aviso en la interfaz.

## Niveles de salida de la API

- `categoria`: `ALTA_PROBABILIDAD` (score ≥ 0.7), `MEDIA_PROBABILIDAD` (≥ 0.4),
  `BAJA_PROBABILIDAD` (resto). Lógica de negocio de A_11, sin redefinir en la app.

Si el deploy falla, pega el error real de build o runtime al agente A_12 para
corregirlo.
