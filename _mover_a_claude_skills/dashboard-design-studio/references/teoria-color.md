# Paso 3 — Teoría del color aplicada a dashboards

## 1. Roles antes que colores

Todo color del dashboard tiene **un rol**. Si un color no tiene rol, sobra.

| Rol | Cantidad | Uso | Ejemplo en este proyecto |
|---|---|---|---|
| Fondo | 1–2 | Lienzo y superficies (tarjetas) | Blanco hueso / gris muy claro |
| Texto | 2–3 | Principal, secundario, deshabilitado | Casi negro, gris medio |
| Identidad (acento estructural) | 1 (+ su escala tonal) | Títulos, encabezados, dato principal, marca | Lo define el concepto |
| Comparación | 1–2 | Años anteriores, referencia | Tonos claros de la identidad o grises |
| Semánticos | 3–4 | Estados: bien / mal / advertencia / neutro | Verde `#2E7D32`, rojo `#C62828`, naranja `#EF8F00`, gris `#9E9E9E` (ya comprometidos) |
| Categóricos | ≤ 6–8 | Series nominales (canal, formato) | Paleta accesible |

**Regla del proyecto:** los semánticos ya están comprometidos en `docs/05_diseno_dashboard.md` y en la medida
`Color Crecimiento`. El color de identidad **no puede** ser verde, rojo ni naranja saturado, porque competiría
con el significado. Probar familias: azul petróleo/teal, índigo, ciruela, terracota apagado, verde oliva muy
oscuro (solo si se distingue claramente del verde semántico).

**Diagnóstico de la paleta actual** (`paleta.py` sobre el fondo `#F4F6F9`): azul `#1F3A5F`, verde y rojo pasan;
azul claro `#8FA8C8` (2,3:1), naranja `#EF8F00` (2,3:1) y gris `#9E9E9E` (2,5:1) **no llegan a 3:1**. Opciones:
mantenerlos como relleno de barras grandes siempre acompañados de etiqueta de dato, y usar variantes oscuras
cuando sean **líneas finas o texto** (verificado: naranja `#B26A00` 3,9:1 y azul de comparación `#5F7FA6`
3,8:1 sirven para líneas y texto grande/negrita; gris `#6E6E6E` 4,7:1 sirve también para texto normal). Cambiar un semántico implica actualizar la medida `Color Crecimiento` y el doc 05.

## 2. Armonías (rueda cromática)

| Armonía | Cómo | Carácter | Cuándo usar en un dashboard |
|---|---|---|---|
| Monocromática | Un tono, varias luminosidades | Sobria, muy limpia | Base para casi todo dashboard; acentos solo semánticos |
| Análoga | Tonos vecinos (±30°) | Armónica, tranquila | Identidad + comparación |
| Complementaria | Tonos opuestos (180°) | Contraste fuerte | Un único acento puntual (p. ej. dato héroe) |
| Complementaria dividida | Base + los 2 vecinos del opuesto | Contraste con menos tensión | Portadas con carácter |
| Triádica | 3 tonos a 120° | Vibrante | Difícil en BI: solo con baja saturación |

Recomendación práctica: **monocromática/análoga para estructura + semánticos para estados + 1 acento
complementario como máximo** (para el elemento firma).

## 3. Regla 60-30-10

- **60 %** color dominante neutro (fondos y superficies).
- **30 %** color secundario (identidad en encabezados, bandas, barras principales).
- **10 %** acento (lo que debe mirarse primero: dato héroe, alerta, llamado a la acción).

En pantallas analíticas el reparto real suele ser 80-15-5: más neutro, porque los gráficos ya aportan color.

## 4. Luminosidad > tono (usar OKLCH)

El ojo ordena por **luminosidad**. Una escala tonal útil varía L de forma pareja y baja un poco el croma en los
extremos. Trabajar en **OKLCH** (perceptualmente uniforme) en lugar de HSL: dos colores con la misma L en OKLCH
se ven igual de claros; en HSL no.

Generar la escala de la identidad con:
```bash
python scripts/paleta.py --escala "#0F5C4D"
```
Usos típicos de la escala: 95 % fondos de tarjeta suaves · 85 % comparación · 55–65 % barras · 30–40 % títulos y
dato principal · 20 % texto sobre claro.

## 5. Accesibilidad (obligatoria)

| Elemento | Contraste mínimo (WCAG 2.x AA) |
|---|---|
| Texto normal (< 18 pt) | 4.5 : 1 |
| Texto grande (≥ 18 pt o ≥ 14 pt negrita) | 3 : 1 |
| Elementos gráficos (barras, líneas, íconos) | 3 : 1 contra el fondo adyacente |

Daltonismo: ~8 % de los hombres tiene deficiencia rojo-verde. El par verde/rojo del proyecto debe
acompañarse SIEMPRE de signo o forma (▲ ▼, "+"/"−", etiqueta de texto). `paleta.py` simula deuteranopia,
protanopia y tritanopia y reporta los pares que se confunden (ΔE < 10).

## 6. Psicología y cultura del color (usar con cuidado)

| Familia | Asociaciones frecuentes | Riesgo en dashboards |
|---|---|---|
| Azul | Confianza, institucional, calma | Genérico: es el default de todo |
| Teal / petróleo | Frescura, salud, modernidad | Puede confundirse con verde semántico si es claro |
| Verde | Crecimiento, bien, fresco/alimentos | Ya es semántico ("sube") |
| Rojo | Alerta, pérdida, urgencia; en retail: ofertas | Ya es semántico ("cae") |
| Naranja/ámbar | Energía, advertencia, precio/oferta | Ya es semántico ("advertencia") |
| Terracota/arena | Cálido, natural, mercado | Bajo contraste si es claro |
| Morado/ciruela | Premium, analítico | Poco asociado a retail masivo |
| Gris | Neutro, contexto | Ideal para "todo lo que no es el mensaje" |

Para retail/supermercado funcionan bien los neutros cálidos (papel, kraft, crema) con una identidad oscura
profunda y acentos reservados a los estados.

## 7. Paletas base accesibles

- **Okabe-Ito** (categórica, segura para daltonismo): `#E69F00 #56B4E9 #009E73 #F0E442 #0072B2 #D55E00 #CC79A7 #000000`.
- **ColorBrewer**: secuenciales (`Blues`, `YlGnBu`) y divergentes (`RdBu`, `BrBG`) para mapas de calor.
- **Gris + 1 acento** (Storytelling with Data): todo gris `#BFBFBF`/`#7F7F7F` y solo la serie del mensaje en color.

## 8. Fondos

- Evitar blanco puro + negro puro (vibración): usar blanco roto (`#FAFAF7`, `#F7F4EE`) y texto casi negro
  (`#1E2A2F`, `#222`).
- Modo oscuro solo si hay razón (sala de control, proyección). En proyector, el claro suele leerse mejor.
- Las tarjetas se separan del fondo por **diferencia de luminosidad pequeña** (2–4 % en L) o un borde de 1 px;
  sombras fuertes envejecen el diseño.
