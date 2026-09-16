"""
A_12 — App Streamlit de scoring de contratación de fondos.

Capa de interfaz (UI) y cliente HTTP para la API de inferencia de A_11.
No contiene lógica de Machine Learning: consume el endpoint `POST /predict`,
envía `[{...}]` y representa la salida reducida real de la API
(`registro_id`, `score_contratacion`, `prediccion_binaria`, `categoria`).

Contrato heredado de A_11 (verificado en
`07_despliegue/deploy-ready/api_render/api/schemas.py`).

Ejecución local (desde `07_despliegue/app`):
    uv run streamlit run app.py

La API debe estar arrancada antes (ver README.md).
"""

# ── Configuración ─────────────────────────
# Bloque único de configuración operativa: única fuente de verdad para
# URLs, endpoints, timeouts y reintentos.
# Despliegue actual: apunta a la API desplegada en Render.
# Para probar en local contra la API local, cambiar a "http://127.0.0.1:8000".
API_BASE_URL = "https://caso-agentes-1-yhkk.onrender.com"
SCORE_ENDPOINT = "/predict"
WARMUP_ENDPOINT = "/health"

DEFAULT_TIMEOUT = 60     # segundos del POST de scoring (cold start ~50 s en Render free)
WARMUP_TIMEOUT = 10      # segundos por intento de warmup (< DEFAULT_TIMEOUT)
WARMUP_MAX_WAIT = 120    # segundos máximo del bucle de warmup (solo API remota)
WARMUP_RETRIES = 0       # ciclos extra de warmup remoto (0-1 recomendado)
SCORING_RETRIES = 1      # reintentos del POST ante timeout/conexión (0-1 recomendado)
ENABLE_WARMUP = True     # despertar el servicio antes del POST
DEBUG_MODE = False       # True = mostrar detalles técnicos de diagnóstico

# La API local no tiene cold start: si no responde al primer intento,
# no está arrancada y se avisa de inmediato (sin esperas largas).
API_ES_LOCAL = ("127.0.0.1" in API_BASE_URL) or ("localhost" in API_BASE_URL)

# ── Imports ─────────────────────────
import time
from pathlib import Path

import requests
import streamlit as st

# ── Rutas y textos de la app ─────────────────────────
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"

APP_TITLE = "Scoring de contratación de fondos"
APP_DESCRIPTION = "Identifica clientes con mayor probabilidad de contratación"
PAGE_TITLE = "Scoring de contratación de fondos"

LOGO_CANDIDATOS = [
    "logo_scoring.png",
    "logo_scoring.jpg",
    "logo_scoring.jpeg",
    "logo_scoring.svg",
    "logo.png",
    "logo.jpg",
    "logo.jpeg",
    "logo.svg",
    "score.jpg",
]
FAVICON_CANDIDATOS = [
    "favicon.png",
    "favicon.ico",
    "favicon.jpg",
    "favicon.jpeg",
]

