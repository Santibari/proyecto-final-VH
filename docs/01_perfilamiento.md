# Fase 1 — Perfilamiento y entendimiento del dataset

_Proyecto final BI 2026-2 · Grupo 3 · Cadena nacional de supermercados_
_Fuente: `data/raw/03_cadena_supermercados.csv`. Todas las cifras se reproducen con `python scripts/validacion/01_perfilamiento.py`._
_Estado: **pendiente de validación por el equipo.**_

---

## 1. Resumen ejecutivo

| Aspecto | Resultado | Implicación |
|---|---|---|
| Origen | Dataset **sintético y anonimizado** de una cadena de supermercados simulada (según el enunciado oficial) | Explica patrones artificiales como el de `id_transaccion`. |
| Unidad de observación | **1 fila = 1 línea de venta** (`id_linea`, 60.000 únicos) | Es la granularidad de la tabla de hechos. |
| Completitud | 0 faltantes, 0 filas duplicadas, 0 días sin ventas en el rango. El enunciado anuncia faltantes intencionales, pero también se buscaron celdas vacías, textos centinela ("N/A", "NULL", "-", etc.) y espacios sobrantes, y hay 0. | No se requiere limpieza ni imputación. Queda documentado que se verificó. |
| Cobertura | 01/01/2024 – 30/09/2026 (33 meses, 1.004 días) | **2026 es parcial**: toda comparación anual se hace enero–septiembre vs enero–septiembre. |
| Consistencia interna | Jerarquía geográfica limpia; promoción ↔ descuento coherentes; costo < venta en el 100 % de las líneas | Los datos son confiables para medir ventas, margen estimado y quiebre. |
| **Problema principal** | `id_transaccion` **no representa una compra**: ninguno de los 16.852 IDs con varias líneas es consistente en fecha, ciudad, formato, canal ni medio de pago | Afecta los KPI "Transacciones" y "Ticket promedio" de la guía. **Decisión: solución mixta** (sección 5.1). |
| Señal analítica | Margen % y quiebre % casi idénticos entre grupos; las diferencias están en el **volumen y el crecimiento** | Hay que aplicar la regla de materialidad del plan. |

## 2. Diccionario de datos

| # | Columna | Tipo en Power BI | Descripción | Dominio / rango observado | Rol en el modelo | Observaciones |
|---|---|---|---|---|---|---|
| 1 | `id_linea` | Texto | Identificador único de la línea de venta | `SUP-000001`…`SUP-060000`; 60.000 únicos | Clave de `FactVentas` | Única y sin nulos. |
| 2 | `id_transaccion` | Texto | Según la guía, identificador de la compra | 21.264 distintos; 1 a 12 líneas por ID | Atributo de `FactVentas` (uso según la decisión 8.1) | **No es consistente** (sección 5). |
| 3 | `fecha` | Fecha | Día de la venta | 2024-01-01 a 2026-09-30 | Relación con `DimCalendario` | Formato ISO `yyyy-mm-dd`, sin hora. |
| 4 | `ciudad` | Texto | Ciudad de la tienda | 12 valores (Bogotá D.C. 24,1 % … Manizales 4,0 %) | `DimGeografia` (clave) | Cada ciudad tiene un solo departamento y una sola región. |
| 5 | `departamento` | Texto | Departamento | 12 valores (1:1 con ciudad) | `DimGeografia` | Redundante con la ciudad; sirve para el mapa. |
| 6 | `region` | Texto | Región comercial | 7: Centro, Caribe, Noroccidente, Nororiente, Suroccidente, Eje Cafetero, Orinoquía | `DimGeografia` | Noroccidente, Suroccidente y Orinoquía tienen **una sola ciudad** cada una. |
| 7 | `formato_tienda` | Texto | Tipo de tienda | Supermercado 47,7 %, Hipermercado 35,3 %, Express 17,0 % | `DimFormato` | No hay ID de tienda. Ciudad × formato da 36 combinaciones. |
| 8 | `categoria` | Texto | Categoría del producto | 8: Abarrotes 17,8 % … Panadería 10,3 % | `DimCategoria` | Es la dimensión con más variación en la venta por línea ($13 mil – $53 mil). |
| 9 | `producto_generico` | Texto | Referencia genérica | 6: "Referencia 01"…"06", repetidas en las 8 categorías (~16,7 % cada una) | **Excluida** | Anónima y uniforme: no permite identificar productos. |
| 10 | `unidades` | Número entero | Unidades de la línea | 1 a 6 (media 2,02) | Hecho | Total: 121.393. |
| 11 | `precio_unitario_cop` | Número entero | Precio unitario antes del descuento | $1.119 – $125.363 (mediana $10.662) | Hecho | Sin valores ≤ 0. |
| 12 | `promocion` | Texto | Tipo de promoción | Sin promoción 57,8 %, Descuento directo 20,2 %, Precio club 9,9 %, 2x1 6,1 %, Puntos dobles 6,0 % | `DimPromocion` | Etiqueta comercial. Su mecánica no se refleja en el descuento (sección 4). |
| 13 | `descuento_pct` | Número decimal | % de descuento aplicado | 0 a 32,27 (media 4,31; con promoción ≈ 10) | Hecho | **Usa punto decimal**: importar con configuración regional en-US. |
| 14 | `venta_neta_cop` | Número entero | Venta neta de la línea | $1.014 – $600.745; total **$1.560.062.403** | Hecho (medida base) | ≈ unidades × precio × (1 − descuento), con redondeo. |
| 15 | `costo_estimado_cop` | Número entero | Costo estimado | $669 – $380.892; total $1.131.389.400 | Hecho | Costo/venta entre 0,62 y 0,83. Siempre se habla de margen **estimado**. |
| 16 | `medio_pago` | Texto | Forma de pago | Débito 33,8 %, Crédito 27,0 %, Efectivo 25,0 %, Billetera digital 14,2 % | `DimMedioPago` o dimensión basura | — |
| 17 | `cliente_fidelizado` | Texto (Sí/No) | Marca de fidelización de la línea | Sí 59,2 %, No 40,8 % | `DimCondicionVenta` o atributo | No hay ID de cliente, **no se puede medir retención**. |
| 18 | `canal` | Texto | Canal de compra | Tienda física 82,1 %, Domicilio 11,9 %, Click & Collect 6,0 % | `DimCanal` o dimensión basura | — |
| 19 | `quiebre_stock_ult_7d` | Texto (Sí/No) → `quiebre_flag` 1/0 | Hubo quiebre de stock en los últimos 7 días | Sí 8,08 % (4.849 líneas) | Hecho (bandera) | Es un estado reciente. **No mide ventas perdidas.** |

