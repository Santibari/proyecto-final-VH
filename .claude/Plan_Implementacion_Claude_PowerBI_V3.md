# PLAN DE IMPLEMENTACIÓN — CLAUDE + POWER BI

**Propósito.** Este documento es la hoja de ruta y el conjunto de reglas de trabajo para que Claude apoye el análisis, el modelado, la construcción, la validación y la preparación de la sustentación del dashboard en Power BI. Claude actúa como copiloto técnico y analítico: propone, explica, valida y documenta. El equipo toma la decisión final y debe entender todo lo que se implemente.

---

## 0. Cambios respecto a la V2

| # | Cambio | Motivo (verificado) |
|---|---|---|
| C1 | **`id_transaccion` queda en revisión.** No se usa para KPIs hasta que el equipo lo decida (sección 8.1). | La guía lo describe como una compra. Sin embargo, en el CSV 16.847 de los 16.852 IDs con más de una línea tienen líneas en **fechas distintas** y también en ciudades, formatos, medios de pago y canales distintos. Ninguno de esos IDs es totalmente consistente (0 de 16.852). Por ejemplo, `T-0003774` aparece en Santa Marta (29/09/2024), Pereira (14/04/2025), Cali (28/05/2025) y Barranquilla (14/07/2026). Una compra real no puede ocurrir en tres años y cuatro ciudades. |
| C2 | La granularidad de la tabla de hechos es **la línea de venta**. Se agregan medidas por línea. | Coincide con la guía ("cada fila es una línea de venta") y no depende de C1. |
| C3 | Regla de **periodo comparable: enero–septiembre vs enero–septiembre**. | Oct–dic solo existe en 2024 y 2025. Ventas ene–sep: 2024 = $425,1 M; 2025 = $424,8 M; 2026 = $428,8 M (+0,9 %). Si se compara el año completo, 2026 parece caer un 24 %, y esa caída es falsa. |
| C4 | Regla de **materialidad**: "no hay diferencia" también es un hallazgo. | Los datos son muy homogéneos. El margen % está entre 27,2 % y 27,7 % en todas las dimensiones. El quiebre está entre 7,5 % y 8,8 %. Fidelizados y no fidelizados tienen el mismo valor por línea. |
| C5 | Se documentan las inconsistencias de origen. | La promoción "2x1" tiene un descuento promedio del 10 %, igual que las demás. Hay 2.390 líneas con una diferencia de hasta ±0,05 % frente a `unidades × precio × (1 − desc)`, que es solo redondeo. |
| C6 | Configuración de importación: **UTF-8 (65001)** y **configuración regional en-US**. | El archivo usa punto decimal. Con es-CO, `descuento_pct` "10.18" se lee mal y las tildes se dañan. |
| C7 | Se completan las reglas vacías de la sección 3 y se corrige el formato de las medidas. | La V2 tenía 6 viñetas vacías y medidas pegadas en la misma línea. |
| C8 | Se concretan el modelo estrella, el % de quiebre y el periodo comparable, cada uno con su cifra de control. | La V2 los dejaba abiertos. |
| C9 | Se incorporan los requisitos de la guía: no medir retención, color semántico (verde, rojo, amarillo/naranja y neutros), guion de sustentación y banco de preguntas. | Alineación con la guía del curso. |
| C10 | Se añade la sección 15, con las skills de Power BI y su forma de uso. | Análisis de `.claude/.Skills/`. |

---

## 1. Contexto que Claude debe respetar

- Contexto asignado: Grupo 3, cadena nacional de supermercados.
- Audiencia: gerencia de tiendas y de categoría.
- Reto orientador: analizar ventas, promociones, mezcla de categorías, fidelización, medios de pago, canales y quiebres de inventario para detectar oportunidades por formato y región.
- Frase guía del curso: **datos → análisis → hallazgos → decisiones**.
- Fuente única: `03_cadena_supermercados.csv`. No se sustituye ni se complementa con otra base.
- El dashboard debe ser interactivo y servir para tomar decisiones.
- La sustentación se hace desde Power BI. Cualquiera de los tres integrantes puede recibir preguntas técnicas.
- Claude no avanza a la fase siguiente si la actual no ha sido documentada y validada por el equipo.

## 2. Diagnóstico inicial del dataset (verificado)

