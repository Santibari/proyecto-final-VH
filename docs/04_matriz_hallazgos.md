# Fases 4 y 4.5 — Exploración y matriz de hallazgos validados

_Proyecto final BI 2026-2 · Grupo 3 · Cadena nacional de supermercados_
_Reproducible con `python scripts/validacion/04_validacion_hallazgos.py`._

## Criterios de validación

| Tipo de hallazgo | Criterio para aceptarlo |
|---|---|
| Crecimiento o caída | Ventas de enero–septiembre 2026 frente a **2025 y frente a 2024**. Es "tendencia" si la variación tiene el mismo signo y es mayor a ±2 % en ambas comparaciones. Si solo cambia frente a 2025, es "rebote" y **no** se presenta como tendencia. |
| Diferencias en tasas (quiebre, margen) | Prueba z de proporciones del grupo contra el resto, con **corrección de Bonferroni** según el número de comparaciones (k). Se acepta si p corregido < 0,05. |
| Materialidad | Diferencias de menos de 1 punto porcentual en tasas = "sin diferencia relevante". |

## Matriz de hallazgos

| # | Hallazgo | Evidencia (enero–septiembre) | Solidez | Decisión que apoya | ¿Entra al dashboard? | Visual recomendado |
|---|---|---|---|---|---|---|
| **HV1** | Las ventas totales están planas: el negocio no crece en conjunto | 2024: $425,1 M · 2025: $424,8 M · 2026: $428,8 M (+0,93 %) | Alta (dato total) | Contexto para priorizar | ✅ Página 1 | KPI + columnas por año |
| **HV2** | El crecimiento sostenido se concentra en **Eje Cafetero** (+8,3 % vs 2025; +2,5 % vs 2024) y **Orinoquía** (+12,0 %; +4,1 %). La caída sostenida está en **Nororiente** (−4,6 %; −2,6 %) | Por ciudad: Manizales (+13,4 %; +7,6 %) y Villavicencio crecen; Cartagena (−8,6 %; −4,9 %) y Bucaramanga (−4,0 %; −5,1 %) caen | Alta (signo consistente en ambas comparaciones) | D1, D2 | ✅ Página 2 | Barras de variación % por región/ciudad con color semántico |
| **HV3** | Combinaciones región × formato con caída sostenida: **Nororiente–Supermercado** (−12,4 %; −9,9 %), **Caribe–Express** (−12,4 %; −10,2 %), **Centro–Express** (−7,2 %; −12,0 %). Con crecimiento sostenido: **Eje Cafetero–Hipermercado** (+13,6 %; +10,3 %) y **Suroccidente–Supermercado** (+9,4 %; +16,0 %) | 500–2.240 líneas por celda en 2026 | Media-alta (consistente; n moderado) | D1, D2 | ✅ Página 2 | Matriz región × formato con formato condicional |
| **HV4** | **Abarrotes** es la única categoría con crecimiento sostenido (+9,1 %; +5,4 %) y el mayor aporte absoluto (+$5,7 M). Las demás están estables (±2 %) | — | Alta | D3 | ✅ Página 2 | Barras de variación por categoría |
| **HV5** | El margen estimado % es **igual** en todos los grupos (rango máximo 0,28 pp) | 27,4 %–27,7 % | Alta | Enfocar la gestión en volumen, no en margen | ✅ Página 3 (como "sin diferencia") | Tarjeta o texto + tooltip |
| **HV6** | **"Puntos dobles" cae de forma sostenida** (−7,1 %; −8,2 %). Las ventas "Sin promoción" crecen (+2,1 %; +2,5 %). Las ventas en promoción representan el 39,7 % | — | Media-alta (participación baja: 5,2 %) | D4 | ✅ Página 3 | Barras de variación por tipo de promoción |
| **HV7** | El quiebre (~8,1 %) es **parejo** en categorías, formatos y ciudades: **ninguna diferencia es significativa** tras la corrección (el mejor caso, Aseo hogar 8,8 %, tiene p corregido = 0,13). Es estable en el tiempo (7,9 % → 8,2 % → 7,9 %) | 4.849 líneas; $126,9 M de ventas en condición de quiebre | Alta (como hallazgo de ausencia de focos) | D6: **política de reposición para toda la cadena**, priorizada por **volumen afectado** (Bogotá: 1.192 líneas; Carnes: $26,5 M) | ✅ Página 4 | KPI % quiebre + barras de ventas con quiebre (volumen) + tendencia trimestral |

## Hallazgos descartados

| Candidato (Fase 2) | Motivo |
|---|---|
| H4: Domicilio es el canal de mayor crecimiento | Es un **rebote**: +6,1 % frente a 2025, pero +1,0 % frente a 2024 (en 2025 había caído −4,8 %). |
| Noroccidente / Caribe como crecimiento o caída | Oscilan: el signo cambia entre las dos comparaciones. |
| Focos de quiebre ciudad × categoría (p. ej. Pereira–Cuidado personal 11,6 %) | No son significativos con la corrección de Bonferroni (k = 96; p corregido = 1,0). |
| Diferencias por fidelización y medio de pago | Margen y venta por línea iguales. El crecimiento oscila. |

## Implicaciones para el diseño (Fase 5)

1. Los crecimientos se muestran con **las dos comparaciones** (frente a 2025 y frente a 2024), o con la serie de los 3 años, para no vender rebotes como tendencias.
2. Página 4: el mensaje no es "estas tiendas fallan", sino "el quiebre es estructural (~8 %) y estas son las zonas con más **volumen afectado**".
3. Página 3: se declara explícitamente que **el margen no varía**.
4. Se agrega la medida **Crecimiento vs 2024 %** para mostrar la segunda comparación.
