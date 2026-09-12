# A_08 — Resumen de Limpieza y Pre-producción

> **Rol**: A_08_Limpieza · **Tipo de trabajo**: análisis estático de código (sin ejecución)
> **Fecha**: 2026-09-07

---

## 1. FASE 0 — Mapeo del proyecto (solo lectura)

### 1.1 Estructura confirmada

- `03_notebooks/` → notebooks de desarrollo `01_Importacion_Datos.ipynb` … `07_Modelizacion.ipynb`
- `02_datos/01_Originales/` → datos crudos de **solo lectura**
- `02_datos/03_Entrenamiento/` → tablones intermedios (pkl)
- `07_despliegue/pre-produccion/` → carpeta de entregables (creada en esta fase)

### 1.2 Ruta canónica de datos (fuente original)

```
02_datos/01_Originales/contratacion_fondos.csv
```

- Nombre de archivo extraído de A_01 (`pd.read_csv(ORIGINALES / 'contratacion_fondos.csv', index_col=0, encoding='utf-8')`).
- **Una única lectura** de CSV en A_01: corresponde al flujo principal.
- El CSV tiene una primera columna **sin nombre** (será el índice con `index_col=0`) y 17 columnas de datos.

### 1.3 Columnas RAW del CSV (según cabecera)

```
Edad, Trabajo, Estado Civil, Fomación, Impago, Prestamo hipotecario, Prestamo Personal,
Canal de contacto, Mes, Dia de la semana, num contactos esta campaña, num días último contacto,
num contactos otras campañas, resultado campaña anterior, variación tasa empleo, euribor3m,
contrata_fondos
```

> Nota: `Fomación` es un typo del CSV (falta la «r»). Se corrige a `formacion` en A_02.

### 1.4 Cadena de notebooks y artefactos intermedios

| Nota | Notebook | Lee | Escribe | ¿Transforma? |
|------|----------|-----|---------|--------------|
| A_01 | Importacion_Datos | CSV original | `01_train_tablon_integrado.pkl`, `validation.pkl` | Sí (split train/val) |
| A_02 | Calidad_Datos | `01_train_tablon_integrado.pkl` | `02_train_tablon_calidad.pkl` | Sí (renombrado, categorías, duplicados, imputación, cast) |
| A_03 | EDA | `02_train_tablon_calidad.pkl` | `03_train_tablon_eda.pkl` | No (solo inspección / gráficos) |
| A_04 | PrepracionDatos | `03_train_tablon_eda.pkl` | `04_train_tablon_transformado.pkl` | Sí (OHE, cíclicas, escalado) |
| A_05 | Selector | `04_train_tablon_transformado.pkl` | `05_train_tablon_preseleccion.pkl`, `Variables_preseleccionadas.txt` | Sí (selección de features) |
| A_06 | Balanceador | `05_train_tablon_preseleccion.pkl` | informe balanceo | Sí (solo diagnóstico; **decisión: NO balancear**) |
| A_07 | Modelizacion | `05_train_tablon_preseleccion.pkl` | `config_mejor_modelo.json`, rankings | No (entrena/evalúa, no transforma el df) |

---

## 2. FASE 1 — Integración lineal de celdas transformadoras

Se han recorrido A_01..A_07 en orden y se han recopilado **todas las celdas que transforman datos** (según la definición del rol: renombrado, casts, imputaciones, borrado, OHE, escalado, selección…).

### 2.1 Celdas integradas por notebook

| Notebook | Celdas transformadoras integradas |
|----------|-----------------------------------|
| A_01 | lectura CSV original; split train/val sin leakage |
| A_02 | renombrado de columnas (snake_case + corrección `Fomación`); cast a `category`; eliminación de duplicados; drop de `dia_de_la_semana`; imputación de `formacion` y `edad`; cast `edad` a `int64` |
| A_03 | (ninguna) |
| A_04 | FASE 0..4: ordinal + imputación de `formacion`, imputación de `num_dias`, log1p de contactos, OHE, flag `contactado_previamente`, seno/coseno de `mes`, escalado estándar, unión final |
| A_05 | selección de las 12 variables finalistas (listado fijo) |
| A_06 | (decisión documentada: sin balanceo; no se integra ninguna transformación de resampling) |
| A_07 | entrenamiento del modelo ganador (RandomForestClassifier) |

### 2.2 Observaciones

- **A_03 (EDA)** no contiene ninguna operación de transformación: solo inspección y gráficos. Se omitió por completo.
- **A_06 (Balanceador)** concluye que **no se balancea** (el modelo ganador usa `class_weight=None`, AUC 0.777 con/sin balanceo). No se integra resampling.
- **Duplicidad / caminos alternativos**: A_02..A_07 leen tablones pickle intermedios. En el notebook 08 se reemplaza esa lectura por el DataFrame en memoria que resulta de la etapa anterior, respetando el mismo orden y el mismo resultado (la única fuente original es el CSV).
- Las 12 variables finalistas coinciden exactamente con `01_Documentos/Variables_preseleccionadas.txt` y con la lista `variables_preseleccionadas_final` de A_05.