| Elemento | Resultado |
|---|---|
| Registros (líneas de venta) | 60.000 |
| Variables | 19 |
| `id_linea` únicos | 60.000 (clave de la tabla de hechos) |
| `id_transaccion` distintos | 21.264 (ver C1: no se comporta como una compra) |
| Rango de fechas | 01/01/2024 – 30/09/2026 (33 meses, ~1.818 líneas por mes, estable) |
| Faltantes / duplicados | 0 / 0 |
| Ventas netas totales | $1.560.062.403 |
| Costo estimado total | $1.131.389.400 |
| Margen estimado total | $428.673.003 (27,48 %) |
| Líneas con quiebre de stock | 4.849 (8,08 %) |
| Líneas de clientes fidelizados | 35.520 (59,2 %) |
| Codificación / separador decimal | UTF-8 con BOM / punto |

**Cardinalidades:** ciudad 12 · departamento 12 · región 7 · formato 3 · categoría 8 · producto_generico 6 ("Referencia 01–06", repetidas en todas las categorías) · promoción 5 · medio de pago 4 · canal 3 · fidelizado 2 · quiebre 2.

**Jerarquía geográfica limpia:** cada ciudad pertenece a un solo departamento y a una sola región.

**Riesgos identificados:**
1. `id_transaccion` es inconsistente (C1).
2. 2026 es parcial (C3).
3. La señal es débil: las diferencias entre grupos son pequeñas (C4).
4. `producto_generico` no aporta al análisis (es una referencia anónima repetida en todas las categorías).
5. No existe un ID de tienda. Ciudad × formato (36 combinaciones) puede servir como aproximación a "punto de venta", siempre documentado como supuesto.
6. No existe un ID de cliente, así que **no se puede medir retención** (lo exige la guía). `cliente_fidelizado` es solo una marca en la línea.
7. `quiebre_stock_ult_7d` es una marca de estado reciente. **No mide ventas perdidas.**
8. `costo_estimado_cop` es una estimación. El margen siempre se llama "margen **estimado**".

## 3. Reglas maestras para Claude

1. No inventar variables, datos, clientes, causalidades ni hallazgos. Si algo no está soportado por el dataset, decirlo.
2. Usar solo el dataset asignado.
3. Separar siempre: **dato observado → cálculo → interpretación → recomendación**.
4. La unidad de análisis es la línea de venta. `id_transaccion` solo se usa según la decisión de la sección 8.1.
5. **Materialidad:** antes de llamar "hallazgo" a una diferencia, reportar su magnitud absoluta y relativa y el número de líneas que la sustentan. Las diferencias de menos de 1 punto porcentual en tasas (margen %, quiebre %) se reportan como "sin diferencia relevante", salvo que haya una justificación.
6. No afirmar causalidad. Se dice "se asocia con", no "causa".
7. No hablar de retención ni de comportamiento individual de clientes: no existe un ID de cliente.
8. Todas las medidas y transformaciones deben poder explicarse en la sustentación.
9. Antes de implementar una decisión importante, proponerla y justificarla. El equipo la revisa.
10. Ningún visual se construye solo porque la variable existe.
11. No eliminar registros sin una justificación documentada. El CSV original no se modifica.
12. **2026 es parcial (hasta el 30/09/2026).** Toda comparación anual o estacional usa enero–septiembre vs enero–septiembre.
13. Cada color tiene una función semántica (sección 10) y cada interacción tiene un propósito analítico.
14. Las etiquetas de promoción se usan como categorías. No se infiere su mecánica (por ejemplo, que "2x1" sea un 50 % de descuento).
15. Si Claude detecta que una decisión anterior fue incorrecta, lo señala, explica el motivo y propone la corrección antes de continuar.

## 4. Arquitectura de trabajo por fases

