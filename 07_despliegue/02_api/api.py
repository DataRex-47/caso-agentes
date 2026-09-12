"""
API de Scoring - Caso Agentes

Este script expone el motor de scoring definido en `scoring.py` mediante FastAPI.

Responsabilidades de este script:
- Recibir datos de entrada (JSON)
- Validar formato con Pydantic (schema)
- Adaptar la entrada al formato esperado por el motor (`scoring_df`)
- Ejecutar inferencia (sin lógica de entrenamiento / batch)
- Devolver la predicción
"""

from typing import Optional

import pandas as pd
from pathlib import Path
from fastapi import FastAPI, Request
from pydantic import BaseModel, Field

from scoring import scoring_df

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


# Schemas (Pydantic)
# Definimos los modelos de entrada y salida.


class RegistroEntrada(BaseModel):

    registro_raw_id: int = Field(alias="Unnamed: 0")

    edad: Optional[float] = Field(default=None, alias="Edad")
    trabajo: Optional[str] = Field(default=None, alias="Trabajo")
    estado_civil: Optional[str] = Field(default=None, alias="Estado Civil")

    # Ojo: en el dataset original aparece como "Fomación" (typo)
    formacion: Optional[str] = Field(default=None, alias="Fomación")

    impago: Optional[str] = Field(default=None, alias="Impago")
    prestamo_hipotecario: Optional[str] = Field(
        default=None, alias="Prestamo hipotecario"
    )
    prestamo_personal: Optional[str] = Field(default=None, alias="Prestamo Personal")

    canal_contacto: Optional[str] = Field(default=None, alias="Canal de contacto")
    mes: Optional[str] = Field(default=None, alias="Mes")
    dia_de_la_semana: Optional[str] = Field(default=None, alias="Dia de la semana")

    num_contactos_esta_campana: Optional[int] = Field(
        default=None, alias="num contactos esta campaña"
    )
    num_dias_ultimo_contacto: Optional[int] = Field(
        default=None, alias="num días último contacto"
    )
    num_contactos_otras_campanas: Optional[int] = Field(
        default=None, alias="num contactos otras campañas"
    )

    resultado_campana_anterior: Optional[str] = Field(
        default=None, alias="resultado campaña anterior"
    )
    variacion_tasa_empleo: Optional[float] = Field(
        default=None, alias="variación tasa empleo"
    )
    euribor3m: Optional[float] = None

    class Config:
        # Permite poblar por el nombre del campo o por el alias
        populate_by_name = True


class PrediccionSalida(BaseModel):
    # Definimos el modelo de salida (respuesta) de la API.

    registro_id: int
    score_contratacion: float


# App FastAPI

api = FastAPI(
    title="API Scoring - Caso Agentes",
    description="API de predicción de contratación de productos bancarios",
    version="1.0",
)

# BASE_DIR permite localizar de forma robusta la carpeta templates.
BASE_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# Funciones de los endpoints
# Son funciones normales de Python. Todavía no están dadas de alta en la API:
# el alta se hace más abajo, en el bloque de registro.


def predict(registro: RegistroEntrada):
    """
    Endpoint principal de inferencia.

    Flujo:
    1) Pydantic valida y tipa el JSON (RegistroEntrada)
    2) Convertimos a dict usando los alias RAW (by_alias=True)
    3) Construimos un DataFrame de una fila (formato esperado por scoring_df)
    4) scoring_df devuelve un DataFrame con ['registro_id', 'score_contratacion']
    5) Devolvemos la primera fila como dict
    """
    # Dict con claves RAW (las que espera el motor / batch)
    registro_dict_raw = registro.model_dump(by_alias=True)

    # DataFrame de una fila
    df_input = pd.DataFrame([registro_dict_raw])

    # Inferencia con el motor ya validado (batch en memoria)
    df_resultado = scoring_df(df_input)

    # Respuesta (primera fila)
    return df_resultado.iloc[0].to_dict()


def health():
    """
    Endpoint de salud: confirma que la API está operativa.
    """
    return {"status": "ok"}


def demo(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="formulario_scoring.html",
        context={"request": request},
    )

# ── Registro manual de los endpoints ────────────────────────────────
# Equivalente exacto a poner @api.post(...) / @api.get(...) encima de cada
# función. api.post("/ruta", ...) devuelve una función de registro; el segundo
# paréntesis le pasa la función que atiende esa ruta.
api.post("/predict", response_model=PrediccionSalida)(predict)
api.get("/health")(health)
api.get("/demo", response_class=HTMLResponse)(demo)


type(templates)