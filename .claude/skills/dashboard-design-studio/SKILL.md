---
name: dashboard-design-studio
description: "Dirección de arte para dashboards y portadas de Power BI: investiga referencias de diseño reales, define un concepto visual, construye la paleta con teoría del color (armonías, 60-30-10, contraste WCAG, daltonismo), elige el patrón de lectura (Z, F, Gutenberg, capas) y la retícula, produce 2–3 propuestas renderizadas y las califica con una rúbrica antes de construir. Úsala SIEMPRE que se pida diseñar, rediseñar o mejorar el aspecto de un dashboard, una página o una portada; cuando algo 'se ve feo', 'genérico' o 'poco profesional'; o cuando se mencione paleta, colores, tema, tipografía, layout, distribución, jerarquía visual, moodboard, referencias, inspiración, patrón Z/F, Gestalt o fondo de página. Se usa ANTES de pbi-report-builder: esta skill decide cómo se ve; pbi-report-builder lo escribe en el .pbip."
---

# Dashboard Design Studio

Dirección de arte para dashboards. Esta skill **no escribe el .pbip**: decide y justifica el diseño y entrega
un paquete listo para `pbi-report-builder` (posiciones, colores, tipografía, imagen de fondo).

> Regla de oro: **cada decisión visual debe poder justificarse** con una referencia, un principio o un dato
> del problema. "Se ve bonito" no es una justificación; "el verde se reserva para crecimiento sostenido porque
> la audiencia lo lee como 'bien' en < 1 s" sí lo es. Esto también sirve para la sustentación.

## Por qué existe (lección aprendida)

Una portada hecha "de memoria" salió genérica: panel azul + panel gris, círculos decorativos, un ícono de
carrito, una curva falsa y cuatro bloques de texto. Técnicamente correcta y visualmente olvidable. Las causas:
no hubo **investigación**, no hubo **concepto**, la paleta fue la de siempre y no se comparó con alternativas.
El flujo de abajo existe para que eso no se repita.

## Flujo obligatorio (no saltarse pasos)

### Paso 0 — Contexto (5 min)
Leer antes de diseñar: el problema y la audiencia (`docs/02_problema.md`), los hallazgos (`docs/04_*`),
el diseño actual (`docs/05_diseno_dashboard.md`), el tamaño de lienzo y la paleta semántica que ya usa el
script generador (`scripts/pbip/generar_reporte_pbir.py`). Anotar: audiencia, 3 mensajes clave, colores
semánticos ya comprometidos (no se pueden reasignar), restricciones técnicas.

### Paso 1 — Investigación de referencias → `references/investigacion.md`
- Buscar **mínimo 8 referencias reales** en al menos 3 tipos de fuente (galerías de BI, diseño editorial/
  periodismo de datos, diseño de producto/UI). Usar `WebSearch`, y para ver las imágenes la búsqueda de
  imágenes o el navegador. Nunca describir una referencia que no se ha visto.
- Llenar la **tabla de moodboard** (referencia → qué se toma: retícula, paleta, tipografía, elemento firma).
- Cerrar con 3–5 **patrones concretos** que se van a adoptar y 3 que se van a evitar.

### Paso 2 — Brief de diseño (concepto antes que píxeles)
Escribir en 6 líneas:
1. **Concepto / metáfora** ligada al dominio (p. ej. supermercado: tiquete de caja, góndola/estantería,
   etiqueta de precio, plano de pasillos). Un concepto da coherencia; la decoración sin concepto se ve genérica.
2. **Personalidad**: 3 adjetivos (p. ej. "editorial, sobrio, cálido").
3. **Patrón de lectura** por tipo de página → `references/composicion.md` (portada ≈ Z o póster centrado;
   página analítica ≈ F o capas; conclusiones ≈ Gutenberg).
4. **Jerarquía**: qué se ve en el 1.er segundo, en el 3.º y en el 10.º.
5. **Elemento firma**: lo único que hace reconocible el dashboard (un dato héroe, una tipografía, una forma).
6. **Qué NO va a tener**.

### Paso 3 — Sistema de color → `references/teoria-color.md`
- Elegir el **color de identidad** desde el concepto y la audiencia, no por costumbre (el azul marino es el
  default de todo el mundo: solo si hay una razón).
- Construir la armonía (análoga, complementaria dividida, etc.) y aplicar **60-30-10**.
- Respetar los **colores semánticos ya comprometidos** (verde/rojo/naranja/gris del proyecto): el color de
  identidad NO puede competir con ellos.
- Validar SIEMPRE con el script:
  ```bash
  python .claude/skills/dashboard-design-studio/scripts/paleta.py --fondo "#F7F4EE" \
      --texto "#1E2A2F" --colores "#0F5C4D,#E3A33B,#2E7D32,#C62828,#EF8F00,#9E9E9E"
  ```
  Debe pasar: contraste texto ≥ 4.5:1, gráficos ≥ 3:1, y colores categóricos distinguibles con
  deuteranopia/protanopia (ΔE ≥ 10 recomendado). Si no pasa, se corrige antes de seguir.