# ── Contrato de entrada (espejo verificado de api/schemas.py) ─────────────────────────
# Las claves son los alias exactos que espera la API (nombres originales del CSV).
# Los valores por defecto reproducen el ejemplo validado de `test_payload.json`.
CAMPOS_ENTRADA = [
    {
        "clave": "Edad",
        "tipo_dato": "float",
        "widget": "slider",
        "minimo": 17,
        "maximo": 100,
        "paso": 1,
        "defecto": 28,
        "ayuda": "Edad del cliente en años",
    },
    {
        "clave": "Trabajo",
        "tipo_dato": "str",
        "widget": "selectbox",
        "opciones": [
            "admin.",
            "blue-collar",
            "entrepreneur",
            "housemaid",
            "management",
            "retired",
            "self-employed",
            "services",
            "student",
            "technician",
            "unemployed",
            "unknown",
        ],
        "defecto": "management",
        "ayuda": "Categoría laboral del cliente",
    },
    {
        "clave": "Estado Civil",
        "tipo_dato": "str",
        "widget": "selectbox",
        "opciones": ["divorced", "married", "single", "unknown"],
        "defecto": "single",
        "ayuda": "Estado civil del cliente",
    },
    {
        "clave": "Fomación",
        "tipo_dato": "str",
        "widget": "selectbox",
        "opciones": [
            "basic.4y",
            "basic.6y",
            "basic.9y",
            "high.school",
            "illiterate",
            "professional.course",
            "university.degree",
            "unknown",
        ],
        "defecto": "university.degree",
        "ayuda": "Nivel de formación (clave original del contrato)",
    },
    {
        "clave": "Impago",
        "tipo_dato": "str",
        "widget": "selectbox",
        "opciones": ["no", "unknown", "yes"],
        "defecto": "no",
        "ayuda": "¿Tiene impagos registrados?",
    },
    {
        "clave": "Prestamo hipotecario",
        "tipo_dato": "str",
        "widget": "selectbox",
        "opciones": ["no", "unknown", "yes"],
        "defecto": "yes",
        "ayuda": "¿Tiene préstamo hipotecario?",
    },
    {
        "clave": "Prestamo Personal",
        "tipo_dato": "str",
        "widget": "selectbox",
        "opciones": ["no", "unknown", "yes"],
        "defecto": "no",
        "ayuda": "¿Tiene préstamo personal?",
    },
    {
        "clave": "Canal de contacto",
        "tipo_dato": "str",
        "widget": "selectbox",
        "opciones": ["cellular", "telephone"],
        "defecto": "cellular",
        "ayuda": "Canal del último contacto de campaña",
    },
    {
        "clave": "Mes",
        "tipo_dato": "str",
        "widget": "selectbox",
        "opciones": [
            "jan",
            "feb",
            "mar",
            "apr",
            "may",
            "jun",
            "jul",
            "aug",
            "sep",
            "oct",
            "nov",
            "dec",
        ],
        "defecto": "jun",
        "ayuda": "Mes del último contacto de campaña",
    },
    {
        "clave": "num contactos esta campaña",
        "tipo_dato": "int",
        "widget": "slider",
        "minimo": 1,
        "maximo": 60,
        "paso": 1,
        "defecto": 3,
        "ayuda": "Número de contactos en la campaña actual",
    },
    {
        "clave": "num días último contacto",
        "tipo_dato": "int",
        "widget": "number",
        "minimo": 0,
        "maximo": 999,
        "paso": 1,
        "defecto": 6,
        "ayuda": "Días desde el último contacto (999 = valor centinela del dataset)",
    },
    {
        "clave": "num contactos otras campañas",
        "tipo_dato": "int",
        "widget": "slider",
        "minimo": 0,
        "maximo": 30,
        "paso": 1,
        "defecto": 2,
        "ayuda": "Número de contactos en campañas anteriores",
    },
    {
        "clave": "resultado campaña anterior",
        "tipo_dato": "str",
        "widget": "selectbox",
        "opciones": ["failure", "nonexistent", "success"],
        "defecto": "success",
        "ayuda": "Resultado de la campaña anterior",
    },
    {
        "clave": "variación tasa empleo",
        "tipo_dato": "float",
        "widget": "slider",
        "minimo": -50,
        "maximo": 50,
        "paso": 1,
        "defecto": -17,
        "ayuda": "Variación del indicador de empleo (escala del dataset)",
    },
    {
        "clave": "euribor3m",
        "tipo_dato": "float",
        "widget": "number",
        "minimo": 0.0,
        "maximo": 10000.0,
        "paso": 1.0,
        "defecto": 729.0,
        "ayuda": "Euríbor 3 meses (escala del dataset)",
    },
]

# ── Agrupación de campos para el panel lateral ─────────────────────────
GRUPOS_ENTRADA = [
    ("Datos personales", ["Edad", "Trabajo", "Estado Civil", "Fomación"]),
    ("Productos y estado", ["Impago", "Prestamo hipotecario", "Prestamo Personal"]),
    ("Contacto y campaña", ["Canal de contacto", "Mes", "resultado campaña anterior"]),
    (
        "Historial de campañas",
        [
            "num contactos esta campaña",
            "num días último contacto",
            "num contactos otras campañas",
        ],
    ),
    ("Entorno económico", ["variación tasa empleo", "euribor3m"]),
]

INDICE_CAMPOS = {}
for campo in CAMPOS_ENTRADA:
    INDICE_CAMPOS[campo["clave"]] = campo

