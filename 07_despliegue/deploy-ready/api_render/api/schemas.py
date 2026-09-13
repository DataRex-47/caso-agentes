"""
Contrato externo oficial de la API de scoring.

Derivado del flujo real de `02_produccion_scoring.py`.

- input_externo_tolerado     : nombres originales del CSV (typo "Fomación").
- input_canonico_interno     : snake_case sin acentos, tras `prepara_datos`.
- contrato_publico_propuesto : nombres externos tolerados.

Exclusiones: `contrata_fondos` (target), `Unnamed: 0` (ID generado),
`Dia de la semana` (el flujo lo elimina).
"""

from pydantic import BaseModel, ConfigDict, Field


# ── Contrato externo de entrada ─────────────────────────
class RegistroEntrada(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    edad: float = Field(..., alias="Edad")
    trabajo: str = Field(..., alias="Trabajo")
    estado_civil: str = Field(..., alias="Estado Civil")
    formacion: str = Field(..., alias="Fomación")
    impago: str = Field(..., alias="Impago")
    prestamo_hipotecario: str = Field(..., alias="Prestamo hipotecario")
    prestamo_personal: str = Field(..., alias="Prestamo Personal")
    canal_contacto: str = Field(..., alias="Canal de contacto")
    mes: str = Field(..., alias="Mes")
    num_contactos_esta_campana: int = Field(..., alias="num contactos esta campaña")
    num_dias_ultimo_contacto: int = Field(..., alias="num días último contacto")
    num_contactos_otras_campanas: int = Field(..., alias="num contactos otras campañas")
    resultado_campana_anterior: str = Field(..., alias="resultado campaña anterior")
    variacion_tasa_empleo: float = Field(..., alias="variación tasa empleo")
    euribor3m: float = Field(..., alias="euribor3m")


# ── Contrato público de salida ─────────────────────────
class ScoringSalida(BaseModel):
    """Salida reducida operativa (el motor también calcula `percentil`)."""

    registro_id: int
    score_contratacion: float
    prediccion_binaria: int
    categoria: str