## 3. Cobertura temporal

| Año | Líneas | Ventas netas | Meses | Ventas ene–sep |
|---|---|---|---|---|
| 2024 | 21.811 | $564.552.011 | 12 | $425.113.135 |
| 2025 | 21.854 | $566.757.357 | 12 | $424.805.507 |
| 2026 | 16.335 | $428.753.035 | **9** | $428.753.035 |

- Variación ene–sep 2025 vs 2024: **−0,07 %**. Variación ene–sep 2026 vs 2025: **+0,93 %**.
- Si se compara 2026 completo con 2025 completo, el resultado es −24,35 %. **Esa comparación es incorrecta** porque 2026 solo tiene 9 meses.
- El volumen es estable: entre 1.680 y 1.945 líneas por mes, sin días faltantes.

## 4. Reglas de consistencia verificadas

| Regla | Resultado | Conclusión |
|---|---|---|
| `id_linea` es única | 60.000 / 60.000 | ✅ |
| Sin faltantes ni duplicados | 0 / 0 | ✅ |
| Valores numéricos > 0 | 0 casos ≤ 0 | ✅ |
| Costo < venta | 60.000 / 60.000 | ✅ |
| Ciudad → un solo departamento → una sola región | 0 excepciones | ✅ La jerarquía es válida. |
| "Sin promoción" ⇔ descuento = 0 | 0 excepciones en ambos sentidos | ✅ |
| venta_neta = unidades × precio × (1 − desc/100) | 57.610 exactas (±2 COP); 2.390 con una diferencia de hasta 0,048 % | ✅ Es redondeo de origen. No se corrige. |
| El descuento depende del tipo de promoción | Todas las promociones tienen un descuento medio de ≈10 % (2x1 = 10,23 %) | ⚠️ La etiqueta no refleja la mecánica. Se usa como categoría y no se infiere que "2x1" sea un 50 %. |
| `id_transaccion` agrupa una sola compra | 0 de 16.852 IDs multilínea son consistentes | ❌ Ver sección 5. |

## 5. Prueba de `id_transaccion`

Si `id_transaccion` fuera una compra, todas sus líneas tendrían la misma fecha, ciudad, formato, canal, medio de pago y marca de fidelización. Resultado:

| Atributo | IDs multilínea con más de un valor |
|---|---|
| fecha | 16.847 de 16.852 |
| medio_pago | 14.853 |
| ciudad | 16.035 |
| formato_tienda | 13.646 |
| cliente_fidelizado | 11.809 |
| canal | 7.609 |
| **Totalmente consistentes** | **0** |

Entre la primera y la última línea de un mismo ID pasan **509 días en la mediana** (máximo 997). Ejemplo:

| id_linea | fecha | ciudad | formato | medio de pago | venta |
|---|---|---|---|---|---|
| SUP-035833 | 2024-09-29 | Santa Marta | Express | Crédito | $22.572 |
| SUP-000001 | 2025-04-14 | Pereira | Express | Débito | $9.060 |
| SUP-022980 | 2025-05-28 | Cali | Hipermercado | Crédito | $9.366 |
| SUP-002207 | 2026-07-14 | Barranquilla | Supermercado | Débito | $13.930 |

**No se puede reconstruir la compra:**
- Con `id_transaccion` + `fecha` salen 59.930 grupos, prácticamente uno por línea (solo 70 tendrían 2 líneas).
- Una clave con fecha + ciudad + formato + canal + medio de pago + fidelizado agrupa líneas que coinciden por azar, no compras reales. Usarla sería inventar datos.
- La correlación entre el número del ID y la fecha es 0,003: el ID se asignó al azar al generar el dataset sintético.

