"""
Script de reentrenamiento con hiperparametrización y selección de modelo.
Genera el artefacto pipeline completo listo para producción.
"""

import pandas as pd
import numpy as np
import unicodedata
from pathlib import Path
from sklearn.pipeline import make_pipeline
from sklearn.compose import make_column_transformer
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold
from category_encoders import TargetEncoder
import cloudpickle

PROJECT_ROOT = Path(__file__).parent.parent
CSV_PATH = PROJECT_ROOT / "02_datos" / "01_Originales" / "contratacion_fondos.csv"
TARGET = "contrata_fondos"
ARTEFACTO_PATH = PROJECT_ROOT / "07_despliegue" / "artefacto_pipeline.pkl"
RANDOM_STATE = 42


def prepara_datos(df):
    if "Fomación" in df.columns:
        df = df.rename(columns={"Fomación": "Formación"})

    def limpiar_nombre(col):
        col = "".join(
            c
            for c in unicodedata.normalize("NFD", col)
            if unicodedata.category(c) != "Mn"
        )
        col = col.lower().replace(" ", "_").replace("-", "_")
        col = (
            col.replace("á", "a")
            .replace("é", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ú", "u")
            .replace("ñ", "n")
        )
        while "__" in col:
            col = col.replace("__", "_")
        return col.strip("_")

    df.columns = [limpiar_nombre(c) for c in df.columns]
    if "dia_de_la_semana" in df.columns:
        df = df.drop(columns=["dia_de_la_semana"])
    return df


print(f"Cargando datos desde: {CSV_PATH}")
df = pd.read_csv(CSV_PATH, sep=",", encoding="utf-8")
df = prepara_datos(df)
X = df.drop(columns=[TARGET])
y = df[TARGET]

cat_ohe = [
    "trabajo",
    "estado_civil",
    "formacion",
    "impago",
    "prestamo_hipotecario",
    "prestamo_personal",
    "canal_de_contacto",
    "mes",
    "resultado_campana_anterior",
]
cat_oe = ["formacion", "mes"]
cat_te = ["trabajo", "resultado_campana_anterior"]
num_cols = [
    "edad",
    "num_contactos_esta_campana",
    "num_dias_ultimo_contacto",
    "num_contactos_otras_campanas",
    "variacion_tasa_empleo",
    "euribor3m",
]

te = TargetEncoder(cols=cat_te)
X_te = te.fit_transform(X[cat_te], y)
X_te.columns = [f"{c}__te" for c in cat_te]
X_final = pd.concat([X, X_te], axis=1)

preprocesador = make_column_transformer(
    (
        make_pipeline(
            SimpleImputer(strategy="constant", fill_value="unknown"),
            OneHotEncoder(sparse_output=False, handle_unknown="ignore", drop="first"),
        ),
        cat_ohe,
    ),
    (
        make_pipeline(
            SimpleImputer(strategy="constant", fill_value="unknown"),
            OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1),
        ),
        cat_oe,
    ),
    (make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), num_cols),
    remainder="drop",
)

modelos = [
    ("randomforestclassifier", RandomForestClassifier(random_state=RANDOM_STATE)),
    (
        "histgradientboostingclassifier",
        HistGradientBoostingClassifier(random_state=RANDOM_STATE),
    ),
    (
        "logisticregression",
        LogisticRegression(solver="lbfgs", max_iter=500, random_state=RANDOM_STATE),
    ),
]

param_grid = [
    {
        "randomforestclassifier__n_estimators": [50, 100, 200, 300],
        "randomforestclassifier__max_depth": [3, 5, 10, None],
        "randomforestclassifier__min_samples_split": [2, 5, 10],
    },
    {
        "histgradientboostingclassifier__learning_rate": [0.01, 0.05, 0.1],
        "histgradientboostingclassifier__max_iter": [100, 200, 300],
        "histgradientboostingclassifier__max_depth": [3, 5, 10],
    },
    {
        "logisticregression__C": np.logspace(-2, 2, 10),
        "logisticregression__penalty": ["l2"],
        "logisticregression__solver": ["lbfgs"],
        "logisticregression__max_iter": [500],
    },
]

mejor_score = -np.inf
mejor_pipe = None
mejor_params = None
mejor_nombre = None
cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_STATE)
for (nombre, modelo), params in zip(modelos, param_grid):
    pipe = make_pipeline(preprocesador, modelo)
    search = RandomizedSearchCV(
        estimator=pipe,
        param_distributions=params,
        n_iter=20,
        cv=cv,
        scoring="roc_auc",
        n_jobs=-1,
        random_state=RANDOM_STATE,
        refit=True,
        verbose=0,
    )
    search.fit(X_final, y)
    if search.best_score_ > mejor_score:
        mejor_score = search.best_score_
        mejor_pipe = search.best_estimator_
        mejor_params = search.best_params_
        mejor_nombre = nombre

print("=" * 80)
print(f"Mejor modelo: {mejor_nombre}")
print(f"Mejores hiperparámetros: {mejor_params}")
print(f"Mejor ROC-AUC (CV): {mejor_score:.4f}")
print("=" * 80)

artefacto = {
    "pipeline": mejor_pipe,
    "target_encoder": te,
    "columnas_te": cat_te,
    "metadata": {
        "best_model": mejor_nombre,
        "best_params": mejor_params,
        "best_score": mejor_score,
        "cv_folds": 3,
        "metric": "roc_auc",
        "random_state": RANDOM_STATE,
    },
}
with open(ARTEFACTO_PATH, "wb") as f:
    cloudpickle.dump(artefacto, f)
print("✅ Artefacto guardado exitosamente")
print("✅ Reentrenamiento completado")
