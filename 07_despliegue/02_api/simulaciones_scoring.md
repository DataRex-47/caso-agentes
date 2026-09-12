# ============================================================
# Simulación 1 — Perfil joven, alta interacción reciente
#
# Previsión scoring alto: ~0.63
#
# Señales a destacar:
# - campaña anterior = success
# - contacto muy reciente (num días último contacto = 5)
# - varios contactos en la campaña actual
# - perfil joven y formado
# - sin impagos ni préstamos activos
#
# Esta simulación valida que el modelo responde bien
# a señales claras de intención.
# ============================================================

{
  "Unnamed: 0": 101,
  "Edad": 29,
  "Trabajo": "technician",
  "Estado Civil": "single",
  "Fomación": "university.degree",
  "Impago": "no",
  "Prestamo hipotecario": "no",
  "Prestamo Personal": "no",
  "Canal de contacto": "cellular",
  "Mes": "may",
  "Dia de la semana": "thu",
  "num contactos esta campaña": 3,
  "num días último contacto": 5,
  "num contactos otras campañas": 2,
  "resultado campaña anterior": "success",
  "variación tasa empleo": -17,
  "euribor3m": 729
}


# ============================================================
# Simulación 2 — Perfil senior, contacto antiguo, poco engagement
#
# Previsión scoring bajo: ~0.04
#
# Señales a destacar:
# - num días último contacto = 999
# - resultado campaña anterior = nonexistent
# - solo 1 contacto
# - canal telephone
# - perfil retirado
#
# El modelo penaliza correctamente la falta de interacción.
# ============================================================

{
  "Unnamed: 0": 102,
  "Edad": 58,
  "Trabajo": "retired",
  "Estado Civil": "married",
  "Fomación": "basic.4y",
  "Impago": "unknown",
  "Prestamo hipotecario": "yes",
  "Prestamo Personal": "no",
  "Canal de contacto": "telephone",
  "Mes": "nov",
  "Dia de la semana": null,
  "num contactos esta campaña": 1,
  "num días último contacto": 999,
  "num contactos otras campañas": 0,
  "resultado campaña anterior": "nonexistent",
  "variación tasa empleo": -1,
  "euribor3m": 4021
}


# ============================================================
# Simulación 3 — Perfil profesional activo, zona gris
#
# Previsión scoring medio bajo: ~0.34
#
# Señales a destacar:
# - varios contactos
# - campaña previa = failure
# - préstamos activos
# - contexto macro intermedio
#
# Ejemplo típico de lead tibio.
# ============================================================

{
  "Unnamed: 0": 103,
  "Edad": 41,
  "Trabajo": "management",
  "Estado Civil": "divorced",
  "Fomación": "high.school",
  "Impago": "no",
  "Prestamo hipotecario": "yes",
  "Prestamo Personal": "yes",
  "Canal de contacto": "cellular",
  "Mes": "jul",
  "Dia de la semana": "mon",
  "num contactos esta campaña": 4,
  "num días último contacto": 20,
  "num contactos otras campañas": 1,
  "resultado campaña anterior": "failure",
  "variación tasa empleo": -12,
  "euribor3m": 2100
}


# ============================================================
# Simulación 4 — Perfil desempleado, contacto reciente
#
# Previsión scoring medio alto: ~0.47
#
# Señales negativas:
# - unemployed
# - Impago = yes
# - campaña previa = failure
# - contexto macro negativo
#
# Señales positivas:
# - contacto reciente
# - varios contactos previos
# - canal cellular
#
# El modelo prioriza la intención reciente sobre el perfil.
# ============================================================

{
  "Unnamed: 0": 104,
  "Edad": 35,
  "Trabajo": "unemployed",
  "Estado Civil": "single",
  "Fomación": null,
  "Impago": "yes",
  "Prestamo hipotecario": "no",
  "Prestamo Personal": "yes",
  "Canal de contacto": "cellular",
  "Mes": "mar",
  "Dia de la semana": "wed",
  "num contactos esta campaña": 2,
  "num días último contacto": 7,
  "num contactos otras campañas": 3,
  "resultado campaña anterior": "failure",
  "variación tasa empleo": -29,
  "euribor3m": 869
}
