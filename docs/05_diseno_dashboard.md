# Fases 5–7 — Diseño, construcción y validación del dashboard

_Proyecto final BI 2026-2 · Grupo 3 · Cadena nacional de supermercados_
_Estado: **rediseño visual aplicado** (09/10/2026) con la skill `dashboard-design-studio`: dirección "tiquete + editorial"._

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
| 0. Portada | ¿De qué se trata y por dónde empiezo? | Titular, audiencia y datos; tiquete con las ventas ene–sep 2024–2026 y la variación (medida SVG Tiquete); índice navegable |
| 1. Resumen ejecutivo | ¿Cómo está el negocio y dónde mirar primero? | Titular dinámico, 5 KPI (con ticket de referencia ⓘ), podio top 3 de regiones, tabla de posiciones con puestos ganados/perdidos, estacionalidad mensual por año y crecimiento por categoría |
| 2. Desempeño comercial (P1) | ¿Qué regiones, ciudades, formatos y categorías explican el resultado? | Matriz región → ciudad con crecimiento frente a 2025 y 2024 y su lectura; matriz región × formato con fondo semántico; categorías frente a dos años base; aporte en $ por ciudad |
| 3. Promociones, clientes y canales (P2) | ¿Qué palancas comerciales muestran oportunidades? | KPI (% de ventas en promoción, margen, unidades por línea), crecimiento por promoción, mezcla de canales por formato, canales frente a dos años base, fidelizados frente a no fidelizados, medio de pago |
| 4. Disponibilidad (P3) | ¿Dónde los quiebres requieren atención? | KPI de quiebre, % de quiebre mensual 2024–2026, volumen afectado por ciudad y por categoría, matriz categoría × formato |
| 5. Conclusiones | Síntesis y decisiones | 6 decisiones con su responsable (cumple la estructura mínima del PDF, punto 9) |
| Validación técnica (oculta) | ¿Cuadra con el CSV? | Tablas con las cifras de control |

## Rediseño visual "tiquete + editorial"

Elegido entre 3 propuestas (A "El tiquete", B "La liga", C "Editorial"); el equipo pidió la mezcla A + C.

| Decisión | Qué se hizo | Por qué |
|---|---|---|
| Concepto | La portada es un **tiquete de caja**: las cifras ene–sep de 2024–2026 son los renglones, la variación es el "total" y el índice de páginas es navegable (Ctrl + clic). | Metáfora del dominio (supermercado) en lugar de decoración genérica. |
| Tipografía | Titulares en serif (Cambria), cifras en monoespaciada (Consolas, como una caja registradora), texto en Segoe UI. | Jerarquía clara: titular-hallazgo → cifra → detalle. |
| Fondo | Papel cálido `#F5F0E6` con reglas editoriales; tarjetas `#FFFDF8`. | Menos "plantilla corporativa"; el dato es la figura, el fondo no compite. |
| Retícula | 12 columnas (margen 60, medianil 24) en lienzo 1920 × 1080. | Alineación consistente entre páginas. |
| Podio top 3 | Medida **SVG Podio**: las 3 regiones con mayor crecimiento ene–sep, con medallas oro/plata/bronce y la comparación contra hace 2 años. Se anima al cargar o al filtrar. | Pedido del equipo; responde "¿dónde está el crecimiento?" en 1 segundo. |
| Tabla de posiciones | Medida **SVG Posiciones**: puesto actual, **puestos ganados o perdidos** frente al año anterior (▲▼) y barra de crecimiento con color semántico. | Muestra que el total plano esconde movimientos (Orinoquía ▲6). |
| KPI | Medida **SVG KPIs**: cifras con formato colombiano y nota de contexto (años anteriores, ticket de referencia ⓘ). | Formato independiente de la configuración regional del equipo. |
| Titular dinámico | Medida **SVG Titulo Resumen**: "El negocio está plano (+0,9 %), pero las regiones se mueven" y cambia con el año. | Titular = hallazgo, no tema. |

Las medidas SVG (carpeta `8. Diseño (SVG y textos)` de `_Medidas`) se generan en `scripts/pbip/medidas_diseno.py`
y se muestran con el **visual de imagen** (origen: "Seleccionar de los datos"). Responden a todos los segmentadores.

## Color semántico

Paleta validada con `.claude/skills/dashboard-design-studio/scripts/paleta.py` (contraste sobre el papel y daltonismo).

| Color | Significado | Dónde se ve |
|---|---|---|
| Azul petróleo `#0E4D64` | Identidad y dato principal (2026, valores) | Titulares, cifras, barras de volumen, línea 2026 |
| Gris azulado `#5E7F8C` / arena `#C9C2B3` | Comparación (2025 / 2024) | Estacionalidad, segunda comparación |
| Verde `#2E7D32` | Crece de forma sostenida (frente a 2025 y 2024) | Medida `Color Crecimiento`, tabla de posiciones, ▲ |
| Rojo `#C62828` | Cae de forma sostenida | Ídem, ▼ |
| Naranja `#B26A00` | Advertencia: rebote u oscilación, quiebre de stock | Crecimiento que oscila, % quiebre |
| Gris `#7D858C` | Estable, neutro o referencia | Crecimiento estable |
| Oro / plata / bronce | Puesto 1, 2 y 3 (solo en el podio y la tabla) | Medallas |

El naranja y el gris se oscurecieron frente a la primera versión (`#EF8F00` y `#9E9E9E` no llegaban a 3:1 sobre el fondo).
El verde y el rojo siempre van con signo (▲ ▼, + / −) para quien no distingue esos colores.

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

- ~~Línea de % de quiebre en naranja y eje desde 0 %~~ (resuelto en el rediseño).
- ~~Gráfico de ventas por año y tarjeta del ticket truncada~~ (reemplazados por la fila de KPI SVG).
- Tooltips personalizados (páginas de información sobre herramientas) para región y categoría.
- Las tarjetas de las páginas 3 y 4 muestran los decimales según la configuración regional del computador
  (punto o coma); las cifras SVG siempre usan formato colombiano.
- Reemplazar "Nombre 1 · Nombre 2 · Nombre 3" en la portada por los integrantes.
