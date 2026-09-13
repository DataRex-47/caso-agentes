# 🕒 Render Cron Job — Batch de Scoring (`Caso_Agentes`)

Guía para desplegar el proceso batch de scoring como **Cron Job** en Render.

---

## ⚠️ Aviso de coste y plan

- **Los Cron Jobs de Render requieren plan de pago** (no están en el plan free).
- El `cronSchedule` se interpreta en **UTC**.
- El disco del contenedor es **efímero**: todo lo que no se envíe a un destino externo se pierde al terminar la ejecución.

> 📌 Nota: el MCP Context7 no estaba disponible en esta sesión, por lo que este aviso se basa en el conocimiento vigente de Render y **debe revalidarse** en la documentación oficial antes de contratar.

---

## 1. Programación (`schedule`)

```
20 21 * * *      # todos los días a las 21:20 UTC
```

Convertido desde la hora local solicitada:

| Concepto | Valor |
|---|---|
| Hora local solicitada | 21:20 (Europe/Madrid) |
| Equivalencia UTC (CEST, verano = UTC+2) | 19:20 → `20 19 * * *` |
| Equivalencia UTC (CET, invierno = UTC+1) | 20:20 → `20 20 * * *` |

⚠️ Render **no aplica horario de verano**: si quieres que coincida con las 21:20 locales todo el año, tendrás que ajustar el cron en el cambio de hora, o dejar la hora UTC fija y asumir el desfase.

---

## 2. Comandos configurados

```yaml
buildCommand: pip install --upgrade pip && pip install -r 07_despliegue/deploy-ready/render-batch/requirements.txt
startCommand: bash 07_despliegue/deploy-ready/render-batch/start.sh
```

El `start.sh`:
1. Se posiciona en la raíz del repo (no depende de rutas locales del PC).
2. Descarga el CSV de entrada desde `INPUT_URL` (si no está definida, intenta el CSV del repo como respaldo).
3. Ejecuta `07_despliegue/02_produccion_scoring.py --input <tmp> --output <tmp>`.
4. Envía el CSV resultante por POST a `OUTPUT_WEBHOOK_URL` (si no está definida, solo lo deja en el contenedor y lo muestra por log).

---

## 3. Variables de entorno

| Variable | Obligatoria | Descripción |
|---|---|---|
| `INPUT_URL` | ✅ (Render) | URL del CSV de entrada. Sin ella, Render fallará salvo que el CSV esté en el repo. |
| `OUTPUT_WEBHOOK_URL` | ✅ (recomendado) | Endpoint que recibe el CSV de resultados por POST (multipart, campo `file`). Sin ella, el resultado se pierde (disco efímero). |
| `HTTP_TIMEOUT` | ❌ | Timeout HTTP en segundos (por defecto `60`). |
| `PYTHON_VERSION` | ❌ | Versión de Python (por defecto `3.12`, el repo ya incluye `.python-version`). |

> 🔐 Los secretos deben configurarse como variables de entorno en el dashboard (`sync: false`), nunca en el repositorio.

---

## 4. Checklist para el dashboard de Render

1. [ ] Subir el repositorio a GitHub (verifica que `07_despliegue/artefacto_pipeline.pkl` está **commiteado**; los `*.csv` están ignorados por `.gitignore`).
2. [ ] En Render: **New → Cron Job** (o **New → Blueprint** apuntando a `render.yaml`).
3. [ ] Runtime: **Python**. Plan: **Starter** o superior.
4. [ ] Build Command: `pip install --upgrade pip && pip install -r 07_despliegue/deploy-ready/render-batch/requirements.txt`
5. [ ] Start Command: `bash 07_despliegue/deploy-ready/render-batch/start.sh`
6. [ ] Schedule: `20 21 * * *` (UTC) — o `20 19 * * *` si quieres las 21:20 locales en verano.
7. [ ] Añadir `INPUT_URL` y `OUTPUT_WEBHOOK_URL` en **Environment**.
8. [ ] Ejecutar **Trigger Run** una vez y revisar los **Logs**.
9. [ ] Verificar que el webhook ha recibido el CSV `resultados.csv`.

---

## 5. Prueba local rápida de `start.sh` (Git Bash / WSL)

```bash
INPUT_URL="https://.../contratacion_fondos.csv" \
OUTPUT_WEBHOOK_URL="https://..." \
bash 07_despliegue/deploy-ready/render-batch/start.sh
```