### Paso 4 — Retícula y tipografía → `references/composicion.md`
- Lienzo 1920×1080 (el del proyecto): retícula de 12 columnas, margen 64, medianil 24, múltiplos de 8 px.
- Escala tipográfica modular (razón 1.25–1.333). Máximo 2 familias y 3 pesos.
- Fuentes en visuales nativos: solo las que ofrece Power BI (Segoe UI, Segoe UI Light/Semibold/Bold, DIN,
  Georgia, etc.). Tipografías especiales **solo dentro de la imagen de fondo**.

### Paso 5 — 2 o 3 propuestas renderizadas
- Cada propuesta = un HTML a tamaño real del lienzo (1920×1080) con datos reales del proyecto (cifras de
  la validación técnica), con posicionamiento absoluto en píxeles. Todo lo que será visual nativo de Power BI
  lleva `data-pbi="NombreVisual"`; así el mismo HTML produce la imagen de fondo (`--sin-overlays`) y las
  posiciones para construir (`--posiciones`). Renderizar a PNG:
  ```bash
  python .claude/skills/dashboard-design-studio/scripts/render_mockup.py propuesta_a.html --grid --squint
  ```
  `--grid` superpone la retícula (verifica alineación); `--squint` genera la versión desenfocada para la
  prueba de entrecerrar los ojos (¿se lee la jerarquía sin leer el texto?).
- Las propuestas deben ser **realmente distintas** (concepto, paleta o composición), no variaciones de color.
- Mostrar las imágenes al usuario y pedir que elija o combine. No construir en Power BI sin esa elección.
- Para portadas, ver arquetipos y antipatrones en `references/portadas.md`.

### Paso 6 — Crítica con rúbrica → `references/rubrica.md`
Calificar la propuesta elegida (10 criterios, 1–5). **Mínimo 4 en todos y promedio ≥ 4.3** antes de pasar a
Power BI. Si no, iterar. Mostrar la tabla de calificación al usuario: es la evidencia de la decisión.

### Paso 7 — Entrega a `pbi-report-builder` → `references/implementacion-power-bi.md`
Entregar: imagen de fondo (solo formas, sin datos ni textos que se deban editar), lista de visuales con
posición x/y/ancho/alto alineada a la retícula, colores en hex por rol, tamaños de fuente en pt. Los datos
SIEMPRE son visuales nativos (nunca cifras "pintadas" en la imagen: se desactualizan y no se filtran).
Después de construir, comparar el resultado en Desktop con el mockup y corregir diferencias.

## Principios no negociables

1. **Datos primero, decoración al final.** Si un adorno no apoya el concepto o la lectura, se elimina.
2. **Un solo protagonista por pantalla.** Si todo es importante, nada lo es.
3. **El color significa algo.** Color de identidad para estructura; colores semánticos solo para estados.
4. **Espacio en blanco es diseño.** Mínimo 24 px entre bloques; agrupar por proximidad (Gestalt).
5. **Alinear todo a la retícula.** Un desalineado de 6 px se percibe como descuido.
6. **Accesible por defecto.** Contraste WCAG AA y nunca depender solo del color (agregar ícono, signo o texto).
7. **Coherencia entre páginas.** La portada introduce el sistema visual que el resto de páginas sigue.

## Archivos de la skill

| Archivo | Cuándo leerlo |
|---|---|
| `references/investigacion.md` | Paso 1: dónde buscar, consultas, plantilla de moodboard |
| `references/teoria-color.md` | Paso 3: armonías, 60-30-10, OKLCH, semántica, accesibilidad, paletas base |
| `references/composicion.md` | Pasos 2 y 4: patrones Z/F/Gutenberg/capas, Gestalt, retícula, tipografía, atributos preatentivos |
| `references/portadas.md` | Portadas y páginas de inicio: arquetipos, anatomía, antipatrones |
| `references/rubrica.md` | Paso 6: rúbrica de 10 criterios y pruebas rápidas |
| `references/implementacion-power-bi.md` | Paso 7: fondos, tema JSON, fuentes, trucos y límites de Power BI |
| `scripts/paleta.py` | Validar contraste, daltonismo y generar escalas tonales |
| `scripts/render_mockup.py` | Renderizar HTML → PNG con retícula y prueba de desenfoque |

## Relación con otras skills del repo

- `pbi-report-builder`: construye lo que esta skill diseña (páginas y visuales PBIR).
- `pbip-dependency-analyzer`: no interviene en el diseño.
- El plan del proyecto (`.claude/Plan_Implementacion_Claude_PowerBI_V3.md`) manda: diseño después de
  hallazgos validados; cada visual debe entenderse y poder explicarse en la sustentación.
