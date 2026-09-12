# Diseño de Transformaciones — Proyecto Contratación de Fondos

**Estado**: ✅ **CONGELADO** (2026-09-02, aprobado por el usuario — opciones recomendadas A/B/C/D/E)

**Fecha**: 2026-09-02
**Objetivo del proyecto**: Clasificación binaria — scoring de probabilidad de contratación de fondos.
**Target**: `contrata_fondos` (1 = contrata, 0 = no; 11.54% positivos)
**Modelos priorizados**: Se probarán distintos (árboles, lineales, etc.). El tablón final será único y **compatible con ambos**: el escalado es una transformación monótona que no perjudica a los árboles y es imprescindible para modelos sensibles a escala.

---

## Tabla de diseño de transformaciones

La matriz sigue un enfoque de **pipeline secuencial en fases** donde cada variable puede pasar por transformaciones sucesivas que cambian su tipo y escala.

**Fases**: FASE 1 (genera features numéricas a escalar) → FASE 2 (genera features binarias / no escalables) → FASE 3 (escalado selectivo de numéricas continuas) → FASE 4 (unión).

| Variable | Tipo_Original | Transformación_1 | Tipo_Resultado_1 | Transformación_2 | Tipo_Resultado_2 | Escalado_Final | Es_Final | Incluir_DF | Nombre_Col_Final | Justificación |
|----------|---------------|------------------|------------------|------------------|------------------|----------------|----------|------------|------------------|---------------|
| **contrata_fondos** | binaria | — | — | — | — | NO | SÍ | SÍ | contrata_fondos | Target, sin transformar |
| trabajo | cat_nominal | OHE (drop='first') | binarias | — | — | NO | SÍ | SÍ | trabajo_* (11 cols) | 12 categorías; 'unknown' se conserva como categoría propia (no se imputa ni se pierde señal) |
| estado_civil | cat_nominal | OHE (drop='first') | binarias | — | — | NO | SÍ | SÍ | estado_civil_* (3 cols) | Ídem |
| impago | cat_nominal | OHE (drop='first') | binarias | — | — | NO | SÍ | SÍ | impago_* (2 cols) | Binaria con 'unknown' (no=ref.) |
| prestamo_hipotecario | cat_nominal | OHE (drop='first') | binarias | — | — | NO | SÍ | SÍ | prestamo_hipotecario_* (2 cols) | Binaria con 'unknown' |
| prestamo_personal | cat_nominal | OHE (drop='first') | binarias | — | — | NO | SÍ | SÍ | prestamo_personal_* (2 cols) | Binaria con 'unknown' |
| canal_de_contacto | cat_nominal (binaria) | OHE (drop='first') | binaria | — | — | NO | SÍ | SÍ | canal_de_contacto_telephone (1 col) | Solo 2 categorías → 1 dummy |
| formacion | cat_ordinal | Ordinal Encoding (orden educativo, 'unknown'→NaN) | num_ordinal (con NaN) | Imputación mediana | num_continua | StandardScaler | SÍ | SÍ | formacion_oe_imp_ss | Orden natural de estudios; 'unknown' imputado a la mediana ordinal (posición neutra) |
| mes | cat_ordinal (cíclica) | sin/cos (ciclo 12 meses) | num_continua [-1,1] | — | — | NO | SÍ | SÍ | mes_sin, mes_cos | Estacionalidad sin imponer orden lineal 1..12; ya normalizada |
| resultado_campana_anterior | cat_ordinal (con 'nonexistent') | OHE (drop='first') | binarias | — | — | NO | SÍ | SÍ | resultado_campana_anterior_* (2 cols) | 'nonexistent' ≠ intermedio ordinal (no estaba en campaña previa) → mejor como dummy |
| edad | num_discreta | — | num_continua | — | — | StandardScaler | SÍ | SÍ | edad_ss | Asimetría moderada (+0.83) no requiere log |
| num_contactos_esta_campana | num_discreta | log1p | num_continua | — | — | StandardScaler | SÍ | SÍ | num_contactos_esta_campana_log_ss | Cola larga (skew +4.77); log1p maneja el 0 |
| num_contactos_otras_campanas | num_discreta | log1p | num_continua | — | — | StandardScaler | SÍ | SÍ | num_contactos_otras_campanas_log_ss | Cola larga (skew +3.77); log1p maneja el 0 |
| variacion_tasa_empleo | num_continua | — | num_continua | — | — | StandardScaler | SÍ | SÍ | variacion_tasa_empleo_ss | Casi simétrica (-0.71); escalado directo |
| euribor3m | num_continua | — | num_continua | — | — | StandardScaler | SÍ | SÍ | euribor3m_ss | Cuasi-continua (311 valores); escalado directo |
| num_dias_ultimo_contacto | num_discreta | flag (≥0 → 1) | binaria | — | — | NO | SÍ | SÍ | contactado_previamente | Rama 1: separa "no contactado antes" (−1) del resto. No se escala |
| num_dias_ultimo_contacto | num_discreta | −1 → NaN | num_continua (con NaN) | Imputación mediana | num_continua | StandardScaler | SÍ | SÍ | num_dias_ultimo_contacto_imp_ss | Rama 2: días reales entre contactados, sin el −1 sentinel |