---

## 3. FASE 2 — Limpieza y enfoque en el modelo final (DAG de dependencias)

A partir del notebook 08 integrado se construyó el DAG de dependencias y se eliminaron:

- Inspecciones y prints decorativos (`df.info()`, `df.head()`, `✅ …`).
- Columnas intermedias que no alimentan ninguna feature finalista (`sin_contacto_previo`, `formacion_oe`, `num_dias_rec`, etc. se mantienen como pasos intermedios internos pero no se persisten).
- El paso de A_05 (RFECV, MI, PI, consenso, correlación) se sustituye por la **selección directa** de la lista de 12 variables finalistas, que es el resultado real de A_05. No se re-ejecuta la búsqueda de selección porque las 12 variables ya están fijadas en `Variables_preseleccionadas.txt`.

### 3.1 DAG de dependencias (resumen)

```
CSV original
   └─ P01 split train/val (70/30, estratificado)
        └─ P02 renombrado de columnas
             └─ P03 cast a `category`
                  └─ P04 eliminación de duplicados (28015 filas)
                       └─ P05 drop `dia_de_la_semana` + imputar `formacion` y `edad`
                            └─ P06 cast `edad` a `int64`
                                 └─ P07..P10 FASE 1 (ordinal/log/imputación numéricas)
                                      └─ P11..P14 FASE 2 (OHE, cíclicas mes)
                                           └─ P15 FASE 3 (StandardScaler)
                                                └─ P16 FASE 4 (unión df_final)
                                                     └─ P17 selección de 12 features finalistas
                                                          └─ P18 entrenamiento RandomForest final
```

### 3.2 Features finalistas generadas

| Feature | Tipo | Origen |
|---------|------|--------|
| `trabajo_student` | int8 | OHE sobre `trabajo` |
| `impago_unknown` | int8 | OHE sobre `impago` |
| `prestamo_hipotecario_yes` | int8 | OHE sobre `prestamo_hipotecario` |
| `canal_de_contacto_telephone` | int8 | OHE sobre `canal_de_contacto` |
| `mes_sin` | float64 | cíclica seno de `mes` |
| `mes_cos` | float64 | cíclica coseno de `mes` |
| `resultado_campana_anterior_nonexistent` | int8 | OHE sobre `resultado_campana_anterior` |
| `resultado_campana_anterior_success` | int8 | OHE sobre `resultado_campana_anterior` |
| `edad_ss` | float64 | StandardScaler sobre `edad` |
| `num_contactos_esta_campana_log_ss` | float64 | log1p + StandardScaler |
| `variacion_tasa_empleo_ss` | float64 | StandardScaler |
| `euribor3m_ss` | float64 | StandardScaler |

### 3.3 Modelo final

- **Clase**: `RandomForestClassifier` (scikit-learn)
- **Hiperparámetros** (extraídos de `06_resultados/Modelizacion/config_mejor_modelo.json`):
  - `n_estimators=300`, `max_depth=10`, `min_samples_split=2`, `min_samples_leaf=1`
  - `max_features='sqrt'`, `random_state=42`, `n_jobs=-1`, `class_weight=None`
- **Métrica de validación**: `roc_auc` sobre `StratifiedKFold(3, shuffle=True, random_state=42)`
  - AUC CV esperada ≈ **0,8006 ± 0,0024**
- **Objetivo**: `contrata_fondos` (clasificación binaria, ~11,54% positivos)

---

## 4. Decisiones de diseño del notebook 08

1. **Rutas**: construidas con `pathlib.from cwd` (`03_notebooks/`), sin rutas absolutas.
2. **Solo código real**: no hay pseudo-código ni bloques «representativos». Las únicas celdas escritas por el agente son la de título, imports/rutas, verificación de ruta y lectura del CSV (adaptación mínima de ruta).
3. **Sin persistencia de artefactos** (eso corresponde a A_09). El notebook entrena el modelo final y reporta AUC CV, pero no serializa pipelines ni modelos.
4. **Sin balanceo** (decisión de A_06).
5. **Sin celdas markdown** salvo el título inicial.

---

## 5. Entregables generados

- `03_notebooks/08_Preproduccion.ipynb` — notebook finalista ejecutable.
- `07_despliegue/pre-produccion/00_manifiesto_preproduccion.json` — contrato máquina-legible para A_09.
- `07_despliegue/pre-produccion/00_resumen_limpieza.md` — este documento.
