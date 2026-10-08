# Fase 2 — Formulación del problema de negocio

_Proyecto final BI 2026-2 · Grupo 3 · Cadena nacional de supermercados_
_Responde las 8 preguntas orientadoras del enunciado (sección 11) y los requisitos de la sección 7 (audiencia, problema, ≥ 3 KPI y decisiones)._
_La evidencia preliminar se reproduce con `python scripts/validacion/02_evidencia_problema.py` (periodo comparable enero–septiembre)._
_Estado: **pendiente de validación por el equipo.**_

---

## 1. Problema de negocio (en una frase)

> **La gerencia de tiendas y de categoría necesita saber en qué regiones, formatos y categorías se está concentrando el crecimiento o la caída de las ventas, y dónde la disponibilidad de inventario pone en riesgo el desempeño, para priorizar su esfuerzo comercial y operativo.**

**Pregunta central** (de la guía): ¿Qué regiones, formatos y categorías presentan las principales oportunidades de crecimiento y qué factores comerciales u operativos deberían priorizarse?

**Por qué es un problema relevante:** las ventas totales están planas (+0,93 % en enero–septiembre 2026 frente a 2025, y −0,07 % en 2025 frente a 2024). Ese total oculta movimientos opuestos por dentro: unas regiones y categorías crecen y otras caen. Si la gerencia solo mira el total, no ve dónde actuar.

## 2. Audiencia

| Rol | Qué necesita ver | Nivel de detalle |
|---|---|---|
| **Gerencia de tiendas** (audiencia principal) | Desempeño por región, ciudad y formato. Focos de quiebre por punto de venta (ciudad × formato). | Región → ciudad → formato |
| **Gerencia de categoría** (audiencia principal) | Crecimiento y participación de cada categoría. Quiebre por categoría. Uso de promociones. | Categoría → formato / ciudad |

Las dos comparten la página de resumen y luego profundizan por su eje: geografía y formato para la gerencia de tiendas, categoría para la gerencia de categoría.

## 3. Decisiones que la audiencia puede tomar con el dashboard

| # | Decisión | Quién la toma | Pregunta que la apoya |
|---|---|---|---|
| D1 | Priorizar regiones, ciudades o formatos que caen para hacer planes de recuperación (por ejemplo, Nororiente y Caribe) | Gerencia de tiendas | P1 |
| D2 | Reforzar o replicar lo que funciona donde hay crecimiento (por ejemplo, Eje Cafetero y Orinoquía) | Gerencia de tiendas | P1 |
| D3 | Revisar el surtido, el espacio o la exhibición de las categorías que pierden participación | Gerencia de categoría | P1, P2 |
| D4 | Reasignar la inversión promocional entre tipos de promoción y categorías | Gerencia de categoría | P2 |
| D5 | Impulsar canales con crecimiento (Domicilio, Click & Collect) en los formatos donde crecen | Gerencia de tiendas | P2 |
| D6 | Priorizar la reposición de inventario en las combinaciones categoría × formato × ciudad con más quiebre | Ambas (operaciones) | P3 |

Todas son decisiones de **priorización** (dónde mirar primero). El dataset no permite demostrar causas, así que el dashboard señala dónde actuar, no por qué ocurre algo.

## 4. Las tres preguntas analíticas

### P1. ¿Cómo evoluciona el desempeño comercial y dónde se concentra el crecimiento o la caída?
- **Subpreguntas:** ¿cómo evolucionan las ventas mes a mes y año contra año (enero–septiembre)? ¿Qué regiones, ciudades, formatos y categorías explican la variación?
- **Evidencia preliminar (enero–septiembre 2026 vs 2025):**

| Crecen | Caen |
|---|---|
| Orinoquía +12,0 %, Eje Cafetero +8,3 %, Noroccidente +4,5 % | Nororiente −4,6 %, Caribe −2,6 % |
| Manizales +13,4 %, Villavicencio +12,0 % | Cartagena −8,6 %, Cúcuta −5,4 %, Bucaramanga −4,0 % |
| Abarrotes +9,1 % (+$5,7 M, el mayor aporte absoluto) | Cuidado personal −1,6 %, Aseo hogar −1,5 % |
| Hipermercado +1,9 % | Express −0,6 % |

  Cruce región × formato: hay contrastes fuertes. Express crece +28 % en Orinoquía y +21 % en Noroccidente, pero cae −12 % en Caribe. Supermercado cae −12 % en Nororiente.
- **⚠️ Advertencia de volatilidad:** varias unidades que crecen en 2026 **cayeron en 2025** (Orinoquía −7,0 % → +12,0 %; Eje Cafetero −5,4 % → +8,3 %), y varias que caen en 2026 habían crecido en 2025 (Cúcuta +6,6 % → −5,4 %). Esto sugiere **rebotes** y no necesariamente tendencias. Por eso el dashboard debe mostrar **los tres periodos enero–septiembre (2024, 2025 y 2026)**, no solo la variación del último año. La solidez de cada hallazgo se evalúa en la Fase 4.5.
- **Decisiones:** D1, D2, D3.

