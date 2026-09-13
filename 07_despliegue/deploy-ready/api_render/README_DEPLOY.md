# Deploy API en Render · paquete `api_render`

Paquete autocontenido para desplegar la API de scoring. No necesita nada de
fuera de esta carpeta (salvo el artefacto, que va en `artefactos/`).

---

## Configuración en Render (Web Service)

```text
Root Directory:  07_despliegue/deploy-ready/api_render
Build Command:   pip install -r requirements.txt
Start Command:   uvicorn api.main:app --host 0.0.0.0 --port $PORT
Key:             PYTHON_VERSION
Value:           3.12.13
```

> Si Render rechaza `3.12.13`, poner `3.12`.

---

## Artefacto

**No hace falta copiarlo.** El motor lo busca primero en `artefactos/` y, si no
está, lo coge del repo: `07_despliegue/artefacto_pipeline.pkl`.

Si quieres tenerlo dentro (como referencia), este comando lo copia:

```powershell
New-Item -ItemType Directory -Force "07_despliegue\deploy-ready\api_render\artefactos"
Copy-Item "07_despliegue\artefacto_pipeline.pkl" "07_despliegue\deploy-ready\api_render\artefactos\artefacto_pipeline.pkl"
```

---

## Probar en local

```powershell
cd "07_despliegue\deploy-ready\api_render"
uv run uvicorn api.main:app --reload
```

Luego abrir `http://127.0.0.1:8000/docs`.

---

## Estructura

```text
api_render/
├── api/
│   ├── __init__.py
│   ├── main.py               FastAPI (`app`)
│   ├── scoring.py            motor de scoring
│   ├── schemas.py            contrato entrada/salida
│   └── test_payload.json
├── artefactos/
│   └── artefacto_pipeline.pkl
├── __init__.py
├── produccion_scoring.py     copia de referencia (fuente de verdad en 07_despliegue/)
├── requirements.txt
├── runtime.txt
└── README_DEPLOY.md
```

---

## Comprobar tras el deploy

- `GET /health` → `{"status": "ok"}`
- `GET /debug` → `"status": "OK"`
- `POST /predict` → lista JSON

Ejemplo:

```json
[{"registro_id": 0, "score_contratacion": 0.6967, "prediccion_binaria": 1, "categoria": "MEDIA_PROBABILIDAD"}]
```

Si el build falla, copiar el log de Render y devolvérselo al agente.