# ── Interpretación de la salida (niveles reales de la API) ─────────────────────────
INFO_CATEGORIAS = {
    "ALTA_PROBABILIDAD": {
        "color": "#22c55e",
        "estilo": "success",
        "titulo": "Alta probabilidad de contratación",
        "detalle": "Perfil prioritario para la campaña.",
    },
    "MEDIA_PROBABILIDAD": {
        "color": "#f59e0b",
        "estilo": "warning",
        "titulo": "Probabilidad media de contratación",
        "detalle": "Perfil a considerar según el resto de la cartera.",
    },
    "BAJA_PROBABILIDAD": {
        "color": "#ef4444",
        "estilo": "error",
        "titulo": "Baja probabilidad de contratación",
        "detalle": "Perfil no prioritario para esta campaña.",
    },
}

# ── Utilidades de assets ─────────────────────────
def buscar_asset(nombres_candidatos):
    """Devuelve la primera imagen existente en assets/ o None (carga protegida)."""
    for nombre in nombres_candidatos:
        ruta = ASSETS_DIR / nombre
        if ruta.exists():
            return ruta
    return None

# ── Cliente HTTP ─────────────────────────
def wake_api(warmup_url, max_wait=WARMUP_MAX_WAIT):
    """Despierta la API con GET /health. Devuelve True si responde 200/204.

    Con max_wait=0 hace un único intento (fallo rápido para API local).
    """
    instante_inicio = time.time()
    while True:
        try:
            respuesta = requests.get(warmup_url, timeout=WARMUP_TIMEOUT)
            if respuesta.status_code in (200, 204):
                return True
        except requests.RequestException:
            pass
        if time.time() - instante_inicio > max_wait:
            return False
        time.sleep(3)

def enviar_scoring(payload):
    """Envía el payload a POST /predict y devuelve el contrato interno de retorno.

    Estructura devuelta:
    - ok            : bool
    - status_code   : int | None
    - data          : objeto deserializado | None
    - error_message : str | None (mensaje legible y accionable)
    - raw_text      : str | None (diagnóstico)
    """
    resultado = {
        "ok": False,
        "status_code": None,
        "data": None,
        "error_message": None,
        "raw_text": None,
    }

    url = API_BASE_URL + SCORE_ENDPOINT
    intentos_totales = SCORING_RETRIES + 1

    for numero_intento in range(intentos_totales):
        try:
            respuesta = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
        except requests.Timeout:
            resultado["error_message"] = (
                "El servicio de scoring no respondió a tiempo. "
                "Puede estar despertando: vuelve a intentarlo en unos segundos."
            )
            continue
        except requests.ConnectionError:
            resultado["error_message"] = (
                "No hay conexión con la API de scoring. Comprueba que está "
                "arrancada y que API_BASE_URL apunta a la URL correcta."
            )
            continue
        except requests.RequestException as error:
            resultado["error_message"] = (
                f"Error de red al llamar a la API ({type(error).__name__}). "
                "Vuelve a intentarlo en unos segundos."
            )
            continue

        resultado["status_code"] = respuesta.status_code

        if respuesta.status_code != 200:
            if respuesta.status_code == 422:
                resultado["error_message"] = (
                    "La API rechazó los datos (HTTP 422): entrada incompatible "
                    "con el contrato. Revisa los campos enviados."
                )
            elif respuesta.status_code == 400:
                resultado["error_message"] = (
                    "La API rechazó la petición (HTTP 400). Revisa los datos enviados."
                )
            else:
                resultado["error_message"] = (
                    f"La API devolvió un error HTTP {respuesta.status_code}. "
                    "Vuelve a intentarlo en unos segundos."
                )
            resultado["raw_text"] = respuesta.text[:500]
            return resultado

        try:
            resultado["data"] = respuesta.json()
        except ValueError:
            resultado["error_message"] = (
                "La API respondió con un formato no JSON. Revisa el estado del servicio."
            )
            resultado["raw_text"] = respuesta.text[:500]
            return resultado

        resultado["ok"] = True
        return resultado

    return resultado

