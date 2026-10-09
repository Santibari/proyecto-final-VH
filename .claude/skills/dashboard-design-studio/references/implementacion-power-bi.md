# Paso 7 — Llevar el diseño a Power BI (entrega a pbi-report-builder)

## División de trabajo: imagen de fondo vs. visuales nativos

| Va en la **imagen de fondo** (PNG 1920×1080) | Va como **visual nativo** |
|---|---|
| Formas, bandas, texturas, líneas, tiras de color | Toda cifra (tarjetas, gráficos, tablas) |
| Tipografía especial en textos que nunca cambian (opcional) | Títulos, subtítulos e integrantes (editables en Desktop) |
| Marcos de tarjetas con sombra/redondeo complejos | Segmentadores, navegación, botones con acción |

Nunca pintar datos en la imagen: no se filtran, no se actualizan y no se pueden defender en la sustentación.

**Flujo del fondo:** HTML del mockup → quitar textos y datos → `render_mockup.py fondo.html --sin-overlays` →
PNG → registrar como recurso (`StaticResources/RegisteredResources`) y usarlo en `page.json`
(`background.image`, `scaling: 'Fit'`). Ya hay un ejemplo funcional en `scripts/pbip/generar_reporte_pbir.py`
(función `registrar_imagen`). Con el lienzo 1920×1080 y la imagen al mismo tamaño, las coordenadas del mockup
son las mismas que las del visual.

## Fuentes disponibles en visuales nativos

Segoe UI, Segoe UI Light, Segoe UI Semibold, Segoe UI Bold, DIN, Arial, Arial Black, Calibri, Cambria,
Candara, Consolas, Constantia, Corbel, Courier New, Georgia, Lucida Sans Unicode, Tahoma, Times New Roman,
Trebuchet MS, Verdana, Wingdings. (Puede variar con la versión; revisar en Desktop.)
Combinaciones que funcionan: **DIN** (cifras y titulares, aire técnico) + **Segoe UI** (cuerpo);
**Georgia** (titulares editoriales) + **Segoe UI** (datos).

En textbox PBIR: `"textStyle": {"fontFamily": "DIN", "fontSize": "24pt", "fontWeight": "bold", "color": "#..."}`.

## Tema JSON (opcional, recomendado)

Un tema (`*.json` en `StaticResources/RegisteredResources`, registrado en `report.json` como
`"type": "CustomTheme"`) fija `dataColors`, `background`, `foreground`, `tableAccent` y `textClasses`
(`callout`, `title`, `header`, `label`). Hace que los visuales nuevos nazcan con la paleta correcta.
Orden de `dataColors`: primero identidad y comparación; los semánticos se aplican por medida
(`Color Crecimiento`), no por orden.

## Formato de visuales para que se vean "diseñados"

- Encabezado del visual: título con hallazgo, alineado a la izquierda, sin bordes; subtítulo en gris.
- Fondo del visual transparente cuando la tarjeta está en la imagen de fondo (alinear al píxel).
- Quitar: bordes por defecto, sombras, encabezado de visual (iconos al pasar el mouse) en portada.
- Tarjeta KPI: `cardVisual` (nueva) permite referencia y etiqueta; tamaño de valor 28–40 pt.
- Navegación: botones (`actionButton`) o formas con acción `PageNavigation`, con estados (predeterminado,
  al pasar, seleccionado) en la paleta; o `pageNavigator` con formato de colores del tema.
- Etiquetas de datos en vez de ejes cuando hay ≤ 12 barras.

## Paquete de entrega a `pbi-report-builder`

```
Página: pg00Portada (1920×1080)  Fondo: portada_fondo.png
| Visual | Tipo | x | y | w | h | Fuente / tamaño / color | Medida o texto |
| Titulo | textbox | 60 | 216 | 1192 | 260 | DIN 72 bold #1E2A2F | "Cadena nacional de supermercados" |
| Heroe  | cardVisual | 1324 | 216 | 584 | 200 | DIN 96 #0F5C4D | _Medidas[Crecimiento Ventas Ene-Sep %] |
...
Paleta: identidad #..., comparación #..., semánticos (sin cambios), fondo #..., texto #...
```

Después de construir: abrir en Desktop, tomar captura y compararla con el mockup aprobado. Corregir las
diferencias (desplazamientos, fuentes sustituidas, rellenos internos de los visuales ≈ 8–10 px).