| Fase | Qué hace Claude | Salida |
|---|---|---|
| **0 — Entorno** | Crear la estructura de carpetas, instalar las skills útiles (sección 15) y proteger el CSV original. | Carpetas + skills operativas |
| **1 — Perfilamiento** | Completar el perfilamiento, el diccionario de datos y la lista de validaciones para Power BI. | `docs/01_perfilamiento.md` |
| **2 — Problema** | Confirmar el problema y las 3 preguntas de la guía, con las decisiones que apoya cada una. Resolver la decisión 8.1. | `docs/02_problema.md` |
| **3 — Modelo** | Modelo estrella (sección 6), calendario y Power Query documentado. Guardar como **.pbip**. | Modelo validado + `docs/03_modelo.md` |
| **4 — Exploración** | Analizar todas las dimensiones con periodo comparable y materialidad. | Candidatos a hallazgo |
| **4.5 — Validación de hallazgos** | Para cada uno: dato, cálculo, magnitud, n, interpretación, limitación, decisión y visual. Validar con un script independiente sobre el CSV. El equipo aprueba. | `docs/04_matriz_hallazgos.md` |
| **5 — Diseño** | Wireframe basado solo en los hallazgos aprobados. | Propuesta aprobada |
| **6 — Construcción** | Construir en Power BI Desktop (el equipo) con apoyo de `pbi-report-builder` cuando convenga (sección 15). | PBIX/PBIP funcional |
| **7 — Validación técnica** | Contrastar totales, medidas, filtros y DAX contra el CSV. Auditar el modelo con `pbip-dependency-analyzer`. | Checklist de pruebas |
| **8 — Auditoría + sustentación** | Revisar como profesor evaluador. Preparar guion (sección 13) y banco de preguntas (sección 13.1). | Auditoría + guion |
| **9 — Entrega** | Verificar que el PBIX abre y que la ruta del CSV es fácil de actualizar. Documentación completa. | Paquete final |

**Estructura de carpetas:**
```
proyecto-final-VH/
├── .claude/
│   ├── Plan_Implementacion_Claude_PowerBI_V3.md
│   └── skills/<nombre-skill>/SKILL.md       (ubicación que Claude Code reconoce)
├── data/raw/03_cadena_supermercados.csv     (original, solo lectura)
├── docs/                                    (entregables de cada fase)
├── scripts/validacion/                      (recalculan las cifras de control desde el CSV)
├── powerbi/                                 (.pbip + .pbix final)
└── Guia_Estudiantes_Proyecto_Dashboard_BI.docx
```

## 5. Problema y preguntas (tomados de la guía, enriquecidos con evidencia)

**Pregunta central:** ¿Qué regiones, formatos y categorías presentan las principales oportunidades de crecimiento y qué factores comerciales u operativos deberían priorizarse?

- **P1.** ¿Cómo evoluciona el desempeño comercial y dónde se concentra el crecimiento? _(Siempre ene–sep vs ene–sep.)_
  Primera evidencia en 2026 vs 2025: el total crece +0,9 %. Orinoquía (+12,0 %), Eje Cafetero (+8,3 %) y Abarrotes (+9,1 %) crecen; Nororiente (−4,6 %) y Caribe (−2,6 %) caen. P1 tiene historia que contar.
- **P2.** ¿Qué combinación de categorías, formatos, promociones, fidelización y canales presenta mejores oportunidades?
  Advertencia: el margen % y el valor por línea son casi idénticos entre grupos. Probablemente se responda con **participación (mix) y crecimiento**. Domicilio crece +6,1 % mientras la tienda física crece +0,2 %. Si no hay diferencia, se dice.
- **P3.** ¿Dónde existen problemas de disponibilidad que requieren atención operativa?
  Advertencia: el rango es estrecho (7,5 %–8,8 %). Conviene analizar cruces (categoría × formato × ciudad) y el volumen de líneas afectadas.

## 6. Modelo de datos (propuesta para validar en la Fase 3)

**Tabla de hechos `FactVentas`.** Granularidad: **1 fila = 1 línea de venta** (`id_linea`).
Columnas: `id_linea`, `id_transaccion`, `fecha`, claves de dimensión, `unidades`, `precio_unitario_cop`, `descuento_pct`, `venta_neta_cop`, `costo_estimado_cop` y `quiebre_flag` (1/0).

| Dimensión | Contenido | Justificación |
|---|---|---|
| `DimCalendario` | Fechas continuas del 01/01/2024 al 31/12/2026: año, trimestre, mes, nombre del mes, `EsPeriodoComparable` (mes ≤ 9) y `TieneDatos` | Inteligencia de tiempo y corte de 2026. Se marca como tabla de fechas. |
| `DimGeografia` | Ciudad, departamento y región (12 filas) | Jerarquía real para profundizar región → ciudad (el ejemplo de la guía: "seleccionar Orinoquía"). |
| `DimFormato` | Formato de tienda (3) | Eje del reto. |
| `DimCategoria` | Categoría (8) | Eje del reto. `producto_generico` se excluye. |
| `DimPromocion` | Tipo de promoción + "Con/Sin promoción" (5) | Comparar con y sin promoción. |
| `DimCanal`, `DimMedioPago` | 3 y 4 filas | Alternativa: una dimensión basura `DimCondicionVenta` (canal × medio de pago × fidelizado). Se decide en la Fase 3. |