### P2. ¿Qué combinación de categorías, formatos, promociones, fidelización y canales presenta mejores oportunidades?
- **Subpreguntas:** ¿cuánto pesa cada palanca comercial en las ventas (mix)? ¿Cuáles crecen? ¿Hay diferencias de margen o de venta por línea entre grupos?
- **Evidencia preliminar:**
  - **Canal:** Domicilio crece +6,1 % (12,5 % de participación) y tienda física +0,2 % (81,5 %). Por formato, Domicilio crece +12–13 % en Express e Hipermercado, y Click & Collect +17,5 % en Hipermercado.
  - **Promociones:** "Puntos dobles" cae −7,1 % y "Sin promoción" crece +2,1 %. El peso de la promoción es similar en todas las categorías (39–41 % de las ventas).
  - **Fidelización:** las ventas de no fidelizados crecen +2,6 % y las de fidelizados −0,2 %. Tienen la misma venta por línea.
  - **Medio de pago:** Crédito +4,2 % y Débito −2,9 %.
  - **Margen estimado %:** entre 27,4 % y 27,7 % en todos los grupos. **No hay diferencias de rentabilidad relevantes**, y eso se declara como resultado.
- **Implicación:** P2 se responde con **mix y crecimiento**, no con rentabilidad. La única dimensión con diferencias grandes en venta por línea es la categoría ($13 mil en Panadería frente a $53 mil en Carnes), que es estructural.
- **Decisiones:** D4, D5.

### P3. ¿Dónde existen problemas de disponibilidad que requieren atención operativa?
- **Subpreguntas:** ¿qué categorías, formatos y ciudades concentran las líneas con quiebre? ¿Cuántas ventas se registraron en condición de quiebre? ¿El quiebre mejora o empeora en el tiempo?
- **Evidencia preliminar:**
  - Tasa global: 8,08 %. Estable en el tiempo (enero–septiembre: 7,9 % → 8,2 % → 7,9 %).
  - Por categoría: Aseo hogar 8,8 % y Cuidado personal 8,5 % (las más altas); Lácteos 7,6 % (la más baja).
  - Por volumen: Bogotá concentra 1.192 líneas con quiebre ($32 M en ventas en esa condición). Carnes tiene la mayor venta afectada ($26,5 M).
  - Focos en cruces: Pereira–Cuidado personal 11,6 % (n = 346), Villavicencio–Aseo hogar 10,7 % (n = 385), Medellín–Aseo hogar 10,0 % (n = 988).
- **⚠️ Advertencia estadística:** con 96 cruces ciudad × categoría, algunos superan el 10 % solo por azar. En la Fase 4 se aplica una prueba de significancia o un umbral mínimo de líneas antes de llamarlos "foco". Los cruces con más líneas (por ejemplo, Medellín–Aseo hogar, n = 988) son los más sólidos.
- **Decisiones:** D6.

## 5. KPIs

| KPI | Definición | Fórmula (DAX conceptual) | Cifra de control | Pregunta |
|---|---|---|---|---|
| **Ventas netas** | Valor vendido después de descuentos | `SUM(venta_neta_cop)` | $1.560.062.403 (total) | P1, P2 |
| **Crecimiento ventas (enero–septiembre)** | Variación frente al mismo periodo del año anterior | `DIVIDE([Ventas], [Ventas año anterior comparable]) − 1` | 2026 vs 2025: +0,93 %; 2025 vs 2024: −0,07 % | P1 |
| **Margen estimado %** | Proporción de la venta que queda tras el costo estimado | `DIVIDE([Ventas] − [Costo], [Ventas])` | 27,48 % | P2 |
| **% Quiebre de stock** | Proporción de líneas vendidas con quiebre en los últimos 7 días | `DIVIDE([Líneas con quiebre], [Líneas])` | 8,08 % | P3 |
| **Venta por línea** | Valor promedio de una línea de venta | `DIVIDE([Ventas], [Líneas])` | $26.001 | P2 |
| _Referencia:_ Ticket promedio (ID dataset) | Ventas ÷ IDs de transacción distintos, siempre global | Ver plan, sección 8.1 | $73.366 | — |

**Medidas de apoyo** (para gráficos y tooltips, no son KPI de cabecera): Líneas de venta, Unidades, Unidades por línea, Ventas con quiebre, % Ventas en promoción, Participación % (sobre el total del contexto), Diferencia absoluta de ventas frente al año anterior.

## 6. Dimensiones para segmentar y comparar

