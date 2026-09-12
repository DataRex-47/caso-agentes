# Script - Organización con sidebar y columnas

import pandas as pd
import seaborn as sns
import streamlit as st
import matplotlib.pyplot as plt
import time


# Sidebar: Input

with st.sidebar:
    archivo = st.file_uploader("Selecciona un archivo csv")


# Carga de datos


@st.cache_data()
def cargar_datos(archivo):
    if archivo is None:
        st.stop()
    df = pd.read_csv(archivo)
    time.sleep(3)
    return df


df = cargar_datos(archivo)

# Selector de variable

with st.sidebar:
    variable = st.selectbox("Selecciona una variable:", df.columns.to_list())

# Zona central: Resultados

col1, col2,col3 = st.columns((2, 2,1))

# Gráfico

with col1:
    fig, ax = plt.subplots()
    sns.histplot(data=df, x=variable, ax=ax)
    plt.xticks(rotation=45)
    st.pyplot(fig)


# Tabla de frecuencias

with col2:
    tabla_resumen = df[variable].value_counts().reset_index()
    tabla_resumen.columns = [variable, "Frecuencia"]
    st.dataframe(tabla_resumen, use_container_width=True)

#Basura
with col3:
    st.write("hola hermosa")