# ── Widgets y construcción del payload ─────────────────────────
def render_campo(campo):
    """Dibuja el widget del campo en el contexto actual y devuelve su valor."""
    clave = campo["clave"]
    ayuda = campo.get("ayuda")

    if campo["widget"] == "slider":
        return st.slider(
            clave,
            min_value=campo["minimo"],
            max_value=campo["maximo"],
            value=campo["defecto"],
            step=campo["paso"],
            help=ayuda,
        )

    if campo["widget"] == "number":
        return st.number_input(
            clave,
            min_value=campo["minimo"],
            max_value=campo["maximo"],
            value=campo["defecto"],
            step=campo["paso"],
            help=ayuda,
        )

    opciones = campo["opciones"]
    indice_defecto = 0
    if campo["defecto"] in opciones:
        indice_defecto = opciones.index(campo["defecto"])
    return st.selectbox(clave, options=opciones, index=indice_defecto, help=ayuda)

def construir_payload(valores_form):
    """Castea los valores del formulario al tipo esperado por el contrato."""
    payload = {}
    for campo in CAMPOS_ENTRADA:
        clave = campo["clave"]
        valor = valores_form[clave]
        if campo["tipo_dato"] == "float":
            payload[clave] = float(valor)
        elif campo["tipo_dato"] == "int":
            payload[clave] = int(valor)
        else:
            payload[clave] = str(valor)
    return payload

# ── Visualización del resultado ─────────────────────────
def construir_gauge_html(porcentaje, color):
    """Velocímetro SVG: zonas de color, aguja animada y valor central."""
    porcentaje_seguro = max(0.0, min(100.0, porcentaje))
    angulo_aguja = -90.0 + 1.8 * porcentaje_seguro

    largo_arco = 345.6
    fin_zona_baja = 0.40 * largo_arco
    fin_zona_media = 0.70 * largo_arco
    largo_zona_media = fin_zona_media - fin_zona_baja
    largo_zona_alta = largo_arco - fin_zona_media

    html = f"""
    <div style="display:flex;justify-content:center;">
      <svg viewBox="0 0 260 158" role="img" aria-label="Velocímetro de scoring"
           style="width:100%;max-width:540px;height:auto;display:block;margin:0 auto;">
        <path d="M 20 140 A 110 110 0 0 1 240 140" fill="none"
              stroke="#ef4444" stroke-opacity="0.35" stroke-width="16" stroke-linecap="butt"
              stroke-dasharray="{fin_zona_baja:.1f} 400"/>
        <path d="M 20 140 A 110 110 0 0 1 240 140" fill="none"
              stroke="#f59e0b" stroke-opacity="0.35" stroke-width="16" stroke-linecap="butt"
              stroke-dasharray="{largo_zona_media:.1f} 400"
              stroke-dashoffset="-{fin_zona_baja:.1f}"/>
        <path d="M 20 140 A 110 110 0 0 1 240 140" fill="none"
              stroke="#22c55e" stroke-opacity="0.35" stroke-width="16" stroke-linecap="butt"
              stroke-dasharray="{largo_zona_alta:.1f} 400"
              stroke-dashoffset="-{fin_zona_media:.1f}"/>
        <circle cx="130" cy="140" r="84" fill="{color}" fill-opacity="0.08"/>
        <line x1="130" y1="140" x2="130" y2="84"
              stroke="{color}" stroke-width="6" stroke-linecap="round">
          <animateTransform attributeName="transform" type="rotate"
                            from="-90 130 140" to="{angulo_aguja:.1f} 130 140"
                            dur="1.1s" fill="freeze"
                            calcMode="spline" keyTimes="0;1"
                            keySplines="0.2 0.8 0.2 1"/>
        </line>
        <circle cx="130" cy="140" r="10" fill="#0e1117"
                stroke="{color}" stroke-width="4"/>
        <text x="130" y="116" text-anchor="middle" font-size="30"
              font-weight="700" fill="#f0f6fc">{porcentaje_seguro:.1f}%</text>
        <text x="130" y="132" text-anchor="middle" font-size="9"
              fill="rgba(240,246,252,0.65)">SCORE DE CONTRATACIÓN</text>
        <text x="24" y="156" text-anchor="middle" font-size="9"
              fill="rgba(240,246,252,0.55)">0</text>
        <text x="236" y="156" text-anchor="middle" font-size="9"
              fill="rgba(240,246,252,0.55)">100</text>
      </svg>
    </div>
    """
    return html