| Dimensión | Uso principal | Pregunta |
|---|---|---|
| Fecha (año, trimestre, mes) | Eje temporal, periodo comparable | P1, P3 |
| Región → ciudad (con departamento) | Comparación geográfica y profundización | P1, P3 |
| Formato de tienda | Comparación por formato y cruce con región y canal | P1, P2, P3 |
| Categoría | Mix, crecimiento y quiebre por categoría | P1, P2, P3 |
| Promoción (tipo y con/sin) | Mix promocional | P2 |
| Canal | Mix y crecimiento por canal | P2 |
| Medio de pago | Mix (dimensión secundaria) | P2 |
| Cliente fidelizado | Mix (dimensión secundaria) | P2 |

Se excluyen: `producto_generico` (anónima y uniforme) y `id_transaccion` como dimensión.

## 7. Filtros e interacciones necesarios

| Mecanismo | Propósito analítico | Páginas |
|---|---|---|
| Segmentador de **año** (con periodo comparable enero–septiembre) | Cambiar el periodo de análisis sin romper la comparación | Todas |
| Segmentadores de **región** y **formato** | Enfocar el análisis en el ámbito de una gerencia de tiendas | Todas |
| Segmentador de **categoría** | Enfocar el análisis en una gerencia de categoría | 2, 3, 4 |
| **Selección cruzada** entre gráficos | Ejemplo de la guía: seleccionar Orinoquía y ver qué ciudades, formatos y categorías explican su comportamiento | 2, 3, 4 |
| **Jerarquía de profundización** región → ciudad | Bajar de región a ciudad sin cambiar de página | 2, 4 |
| **Tooltips personalizados** | Mostrar los tres periodos enero–septiembre (por la advertencia de volatilidad) y el n de líneas (por la advertencia estadística) | 2, 4 |
| **Navegación** entre páginas (botones) | Recorrer el dashboard en el orden de las preguntas | Todas |

Los segmentadores se **sincronizan** entre páginas para que el contexto elegido se mantenga.

## 8. Hallazgos candidatos (se validan en las Fases 4 y 4.5)

| # | Candidato | Pregunta | Riesgo a validar |
|---|---|---|---|
| H1 | El total está plano, pero esconde regiones que crecen (Orinoquía, Eje Cafetero, Noroccidente) y otras que caen (Nororiente, Caribe) | P1 | Volatilidad: ¿es tendencia o rebote? |
| H2 | Abarrotes es la categoría que más aporta al crecimiento (+$5,7 M) | P1 | Rebote frente a 2025 (−3,4 %). En la comparación 2026 vs 2024 sigue creciendo (+5,4 %). |
| H3 | Contrastes fuertes región × formato (Express en Orinoquía y Noroccidente frente a Caribe) | P1 | n pequeño por celda |
| H4 | Domicilio es el canal de mayor crecimiento, sobre todo en Express e Hipermercado | P2 | 2025 cayó −4,8 % |
| H5 | No hay diferencias de margen entre palancas comerciales: la oportunidad está en el volumen, no en el margen | P2 | Hallazgo "negativo" que hay que comunicar bien |
| H6 | "Puntos dobles" pierde ventas (−7,1 %) | P2 | Participación baja (5,2 %) |
| H7 | Aseo hogar y Cuidado personal tienen el mayor quiebre, con focos en ciertas ciudades | P3 | Comparaciones múltiples, n por celda |
| H8 | El quiebre es estable en el tiempo (no mejora): es un problema estructural | P3 | — |

## 9. Herramienta y flujo de trabajo

**Herramienta: Power BI Desktop.** Por qué:
- Integra en una sola herramienta la preparación (Power Query), el modelado (esquema estrella con relaciones), el cálculo (DAX con inteligencia de tiempo) y la interactividad (segmentadores, selección cruzada, tooltips, navegación).
- Permite la sustentación en vivo que exige el enunciado.
- Maneja 60.000 filas sin problemas de rendimiento.
- Es una herramienta del curso, y el formato `.pbip` permite versionar el modelo y usar las skills de apoyo.

**Flujo de datos:**
```
CSV original (data/raw, solo lectura)
   → Power Query: UTF-8, configuración regional en-US, tipos, quiebre_flag, dimensiones
   → Modelo estrella: FactVentas + DimCalendario, DimGeografia, DimFormato, DimCategoria, DimPromocion, (canal/pago/fidelizado)
   → Medidas DAX en _Medidas (KPI, periodo comparable, apoyo)
   → Visuales por página (P1 → P2 → P3 → conclusiones)
Validación paralela: scripts/validacion/*.py recalculan desde el CSV cada cifra de control.
```

## 10. Pendiente de validación del equipo

1. ¿Aprueban el problema, la audiencia y las decisiones D1–D6?
2. ¿Aprueban los 5 KPI más la referencia del ticket?
3. ¿Están de acuerdo con mostrar los **tres periodos enero–septiembre** (2024, 2025 y 2026) por la advertencia de volatilidad?
4. ¿Confirman que se avanza a la **Fase 3 — Modelo de datos**? En esa fase el trabajo pasa a Power BI Desktop: les daré los pasos exactos de Power Query y el modelo para que los ejecuten, o los preparo como archivos si trabajamos con `.pbip`.
