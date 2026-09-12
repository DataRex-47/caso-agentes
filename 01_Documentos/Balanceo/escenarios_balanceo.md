# Escenarios de Balanceo Probados

- **Fecha**: 2026-09-02
- **Agente**: A_06_BalanceadorClases
- **Target**: `contrata_fondos` (clasificación binaria)
- **Dataset**: tablón completo `05_train_tablon_preseleccion.pkl` (28,015 filas)
- **Split interno**: 20% test, estratificado, `random_state=42`
- **Modelo**: regresión logística | **Métrica**: ROC AUC sobre test interno

## Tabla comparativa

| Escenario | n_train post-balanceo | % clase positiva train | AUC test |
|---|---|---|---|
| Sin balanceo | 22,412 | 11.54% | 0.7772 |
| RandomUnderSampler | 5,174 | 50.00% | 0.7755 |
| RandomOverSampler | 39,650 | 50.00% | 0.7754 |
| SMOTETomek | 38,684 | 50.00% | 0.7748 |

## Método finalmente elegido

**Ninguno (no balancear).** Los escenarios con balanceo no mejoraron el AUC
del escenario base; se descartan por pérdida de información (undersampling),
aumento de tamaño sin ganancia (oversampling) y complejidad adicional
(SMOTETomek).
