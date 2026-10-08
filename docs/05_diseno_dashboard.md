# Fases 5–7 — Diseño, construcción y validación del dashboard

_Proyecto final BI 2026-2 · Grupo 3 · Cadena nacional de supermercados_
_Estado: **primera versión funcional**. El diseño visual se ajustará en una iteración posterior._

## Cómo se construye

| Pieza | Herramienta | Archivo |
|---|---|---|
| Proyecto `.pbip` (formato TMDL + PBIR) | Power BI Desktop | `powerbi/ProyectoFinal.pbip` |
| Modelo: tablas, Power Query, relaciones, 23 medidas | Script | `scripts/pbip/generar_modelo_tmdl.py` |
| Páginas y visuales (75 objetos) | Script basado en la skill `pbi-report-builder` | `scripts/pbip/generar_reporte_pbir.py` |

Para regenerar: **cerrar Power BI Desktop**, ejecutar el script correspondiente y volver a abrir `ProyectoFinal.pbip`.
Los cambios hechos a mano en Desktop sobre las páginas generadas se pierden si se vuelve a ejecutar el script de reporte.

## Páginas

| Página | Pregunta | Contenido |
|---|---|---|
| 1. Resumen ejecutivo | ¿Cómo está el negocio y dónde mirar primero? | 5 KPI + ticket de referencia (gris), ventas enero–septiembre por año, estacionalidad mensual por año, crecimiento por región y por categoría, recuadro "Dónde mirar primero" |
| 2. Desempeño comercial (P1) | ¿Qué regiones, ciudades, formatos y categorías explican el resultado? | Matriz región → ciudad con crecimiento frente a 2025 y 2024 y su lectura; matriz región × formato con fondo semántico; categorías frente a dos años base; aporte en $ por ciudad |
| 3. Promociones, clientes y canales (P2) | ¿Qué palancas comerciales muestran oportunidades? | KPI (% de ventas en promoción, margen, unidades por línea), crecimiento por promoción, mezcla de canales por formato, canales frente a dos años base, fidelizados frente a no fidelizados, medio de pago |
| 4. Disponibilidad (P3) | ¿Dónde los quiebres requieren atención? | KPI de quiebre, % de quiebre mensual 2024–2026, volumen afectado por ciudad y por categoría, matriz categoría × formato |
| 5. Conclusiones | Síntesis y decisiones | 6 decisiones con su responsable (cumple la estructura mínima del PDF, punto 9) |
| Validación técnica (oculta) | ¿Cuadra con el CSV? | Tablas con las cifras de control |

## Color semántico

| Color | Significado | Dónde se ve |
|---|---|---|
| Azul `#1F3A5F` | Identidad y dato principal (2026, valores) | Encabezados, KPI, barras de volumen |
| Azul claro `#8FA8C8` / gris claro | Comparación (años anteriores, "vs hace 2 años") | Estacionalidad, barras de dos comparaciones |
| Verde `#2E7D32` | Crece de forma sostenida (frente a 2025 y 2024) | Barras y matrices de crecimiento (medida `Color Crecimiento`) |
| Rojo `#C62828` | Cae de forma sostenida | Ídem |
| Naranja `#EF8F00` | Advertencia: rebote u oscilación, quiebre de stock | Crecimiento que oscila, KPI % quiebre |
| Gris `#9E9E9E` | Estable, neutro o referencia | Crecimiento estable, ticket de referencia, fidelización |

El color de crecimiento **no es manual**: lo calcula la medida `Color Crecimiento` a partir de `Lectura Tendencia`. Por eso se mantiene coherente con cualquier filtro.

## Distribución (patrón F)

Todas las páginas siguen el mismo esquema de lectura de arriba hacia abajo y de izquierda a derecha:
1. Banda superior con el título (la pregunta de la página) y la navegación a la derecha.
2. Fila de segmentadores (Año, Región, Formato, Categoría).
3. Fila de KPI o de lectura del hallazgo.
4. Gráficos principales a la izquierda (lo más importante) y gráficos de detalle a la derecha y abajo.

## Interactividad

| Mecanismo | Propósito |
|---|---|
| Segmentador **Año** (selección única, 2026 por defecto) | Las medidas de crecimiento necesitan un solo año. Los gráficos de serie temporal (ventas por año, estacionalidad, quiebre mensual) **no** responden a este filtro para mostrar siempre la historia completa. |
| Segmentadores Región, Formato y Categoría | Enfocar el análisis en el ámbito de cada gerencia. Están sincronizados entre páginas (`syncGroup`). |
| Selección cruzada | Al hacer clic en una región o categoría se filtran los demás gráficos (ejemplo de la guía: Orinoquía). |
| Profundización en la matriz región → ciudad | Bajar de región a ciudad sin cambiar de página. |
| Tooltips | Las barras de crecimiento muestran la segunda comparación (vs hace 2 años) y la lectura de tendencia. |
| Navegador de páginas | Recorrer el dashboard en el orden P1 → P2 → P3 → conclusiones. |

## Validación técnica (Fase 7) — resultado

Se verificó en Power BI Desktop, en la página "Validación técnica", el 07/10/2026:

| Control | Esperado (CSV) | Power BI | ✓ |
|---|---|---|---|
| Ventas netas | 1.560.062.403 | $1.560.062.403 | ✅ |
| Costo / Margen / Margen % | 1.131.389.400 / 428.673.003 / 27,48 % | Iguales | ✅ |
| Líneas / Unidades | 60.000 / 121.393 | Iguales | ✅ |
| Líneas con quiebre / % / ventas con quiebre | 4.849 / 8,08 % / 126.858.302 | Iguales | ✅ |
| Ventas en promoción / % | 618.958.563 / 39,68 % | Iguales | ✅ |
| Venta por línea / Transacciones / Ticket | 26.001 / 21.264 / 73.366 | Iguales | ✅ |
| Ventas enero–septiembre 2024 / 2025 / 2026 | 425.113.135 / 424.805.507 / 428.753.035 | Iguales | ✅ |
| Crecimiento 2025 / 2026 | −0,07 % / +0,93 % | Iguales | ✅ |
| Ticket por región | Fijo en 73.366 | Fijo en las 7 regiones | ✅ |
| Tildes y decimales | "Bogotá D.C.", descuento 32,27 | Correctos | ✅ |

## Pendientes para la iteración de diseño

- La línea de % de quiebre debe salir en naranja (hoy sale en el azul por defecto) y su eje debería empezar en 0 % para no exagerar la variación.
- Las etiquetas del gráfico de ventas por año usan el formato "0,43 mil M"; conviene mostrarlas en "mill.".
- Tooltips personalizados (páginas de información sobre herramientas) para región y categoría.
- Afinar tamaños y espacios; revisar los textos truncados en la tarjeta del ticket.
