# ── Imports ─────────────────────────────────────────────────────────
from pathlib import Path

import cloudpickle
import numpy as np
import pandas as pd
from sklearn.compose import make_column_transformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.model_selection import RandomizedSearchCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

# ── Constantes ──────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = PROJECT_ROOT / "02_datos" / "01_Originales" / "contratacion_fondos.csv"
TARGET = "contrata_fondos"
ARTEFACTO_PATH = PROJECT_ROOT / "07_despliegue" / "artefacto_pipeline.pkl"

# Mapeo de abreviaturas de mes (formato inglés del dataset) a número 1-12.
MAP_MES = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
           'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}

# ── 1. Función de filas (solo si es necesaria) ──────────────────────
def prepara_datos(df):
    return df.drop_duplicates(keep='first')

# ── 2. Definición de columnas ───────────────────────────────────────
cat_cols = ['Trabajo', 'Impago', 'Prestamo hipotecario',
            'Canal de contacto', 'resultado campaña anterior']
num_cols = ['Edad', 'variación tasa empleo', 'euribor3m']
mes_col = ['Mes']
contactos_col = ['num contactos esta campaña']


# Transformación custom: mes -> sin/cos (codificación cíclica del mes).
def _mes_sin_cos(df):
    mes_num = df['Mes'].map(MAP_MES).astype(float)
    angulo = 2 * np.pi * mes_num / 12
    return np.column_stack([np.sin(angulo), np.cos(angulo)])


mes_transformer = FunctionTransformer(_mes_sin_cos, validate=False)

# ── 3. ColumnTransformer ────────────────────────────────────────────
preprocesador = make_column_transformer(
    (make_pipeline(SimpleImputer(strategy='median'), StandardScaler()), num_cols),
    (make_pipeline(SimpleImputer(strategy='most_frequent'),
                   OneHotEncoder(handle_unknown='ignore', drop='first')), cat_cols),
    (make_pipeline(SimpleImputer(strategy='median'),
                   FunctionTransformer(np.log1p, validate=False),
                   StandardScaler()), contactos_col),
    (mes_transformer, mes_col),
    remainder='drop',
)

# ── 4. Modelo base ──────────────────────────────────────────────────
modelo_base = RandomForestClassifier(random_state=42)
pipe = make_pipeline(preprocesador, modelo_base)

# ── 5. Espacio de hiperparámetros ───────────────────────────────────
param_distributions = {
    'randomforestclassifier__n_estimators': [200, 300],
    'randomforestclassifier__max_depth': [None, 10, 20, 30],
    'randomforestclassifier__min_samples_split': [2, 5, 10],
    'randomforestclassifier__min_samples_leaf': [1, 2, 4],
    'randomforestclassifier__class_weight': [None, 'balanced'],
}

search = RandomizedSearchCV(
    estimator=pipe,
    param_distributions=param_distributions,
    n_iter=15,
    cv=3,
    scoring='roc_auc',
    n_jobs=-1,
    random_state=42,
    refit=True,
)

# ── 6. Carga de datos y preparación ─────────────────────────────────
df = pd.read_csv(CSV_PATH, index_col=0, encoding='utf-8')
df = prepara_datos(df)

X = df.drop(columns=[TARGET])
y = df[TARGET].astype(int)

# ── 7. Hiperparametrización + entrenamiento ─────────────────────────
search.fit(X, y)
best_pipe = search.best_estimator_
print('Mejores hiperparámetros:', search.best_params_)
print('Mejor score de validación:', search.best_score_)

# ── 8. Serialización del mejor pipeline ─────────────────────────────
with open(ARTEFACTO_PATH, 'wb') as f:
    cloudpickle.dump(best_pipe, f)

import seaborn as sns
import matplotlib.pyplot as plt
sns.barplot(x=list(search.best_params_.keys()), y=list(search.best_params_.values()))
plt.xticks(rotation=45)
plt.show()