**El ticket por ID es incoherente al segmentarlo:**

| Región | Ticket por ID | Venta por línea |
|---|---|---|
| Centro | $37.188 | $25.980 |
| Caribe | $33.085 | $25.906 |
| Noroccidente | $30.923 | $26.010 |
| Eje Cafetero | $30.378 | $26.795 |
| Nororiente | $30.268 | $25.960 |
| Suroccidente | $29.525 | $25.493 |
| Orinoquía | $28.051 | $26.327 |
| **Total** | **$73.366** | **$26.001** |

Todas las regiones quedan por debajo del total, algo imposible con compras reales. La suma de "transacciones" por región da 48.106, contra 21.264 en el total.

### 5.1 Tratamiento adoptado: solución mixta

1. Los **KPI de análisis son por línea** (`Venta por Linea`, `Unidades por Linea`) y responden a todos los filtros.
2. **El ticket de la guía** ($73.366 = 1.560.062.403 / 21.264) se muestra en la página 1 solo como **referencia global**: tarjeta gris, fija con `REMOVEFILTERS()` y con un tooltip que explica la limitación.
3. Ningún gráfico segmenta Transacciones ni Ticket.
4. El caso se explica en el paso "Preparación de datos" de la sustentación.

Detalle completo y DAX: sección 8.1 del plan.

## 6. Riesgos y decisiones

| # | Riesgo | Tratamiento propuesto | ¿Quién decide? |
|---|---|---|---|
| R1 | `id_transaccion` no es una compra | **Solución mixta** (sección 5.1). La consulta al profesor es opcional. | Decidido por el equipo |
| R2 | 2026 es parcial | Calendario con `EsPeriodoComparable` (mes ≤ 9). YoY solo enero–septiembre. | Ya definido en el plan |
| R3 | Señal débil en tasas (margen 27,4–27,7 %; quiebre 7,6–8,8 %) | Regla de materialidad. Enfocar el análisis en participación, crecimiento y volumen afectado. | Ya definido en el plan |
| R4 | Tres regiones con una sola ciudad | Al profundizar región → ciudad, Noroccidente = Medellín, Suroccidente = Cali y Orinoquía = Villavicencio. Hay que mencionarlo al presentar. | Informativo |
| R5 | Mecánica de promociones no reflejada | Comparar promociones solo como categorías (participación, crecimiento, quiebre). | Informativo |
| R6 | Sin ID de cliente ni de tienda | No hablar de retención. "Punto de venta" = ciudad × formato, solo como supuesto explícito. | Informativo |

## 7. Validaciones que se deben ejecutar en Power BI (Fase 3)

**Importación (Power Query):**
- [ ] Origen: `data/raw/03_cadena_supermercados.csv`, **codificación 65001 (UTF-8)**, delimitador coma, encabezados promovidos.
- [ ] Tipos con **configuración regional en-US** ("Cambiar tipo → Usar configuración regional"), sobre todo `descuento_pct`.
- [ ] Tipos: `fecha` = Fecha; `unidades`, `precio_unitario_cop`, `venta_neta_cop`, `costo_estimado_cop` = Número entero; `descuento_pct` = Número decimal; el resto = Texto.
- [ ] `quiebre_flag` = `if [quiebre_stock_ult_7d] = "Sí" then 1 else 0` (Número entero).

**Cifras de control (deben coincidir exactamente):**

| Validación | Valor esperado |
|---|---|
| Filas de `FactVentas` | 60.000 |
| Suma `venta_neta_cop` | 1.560.062.403 |
| Suma `costo_estimado_cop` | 1.131.389.400 |
| Margen estimado | 428.673.003 (27,48 %) |
| Suma `unidades` | 121.393 |
| Suma `quiebre_flag` | 4.849 (8,08 %) |
| Líneas fidelizadas | 35.520 |
| Máximo `descuento_pct` | 32,27 (si aparece 3227, la configuración regional está mal) |
| Fecha mínima / máxima | 01/01/2024 / 30/09/2026 |
| Ventas ene–sep 2024 / 2025 / 2026 | 425.113.135 / 424.805.507 / 428.753.035 |
| Ciudades / regiones distintas | 12 / 7 |
| Texto con tildes | "Bogotá D.C.", "Medellín", "Orinoquía", "Lácteos" se ven correctamente |
| Tarjeta con el total de ventas con un segmentador de región | La suma de las 7 regiones = 1.560.062.403 (sin filas "en blanco") |
| `Transacciones (ID dataset)` / `Ticket Promedio (ID dataset)` | 21.264 / $73.366. El ticket **no debe cambiar** al seleccionar una región. |
| `Venta por Linea` total / Centro / Orinoquía | $26.001 / $25.980 / $26.327 |

## 8. Pendiente de validación del equipo

1. ¿Están de acuerdo con el diccionario y con excluir `producto_generico`?
2. ~~Decisión sobre `id_transaccion`~~ → **solución mixta** (sección 5.1).
3. ¿Confirman que se avanza a la **Fase 2 — Formulación del problema**?
