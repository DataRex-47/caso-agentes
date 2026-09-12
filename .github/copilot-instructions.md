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

**Fase completada**: A_08_Limpieza

**Notebook finalista**: `03_notebooks/08_Preproduccion.ipynb`

**Manifiesto para A_09**: `07_despliegue/pre-produccion/00_manifiesto_preproduccion.json`

**Siguiente paso**: Ejecutar A_09_Pipelines

**Estructura del dataframe**:
```
<class 'pandas.DataFrame'>
RangeIndex: 28015 entries, 0 to 28014
Data columns (total 13 columns):
 #   Column                                  Non-Null Count  Dtype
---  ------                                  --------------  -----
 0   trabajo_student                         28015 non-null  int8
 1   impago_unknown                          28015 non-null  int8
 2   prestamo_hipotecario_yes                28015 non-null  int8
 3   canal_de_contacto_telephone             28015 non-null  int8
 4   mes_sin                                 28015 non-null  float64
 5   mes_cos                                 28015 non-null  float64
 6   resultado_campana_anterior_nonexistent  28015 non-null  int8
 7   resultado_campana_anterior_success      28015 non-null  int8
 8   edad_ss                                 28015 non-null  float64
 9   num_contactos_esta_campana_log_ss       28015 non-null  float64
 10  variacion_tasa_empleo_ss                28015 non-null  float64
 11  euribor3m_ss                            28015 non-null  float64
 12  contrata_fondos                         28015 non-null  int64
dtypes: float64(6), int64(1), int8(6)
memory usage: 1.7 MB
```