---

## Decisiones tomadas

### Decisión 1 — Tratamiento del valor 'unknown' en categóricas nominales
- **CONFIRMADA**: en `trabajo`, `estado_civil`, `impago`, `prestamo_hipotecario`, `prestamo_personal` se **conserva 'unknown' como categoría propia** dentro del OHE (no se imputa).
- **Justificación**: la fase de calidad mantuvo `unknown` como categoría; imputar inventaría información. El modelo puede aprender si "no informado" es informativo.

### Decisión 2 — Tipo de encoding para `formacion`
- **CONFIRMADA — Opción A**: Ordinal Encoding con orden educativo real (`illiterate < basic.4y < basic.6y < basic.9y < high.school < professional.course < university.degree`). El valor `unknown` se convierte en NaN durante el encoding y se imputa con la **mediana ordinal** (posición central neutra) antes de escalar con StandardScaler.
- Feature final: `formacion_oe_imp_ss`.

### Decisión 3 — Codificación de `mes`
- **CONFIRMADA**: features **cíclicas seno/coseno** (`mes_sin`, `mes_cos`) sobre ciclo de 12 meses. Ya están en [-1,1] y **no se escalan**.

### Decisión 4 — Codificación de `resultado_campana_anterior`
- **CONFIRMADA**: OHE con drop='first' → 2 dummies. `nonexistent` no se trata como nivel intermedio ordinal porque significa "sin campaña anterior".

### Decisión 5 — `num_dias_ultimo_contacto` (valor −1 = no contactado previamente)
- **CONFIRMADA — Opción A** con 2 ramas:
  - Rama 1 (binaria, FASE 2, no escalar): flag `contactado_previamente` (1 si días ≥ 0).
  - Rama 2 (numérica, FASE 1 + FASE 3): los −1 pasan a NaN y se imputan con la **mediana**; luego StandardScaler. Feature final: `num_dias_ultimo_contacto_imp_ss`.

### Decisión 6 — Escalado global
- **CONFIRMADA**: las features numéricas continuas de FASE 1 se escalan con **StandardScaler** (FASE 3). No se escalan: binarias (OHE/flags), cíclicas (sin/cos) ni la target.

### Decisión 7 — Política de columnas intermedias y originales
- **CONFIRMADA**: en el df final **solo** entran las versiones finales (escaladas o binarias) + target. Las columnas originales e intermedias (ej. `formacion_oe` sin escalar, `num_dias_ultimo_contacto` original, `edad` original, etc.) quedan **excluidas**.

---

## Riesgos identificados

- **Dimensionalidad**: el OHE de `trabajo` (12 cat) añade 11 dummies; el total del tablón rondará ~35-40 columnas. Aceptable con 28.015 filas.
- **Imputación de `unknown` en `formacion`** (confirmada, opción A): la mediana ordinal puede desplazar ligeramente la distribución; se verificará la frecuencia de `unknown` en la ejecución.
- **Fuga de datos / overfitting**: se descarta Target Encoding (riesgo de fuga y sobreajuste para un objetivo de scoring con probabilidad bien calibrada).
- **Variables de contexto macro** (`variacion_tasa_empleo`, `euribor3m`): valores casi constantes por campaña/mes; pueden ser casi colineales con `mes` — se valorará en modelización, no aquí.
- **Ramas de `num_dias_ultimo_contacto`**: flag + columna imputada no son colineales entre sí (la columna imputada conserva información de días de los contactados; el flag separa grupos).

---

## Notas de implementación (pipeline)

- **FASE 1** (features numéricas a escalar):
  - `formacion` → Ordinal Encoding (orden educativo, `unknown`→NaN) → imputación mediana → feature `formacion_oe_imp`.
  - `num_dias_ultimo_contacto` → −1→NaN → imputación mediana → feature `num_dias_ultimo_contacto_imp`.
  - `num_contactos_esta_campana` → log1p → `num_contactos_esta_campana_log`.
  - `num_contactos_otras_campanas` → log1p → `num_contactos_otras_campanas_log`.
  - `edad`, `variacion_tasa_empleo`, `euribor3m` → se conservan tal cual (paso directo a FASE 3).
- **FASE 2** (binarias / no escalables): dummies OHE de `trabajo`, `estado_civil`, `impago`, `prestamo_hipotecario`, `prestamo_personal`, `canal_de_contacto`, `resultado_campana_anterior` (todas con `drop='first'`); flag `contactado_previamente`; features cíclicas `mes_sin` y `mes_cos`.
- **FASE 3** (escalado selectivo): **StandardScaler** únicamente sobre las features numéricas de FASE 1 (`formacion_oe_imp`, `num_dias_ultimo_contacto_imp`, contactos log1p, `edad`, `variacion_tasa_empleo`, `euribor3m`) → sufijos `_ss`.
- **FASE 4**: unión de versiones finales + target `contrata_fondos`. Se excluyen las columnas originales e intermedias transformadas.
