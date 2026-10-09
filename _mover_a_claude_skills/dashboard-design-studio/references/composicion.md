# Pasos 2 y 4 — Composición, patrones de lectura, retícula y tipografía

## 1. Patrones de lectura (elegir uno por tipo de página)

| Patrón | Cómo se mueve el ojo | Mejor para | Cómo aplicarlo |
|---|---|---|---|
| **Z** | Arriba izq → arriba der → diagonal → abajo izq → abajo der | Portadas, páginas con poco texto y un llamado a la acción | Identidad arriba izq, dato/contexto arriba der, mensaje en la diagonal, navegación abajo der |
| **F** | Barridos horizontales arriba, luego escaneo vertical por la izquierda | Páginas analíticas densas | KPI en la fila superior, lo más importante a la izquierda, títulos que empiecen por la palabra clave |
| **Gutenberg** (diagrama de 4 cuadrantes) | Área óptima arriba izq → área terminal abajo der; las otras dos esquinas son "zonas muertas" | Páginas de conclusiones y decisiones | Tesis arriba izq, decisión/acción abajo der |
| **Capas (layer cake)** | Escaneo de títulos horizontales, uno por banda | Páginas con secciones claras (P1, P2, P3) | Cada banda = una pregunta con su titular-hallazgo |
| **Póster / centro** | Al elemento más grande, luego alrededor | Portadas con un dato héroe o un titular fuerte | Un solo foco enorme, todo lo demás pequeño y periférico |
| **Puntos (spotted)** | Salta entre elementos de alto contraste | Evitarlo: aparece cuando no hay jerarquía | Si el ojo "salta", falta un protagonista |

Ir más allá de Z/F: el patrón solo dice **dónde** poner cosas. La **jerarquía** decide qué gana:
tamaño > contraste de luminosidad > color saturado > posición > peso tipográfico.

## 2. Jerarquía en 3 niveles (prueba 1-3-10)

- **1 s**: un solo elemento (titular, dato héroe o el gráfico principal).
- **3 s**: 2–4 elementos de apoyo (KPI, subtítulo, leyenda de color).
- **10 s**: el resto (detalle, notas, navegación).

Proporción de tamaños orientativa: dato héroe 5–8× el texto de cuerpo; título de página 2–2.5×.

## 3. Gestalt aplicado

| Principio | Aplicación |
|---|---|
| Proximidad | Lo relacionado junto (≤ 16 px), grupos distintos separados (≥ 32 px). Más fuerte que los bordes. |
| Similitud | Mismo tipo de dato = mismo estilo (todas las tarjetas KPI iguales). |
| Región común | Una superficie (tarjeta/banda) agrupa; usar pocas y sutiles. |
| Continuidad / alineación | Bordes alineados crean líneas invisibles que ordenan la página. |
| Figura-fondo | El dato es figura; la decoración siempre es fondo (baja saturación, bajo contraste). |
| Cierre | No hace falta encerrar todo en cajas: el espacio en blanco ya delimita. |

## 4. Atributos preatentivos (lo que se ve sin pensar, < 250 ms)

Color (tono/intensidad), tamaño, posición, orientación, forma, encerramiento, movimiento. Usar **uno** para el
mensaje principal: si todo está resaltado, nada lo está.

## 5. Retícula para lienzo 1920 × 1080

- **Retícula del proyecto: 12 columnas, margen 60, medianil 24, columna 128**
  (`2·60 + 12·128 + 11·24 = 1920`). Inicio de la columna n (0-index): `x = 60 + n·152`.
  Ancho de k columnas: `k·128 + (k−1)·24`.
- Ritmo vertical en múltiplos de 8 px. Bandas: encabezado 96, filtros 64, KPI 128–144.
- Anchos útiles: 3 col = 432 · 4 col = 584 · 6 col = 888 · 8 col = 1192 · 12 col = 1800.
- Todo visual empieza y termina en borde de columna. Verificar con `render_mockup.py --grid`.

## 6. Tipografía

- Escala modular razón 1.25 (base 12 pt): 12 · 15 · 19 · 24 · 30 · 37 · 47 · 58 pt.
- Máximo 2 familias, 3 pesos. Titulares en peso alto, cuerpo regular, notas en gris (no en tamaño minúsculo).
- Interlineado 1.2 en titulares, 1.4–1.5 en cuerpo. Longitud de línea 45–90 caracteres.
- Números: cifras tabulares si se comparan en columna; separadores locales (es-CO: `1.560.062.403`, `27,48 %`).
- Titulares = **hallazgo**, no tema: "Abarrotes es la única categoría que crece" > "Ventas por categoría".
- En visuales nativos de Power BI solo hay fuentes del sistema (ver `implementacion-power-bi.md`).
  Tipografías con más carácter van dentro de la imagen de fondo y solo para textos que no cambian.

## 7. Espacio en blanco y densidad

- Densidad objetivo de una página analítica: 6–9 visuales. Más de 12 es un informe, no un dashboard.
- Portada: 3–6 elementos en total.
- Espacio entre bloques ≥ 24 px; alrededor del dato héroe ≥ 48 px.

## 8. Tinta de datos (Tufte) y limpieza

Quitar: bordes de gráfico, líneas de cuadrícula fuertes, leyendas redundantes (etiquetar la serie directamente),
ejes cuando hay etiquetas de dato, títulos de eje obvios, 3D, sombras, degradados en barras.