# ── Interfaz de usuario ─────────────────────────
ruta_favicon = buscar_asset(FAVICON_CANDIDATOS)
if ruta_favicon is not None:
    icono_pagina = str(ruta_favicon)
else:
    icono_pagina = "📊"

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=icono_pagina,
    layout="wide",
)

if "ultimo_resultado" not in st.session_state:
    st.session_state["ultimo_resultado"] = None

if "celebracion_hecha" not in st.session_state:
    st.session_state["celebracion_hecha"] = False

st.markdown(
    """
    <style>
    .block-container {padding-top: 2.2rem;}
    section[data-testid="stSidebar"] {
        border-right: 1px solid rgba(240, 246, 252, 0.08);
    }
    section[data-testid="stSidebar"] div[data-testid="stForm"] {
        border: none;
        padding: 0;
        background: transparent;
    }
    .a12-gauge-card {
        border: 1px solid rgba(240, 246, 252, 0.08);
        border-radius: 18px;
        padding: 1.4rem 1rem 0.9rem 1rem;
        background: radial-gradient(120% 130% at 50% 0%,
                    rgba(79, 139, 249, 0.10) 0%,
                    rgba(13, 17, 23, 0.0) 65%);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Cabecera ─────────────────────────
columnas_cabecera = st.columns([2, 1])
with columnas_cabecera[0]:
    st.title(APP_TITLE)
    st.markdown(APP_DESCRIPTION)
with columnas_cabecera[1]:
    ruta_logo = buscar_asset(LOGO_CANDIDATOS)
    if ruta_logo is not None:
        st.image(str(ruta_logo), width=300)

st.divider()

# ── Zona de entrada (sidebar) ─────────────────────────
with st.sidebar:
    st.header("Parámetros del cliente")
    st.caption(
        "ℹ️ Si el servicio estaba inactivo, la primera ejecución puede tardar "
        "hasta un minuto mientras se activa. La app reintenta automáticamente."
    )

    valores_form = {}
    with st.form("parametros_entrada_form"):
        for titulo_grupo, claves_grupo in GRUPOS_ENTRADA:
            st.markdown(f"**{titulo_grupo}**")
            for clave in claves_grupo:
                campo = INDICE_CAMPOS.get(clave)
                if campo is not None:
                    valores_form[clave] = render_campo(campo)
        enviado = st.form_submit_button("Resultado", type="primary")

if enviado:
    payload = construir_payload(valores_form)

    servicio_activo = True
    if ENABLE_WARMUP:
        with st.spinner(f"Conectando con el servicio de scoring ({API_BASE_URL})..."):
            if API_ES_LOCAL:
                # Fallo rápido: una API local que no responde no está arrancada.
                servicio_activo = wake_api(API_BASE_URL + WARMUP_ENDPOINT, max_wait=0)
            else:
                servicio_activo = False
                for numero_ciclo in range(WARMUP_RETRIES + 1):
                    if wake_api(API_BASE_URL + WARMUP_ENDPOINT):
                        servicio_activo = True
                        break

    if not servicio_activo:
        if API_ES_LOCAL:
            mensaje_error = (
                f"La API local no responde en {API_BASE_URL}. Opciones: "
                "(1) arráncala en otra terminal con "
                "cd 07_despliegue/deploy-ready/api_render && "
                "uv run uvicorn api.main:app --reload; "
                "(2) si quieres usar la API de Render, cambia API_BASE_URL "
                "en la configuración de app.py. "
                "Después vuelve a pulsar «Resultado»."
            )
        else:
            mensaje_error = (
                "La API no respondió al intento de activación. Comprueba que "
                "está accesible en la URL configurada y vuelve a pulsar «Resultado»."
            )
        st.session_state["ultimo_resultado"] = {
            "ok": False,
            "status_code": None,
            "data": None,
            "error_message": mensaje_error,
            "raw_text": None,
        }
    else:
        with st.spinner("Calculando el scoring..."):
            st.session_state["ultimo_resultado"] = enviar_scoring([payload])
        st.session_state["celebracion_hecha"] = False

st.divider()

# ── Panel de resultado ─────────────────────────
st.subheader("Resultado")
resultado_actual = st.session_state["ultimo_resultado"]

if resultado_actual is None:
    st.info(
        "Configura los parámetros en el panel lateral y pulsa «Resultado» "
        "para obtener el scoring del cliente."
    )
elif not resultado_actual["ok"]:
    st.error(resultado_actual["error_message"] or "No se pudo obtener el scoring.")
    if resultado_actual["status_code"] is not None or resultado_actual["raw_text"]:
        with st.expander("Detalle técnico"):
            if resultado_actual["status_code"] is not None:
                st.write(f"Código HTTP: {resultado_actual['status_code']}")
            if resultado_actual["raw_text"]:
                st.code(resultado_actual["raw_text"])
else:
    datos = resultado_actual["data"]
    if isinstance(datos, list) and len(datos) > 0:
        datos = datos[0]

    registro_id = datos.get("registro_id", "—")
    score = float(datos.get("score_contratacion", 0.0))
    prediccion = int(datos.get("prediccion_binaria", 0))
    categoria = str(datos.get("categoria", ""))
    porcentaje = score * 100.0

    info_categoria = INFO_CATEGORIAS.get(categoria)
    if info_categoria is not None:
        color = info_categoria["color"]
    else:
        color = "#4f8bf9"

    columna_gauge, columna_panel = st.columns([3, 2])

    with columna_gauge:
        st.markdown(
            f"<div style='text-align:center;font-size:1.05rem;opacity:0.85;'>"
            f"El scoring del cliente ID <b>{registro_id}</b> es</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="a12-gauge-card">{construir_gauge_html(porcentaje, color)}</div>',
            unsafe_allow_html=True,
        )

    with columna_panel:
        if info_categoria is not None:
            st.markdown(
                f'<div style="text-align:center;margin-bottom:0.6rem;">'
                f'<span style="background:{info_categoria["color"]}22;'
                f'color:{info_categoria["color"]};padding:6px 16px;'
                f'border-radius:999px;font-weight:700;letter-spacing:0.4px;'
                f'border:1px solid {info_categoria["color"]}66;">'
                f'{categoria}</span></div>',
                unsafe_allow_html=True,
            )
            mensaje = f"**{info_categoria['titulo']}** — {info_categoria['detalle']}"
            if info_categoria["estilo"] == "success":
                st.success(mensaje)
            elif info_categoria["estilo"] == "warning":
                st.warning(mensaje)
            else:
                st.error(mensaje)
        else:
            st.info(f"Categoría devuelta por la API: {categoria}")

        if prediccion == 1:
            st.caption("Predicción del modelo: contratará")
        else:
            st.caption("Predicción del modelo: no contratará")
        st.caption(f"Registro evaluado: ID {registro_id}")

    if categoria == "ALTA_PROBABILIDAD" and not st.session_state["celebracion_hecha"]:
        st.balloons()
        st.session_state["celebracion_hecha"] = True

    if DEBUG_MODE:
        with st.expander("Respuesta completa de la API (debug)"):
            st.json(datos)

st.divider()

# ── Configuración de conexión (avanzado, colapsado) ─────────────────────────
st.caption(
    "API de scoring configurada en `app.py`. Verifica que `API_BASE_URL` "
    "apunta a la URL pública real de tu API antes de usar la app desplegada."
)
with st.expander("⚙️ Configuración de conexión (avanzado)"):
    st.markdown(f"**API configurada:** `{API_BASE_URL}`")
    st.markdown(
        "Por defecto apunta al entorno local validado por A_11. No asumas que "
        "esta URL es válida para tu caso: la API debe estar desplegada y "
        "accesible antes de usar la app en Render, y `API_BASE_URL` debe "
        "actualizarse a la URL pública (por ejemplo, "
        "`https://tu-api.onrender.com`)."
    )
    st.markdown(
        f"Timeout de scoring: {DEFAULT_TIMEOUT} s · Timeout de warmup: "
        f"{WARMUP_TIMEOUT} s · Reintentos de scoring: {SCORING_RETRIES} · "
        f"Warmup activado: {ENABLE_WARMUP}"
    )