Reglas: relaciones 1:* con filtro en una sola dirección, sin bidireccionales. Los textos de la tabla de hechos se ocultan. Se usa una tabla de medidas `_Medidas`. Antes del DAX definitivo se confirman los nombres reales.

**Power Query, obligatorio:** codificación 65001 (UTF-8) y configuración regional **en-US** para los números. Control: `descuento_pct` máximo = 32,27; suma de ventas = 1.560.062.403; "Bogotá D.C." con tilde correcta.

## 7. Inteligencia de tiempo y corte de 2026

- Último dato: 30/09/2026. Oct–dic solo existe en 2024 y 2025.
- **Periodo comparable estándar: enero–septiembre.** Cifras de control: 2024 = $425.113.135; 2025 = $424.805.507; 2026 = $428.753.035.
- Las medidas de YoY limitan el año anterior a la última fecha con datos desplazada un año. No se usa `SAMEPERIODLASTYEAR` sin ese control.
- La estacionalidad mensual compara el mismo mes entre años. No se promedian meses con distinto número de años.
- Toda tarjeta de "Ventas 2026" lleva el rótulo "(ene–sep)".

## 8. Medidas DAX (punto de partida, se ajustan tras la Fase 3)

```DAX
Ventas Netas          = SUM ( FactVentas[venta_neta_cop] )
Costo Estimado        = SUM ( FactVentas[costo_estimado_cop] )
Margen Estimado       = [Ventas Netas] - [Costo Estimado]
Margen Estimado %     = DIVIDE ( [Margen Estimado], [Ventas Netas] )
Lineas de Venta       = COUNTROWS ( FactVentas )
Unidades              = SUM ( FactVentas[unidades] )
Venta por Linea       = DIVIDE ( [Ventas Netas], [Lineas de Venta] )
Unidades por Linea    = DIVIDE ( [Unidades], [Lineas de Venta] )
Lineas con Quiebre    = CALCULATE ( [Lineas de Venta], FactVentas[quiebre_flag] = 1 )
% Quiebre             = DIVIDE ( [Lineas con Quiebre], [Lineas de Venta] )
Ventas con Quiebre    = CALCULATE ( [Ventas Netas], FactVentas[quiebre_flag] = 1 )
% Ventas en Promocion = DIVIDE ( CALCULATE ( [Ventas Netas], DimPromocion[ConPromocion] = "Sí" ), [Ventas Netas] )
```
- **% Quiebre:** el denominador son las líneas del contexto filtrado. Significa "proporción de líneas con quiebre reciente", tal como lo define la guía. **No** representa ventas perdidas. Control: 4.849 / 60.000 = 8,08 %.
- **Crecimiento (Var % YoY ene–sep):** se construye en la Fase 4 con la regla de la sección 7. Control: +0,93 % (2026 vs 2025).
- Cada medida tiene su cifra de control, calculada con un script sobre el CSV.

### 8.1 Decisión pendiente del equipo: Transacciones y Ticket Promedio

La guía pide `Transacciones = DISTINCTCOUNT(id_transaccion)` (21.264) y "Ticket promedio" como KPI, y espera esa respuesta en la sustentación. El CSV muestra que ese ID agrupa líneas de fechas y ciudades distintas (C1). Opciones:

| Opción | Qué implica | Recomendación |
|---|---|---|
| **A. Consultar al profesor** con la evidencia (ejemplo `T-0003774`) | Resuelve el conflicto con autoridad. | **Recomendada, antes de la Fase 3.** |
| B. Usar el ticket como pide la guía, con una nota de limitación visible | Cumple la guía, pero el KPI es poco confiable. Hay que saber explicar la limitación. | Si el profesor lo pide. |
| C. Reemplazarlo por "Venta por línea" | Es más robusto, pero se aparta de la guía. | Si el profesor lo acepta. |

En cualquier caso, **haber detectado la inconsistencia es un punto a favor en la sustentación** ("validamos los datos y encontramos…").

