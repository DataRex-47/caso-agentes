import streamlit as st
import requests

st.set_page_config(
    page_title="Scoring de contratación",
    page_icon="media/DS4B_favicon.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Scoring de contratación de clientes")

st.write(
    "Aplicación cliente que consume una API de scoring y muestra el resultado en tiempo real."
)

with st.sidebar:
    st.image("media/score.jpg")
    st.divider()  # barra de separación

    
# URL del servicio (API en local)
API_URL = "http://127.0.0.1:8000/predict"


# SIDEBAR: Inputs del usuario

with st.sidebar:
    st.markdown("### Datos del cliente")

    edad = st.number_input("Edad", min_value=18, max_value=100)

    trabajo = st.selectbox(
        "Trabajo", ["blue-collar", "technician", "admin.", "services", "management"]
    )

    estado_civil = st.selectbox("Estado Civil", ["married", "single", "divorced"])

    euribor = st.number_input("Euribor 3m")

    num_contactos = st.number_input("Num contactos esta campaña", min_value=0)

    # Espacio en blanco
    st.markdown("###")

    ejecutar = st.button("Calcular score")


# PROCESO: Llamada a la API

if ejecutar:

    # Construcción dinámica del JSON
    payload = {
        "Unnamed: 0": 1,
        "Edad": edad,
        "Trabajo": trabajo,
        "Estado Civil": estado_civil,
        "Fomación": "basic.4y",
        "Impago": "unknown",
        "Prestamo hipotecario": "yes",
        "Prestamo Personal": "no",
        "Canal de contacto": "cellular",
        "Mes": "aug",
        "Dia de la semana": "mon",
        "num contactos esta campaña": num_contactos,
        "num días último contacto": 999,
        "num contactos otras campañas": 0,
        "resultado campaña anterior": "nonexistent",
        "variación tasa empleo": 142,
        "euribor3m": euribor,
    }

    response = requests.post(API_URL, json=payload)

    # OUTPUT: Mostrar resultado

    if response.ok:

        resultado = response.json()

        # Centramos visualmente el resultado
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            st.metric("Score de contratación", f"{resultado['score_contratacion']:.2%}")

            # Interpretación simple de negocio
            if resultado["score_contratacion"] > 0.5:
                st.success("Alta probabilidad de contratación")
            else:
                st.warning("Baja probabilidad de contratación")

    else:
        st.error("Error en la respuesta de la API")