## 9. Estructura del dashboard (de la guía, se valida en la Fase 5)

| Página | Pregunta que responde |
|---|---|
| 1. Resumen ejecutivo | ¿Cómo está el negocio y dónde debo mirar primero? KPIs: Ventas, Margen est. %, Crecimiento ene–sep, % Quiebre (+ Ticket según 8.1). |
| 2. Desempeño comercial | ¿Qué regiones, ciudades, formatos y categorías explican el desempeño? |
| 3. Promociones y clientes | ¿Cómo se comportan las promociones, la fidelización y los canales? (Se declara dónde no hay diferencias.) |
| 4. Disponibilidad y oportunidades | ¿Dónde hay problemas de stock que merecen atención? |

Las páginas pueden fusionarse o cambiar según la evidencia. No se añaden páginas por cantidad.

## 10. Diseño visual e interactividad

- Patrón Z o F justificado en cada página.
- **Color semántico (según la guía):** un color base de identidad; **verde** para resultados positivos o crecimiento; **rojo** para alertas o deterioro; **amarillo/naranja** para advertencias; **neutros** (grises) para lo que no necesita destacar. Un color nunca tiene dos significados. Si se usa la paleta IBCS de la skill (verde `#44C088`, rojo `#ED7373`, real `#0C3549`, comparación `#CCCCCC`), se agrega un amarillo/naranja de advertencia.
- Tooltips personalizados donde aporten contexto.
- Segmentadores ligados a las preguntas (periodo, región, formato, categoría) e interacción cruzada para profundizar (por ejemplo, Orinoquía → ciudades, categorías, formatos).
- Títulos con mensaje ("Orinoquía lidera el crecimiento ene–sep"), no solo nombres de gráficos.

## 11. Prompts de trabajo por fase

1. **Auditoría del dataset:** completar el perfilamiento, el diccionario y las validaciones. Partir de la sección 2 y no avanzar al diseño.
2. **Formulación del negocio:** confirmar el problema y las preguntas de la guía, evaluar su factibilidad con los datos y definir las decisiones que apoya cada pregunta.
3. **Modelo:** confirmar o ajustar la estrella de la sección 6 y documentar cada decisión.
4. **DAX:** medidas de la sección 8 + inteligencia de tiempo comparable, con su cifra de control.
5. **Exploración:** todas las dimensiones, con periodo comparable y materialidad. Sin causalidad.
6. **Validación de hallazgos:** matriz de impacto, solidez, n, limitación y visual. Recomendar qué entra y qué se descarta.
7. **Diseño visual:** páginas basadas solo en hallazgos validados.
8. **Auditoría final:** como profesor evaluador, con severidad, evidencia, corrección y criterio afectado.

## 12. Checklist de aceptación

- [ ] El problema está en una frase y tiene una audiencia definida.
- [ ] Hay 3 preguntas analíticas con evidencia en el dashboard.
- [ ] Hay al menos 3 KPI relevantes.
- [ ] El modelo estrella está validado y la granularidad (línea de venta) está documentada.
- [ ] La tabla calendario está validada y marcada como tabla de fechas.
- [ ] La decisión 8.1 (Transacciones/Ticket) está tomada y documentada.
- [ ] Las comparaciones temporales usan enero–septiembre vs enero–septiembre.
- [ ] Los totales coinciden con el CSV (ventas 1.560.062.403; margen 428.673.003; quiebre 8,08 %).
- [ ] Los decimales y las tildes se importaron correctamente.
- [ ] Los hallazgos se validaron antes del diseño y cumplen la regla de materialidad.
- [ ] No se afirma causalidad ni se habla de retención.
- [ ] Cada visual, filtro, interacción y color tiene una función explicable.
- [ ] El dashboard funciona directamente en Power BI.
- [ ] Los tres integrantes conocen los datos, el modelo, las medidas, los visuales y las decisiones.

## 13. Guion de sustentación (de la guía)

Contexto → Problema → Preguntas → Datos (qué es una fila) → Recorrido del dashboard → Hallazgos (explicarlos, no leer los gráficos) → Decisiones para la gerencia → Cierre.

### 13.1 Banco de preguntas (respuestas ajustadas a la evidencia)

| Pregunta | Respuesta |
|---|---|
| ¿Qué representa una fila? | Una línea de venta. |
| ¿Cuántas compras hay? | El dataset tiene 21.264 `id_transaccion` distintos. Al validarlo encontramos que un mismo ID agrupa líneas de fechas y ciudades distintas, por lo que [respuesta según la decisión 8.1]. |
| ¿Por qué una tabla calendario? | Para analizar meses y años y construir comparaciones de periodos equivalentes. |
| ¿Cómo calcularon el margen? | Venta neta menos costo estimado. Es un margen estimado. |
| ¿Por qué no comparan 2026 completo con 2025? | Porque 2026 llega hasta septiembre. Comparamos enero–septiembre de cada año. |
| ¿Una promoción aumentó las ventas? | No se puede afirmar causalidad. Solo describimos el comportamiento asociado. |
| ¿Pueden medir retención? | No, porque no existe un identificador de cliente. |
| ¿Por qué ese gráfico o esos colores? | Por la pregunta que responde (comparación, tendencia, composición o distribución) y por la función semántica del color. |

## 14. Condiciones previas pendientes

- [x] La guía del proyecto está en la carpeta.
- [ ] Rúbrica oficial con los criterios y su peso. La guía la menciona, pero no la incluye.
- [ ] Consultar al profesor sobre `id_transaccion` (decisión 8.1).
- [ ] Fechas de entrega y de sustentación.
- [ ] Confirmar si se permite entregar .pbip además de .pbix. Power BI Desktop (versión de Microsoft Store) y Node.js v22 ya están instalados.

## 15. Skills de Claude para Power BI

Análisis de las 3 skills ubicadas en `.claude/.Skills/`:

| Skill | Para qué sirve | Utilidad en este proyecto | Uso |
|---|---|---|---|
| `pbi-requirements-gathering` (`SKILL.md`) | Entrevista de requisitos en 10 fases para proyectos de consultoría (seguridad, licencias, gobierno, gestión del cambio…). | **Baja.** El problema, la audiencia y las preguntas ya están definidos por la guía. Casi todas sus fases no aplican a un proyecto académico. Además depende de `references/questions.md` y `requirements-template.md`, que **no están incluidos**, e incluye promoción del autor al final. | No instalar. Las Fases 1–2 de este plan cubren su propósito. |
| `pbi-report-builder` (`SKILL (2).md`) | Escribe páginas y visuales (formato PBIR en JSON) y medidas (TMDL) directamente en un proyecto **.pbip**. Incluye gráficos IBCS de variación. | **Media-alta en la Fase 6.** Acelera la creación de páginas, tarjetas KPI y la cuadrícula de diseño. Requisitos: que el .pbip lo cree Power BI Desktop, **con Desktop cerrado** mientras escribe, y Node.js (ya instalado). Faltan sus archivos `references/` (plantillas JSON, esquemas, IBCS), pero el SKILL.md contiene los patrones principales. Tiene referencias que no aplican (perfil del autor, skill de marca) que deben ignorarse. | Instalar. Usarla solo después de que el diseño esté aprobado. Cada visual generado debe revisarse y entenderse en Desktop. El formato fino y los tooltips se hacen manualmente. |
| `pbip-dependency-analyzer` (`SKILL (1).md`) | Audita un .pbip: medidas o columnas sin usar, dependencias, relaciones bidireccionales, tablas aisladas, referencias rotas. | **Alta en las Fases 7–8.** Sirve para dejar el modelo limpio y para explicar en la sustentación qué usa cada visual. Es autocontenida (no le faltan archivos). | Instalar. |

**Problema de ubicación:** Claude Code solo reconoce skills en `.claude/skills/<nombre>/SKILL.md`. La carpeta `.claude/.Skills/` (con punto y mayúscula) y los nombres `SKILL (1).md` y `SKILL (2).md` hacen que **ninguna de las tres esté activa hoy**. En la Fase 0 se reorganizan así:
```
.claude/skills/pbi-report-builder/SKILL.md
.claude/skills/pbip-dependency-analyzer/SKILL.md
```
**Condición para usarlas:** ambas requieren trabajar con el proyecto guardado como **.pbip**. Por eso la Fase 3 guarda el modelo en ese formato desde el inicio.

## 16. Regla final de trabajo

**NO empezar por los gráficos.**
Problema → preguntas → perfilamiento → modelo → exploración → hallazgos → validación de hallazgos → diseño → construcción → validación → auditoría → sustentación.
