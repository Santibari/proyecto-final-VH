# Fase 3 — Modelo de datos (Power BI)

_Proyecto final BI 2026-2 · Grupo 3 · Cadena nacional de supermercados_
_Implementación: el script `scripts/pbip/generar_modelo_tmdl.py` escribe este modelo en el proyecto `powerbi/*.pbip` (archivos TMDL)._

---

## 1. Esquema estrella

```
                 DimCalendario (Fecha)
                         │ 1
                         │
DimGeografia (Ciudad) 1──┤          ┌──1 DimCategoria (Categoria)
                         │ *        │
DimFormato (Formato) 1───*  FactVentas  *───1 DimPromocion (Promocion)
                            (1 fila =   *
                         línea de venta) │
                                         └──1 DimCondicionVenta (clave_condicion)

_Medidas: tabla sin datos que solo agrupa las medidas DAX
```

- **Tabla de hechos `FactVentas`.** Granularidad: 1 fila = 1 línea de venta (`id_linea`, 60.000 filas).
- **Relaciones:** todas de varios a uno (`*` → `1`), con filtro en una sola dirección (de la dimensión hacia los hechos). No hay relaciones bidireccionales ni de varios a varios.
- **Claves:** se usan las claves naturales de texto (ciudad, formato, categoría, promoción). Las dimensiones tienen pocas filas (máximo 24), así que no hace falta crear claves numéricas y el modelo es más fácil de explicar.

## 2. Tablas

| Tabla | Filas | Origen | Columnas | Justificación |
|---|---|---|---|---|
| `FactVentas` | 60.000 | Power Query desde `Base` | id_linea, id_transaccion, fecha, ciudad, formato_tienda, categoria, promocion, clave_condicion, unidades, precio_unitario_cop, descuento_pct, venta_neta_cop, costo_estimado_cop, quiebre_flag | Hechos medibles y claves hacia las dimensiones. |
| `DimCalendario` | 1.096 (2024-01-01 a 2026-12-31) | Tabla calculada en DAX | Fecha, Año, Trimestre, MesNum, Mes, AñoMes, EsPeriodoComparable, TieneDatos | Inteligencia de tiempo y control del corte de 2026. Marcada como tabla de fechas. |
| `DimGeografia` | 12 | Power Query (valores distintos) | Region, Departamento, Ciudad + jerarquía Región → Ciudad | Jerarquía geográfica limpia (1 ciudad = 1 departamento = 1 región). |
| `DimFormato` | 3 | Power Query | Formato | Eje del reto ("por formato y región"). |
| `DimCategoria` | 8 | Power Query | Categoria | Eje de la gerencia de categoría. |
| `DimPromocion` | 5 | Power Query | Promocion, Con promocion (Sí/No) | Comparar tipos de promoción y con/sin promoción. |
| `DimCondicionVenta` | 24 | Power Query | clave_condicion, Canal, Medio de pago, Cliente fidelizado | **Dimensión basura (junk dimension):** agrupa 3 atributos de pocos valores y sin jerarquía entre ellos (3 × 4 × 2 = 24 combinaciones). Evita tres tablas de 2 a 4 filas. |
| `_Medidas` | 0 | Tabla vacía | — | Agrupa las medidas DAX en carpetas. |

**Excluidas:**
- `producto_generico`: referencia anónima repetida en todas las categorías (ver perfilamiento).
- `departamento`, `region`, `canal`, `medio_pago`, `cliente_fidelizado` y `quiebre_stock_ult_7d` no están en la tabla de hechos porque ya viven en sus dimensiones o fueron convertidas (`quiebre_flag`).

No se elimina ninguna fila.

## 3. Transformaciones en Power Query

| Paso | Consulta | Qué hace | Por qué |
|---|---|---|---|
| 1 | `RutaCSV` (parámetro) | Ruta del CSV | Si la carpeta cambia al entregar, solo se edita este parámetro. |
| 2 | `Base` (no se carga) | Lee el CSV con **codificación 65001 (UTF-8)**, promueve encabezados, quita el BOM y asigna tipos con **configuración regional en-US** | Las tildes se ven bien y `descuento_pct` "10.18" se lee como 10,18 y no como 1018. |
| 3 | `FactVentas` | Agrega `quiebre_flag` = 1 si quiebre = "Sí", si no 0. Agrega `clave_condicion` = canal \| medio_pago \| cliente_fidelizado. Selecciona columnas. | Una bandera numérica se puede sumar y promediar. La clave conecta con la dimensión basura. |
| 4 | Dimensiones | `Table.Distinct` de las columnas de cada dimensión desde `Base` y cambio de nombres | Cada dimensión sale del mismo dato, así que no puede haber claves huérfanas. |

**Tipos:** `fecha` = fecha. `unidades`, `precio_unitario_cop`, `venta_neta_cop`, `costo_estimado_cop` y `quiebre_flag` = número entero. `descuento_pct` = número decimal. El resto = texto.

**Configuración del modelo:** se desactiva la opción "Fecha/hora automática" porque se usa una tabla calendario propia.

## 4. Tabla calendario

```DAX
DimCalendario =
VAR PrimeraFecha = MIN ( FactVentas[fecha] )
VAR UltimaFecha  = MAX ( FactVentas[fecha] )
RETURN
ADDCOLUMNS (
    CALENDAR ( DATE ( YEAR ( PrimeraFecha ), 1, 1 ), DATE ( YEAR ( UltimaFecha ), 12, 31 ) ),
    "Año", YEAR ( [Date] ), ...
    "EsPeriodoComparable", MONTH ( [Date] ) <= MONTH ( UltimaFecha ),   -- ene–sep
    "TieneDatos", [Date] <= UltimaFecha
)
```
- Cubre años completos (2024–2026), algo que exigen las funciones de inteligencia de tiempo como `DATEADD`.
- `EsPeriodoComparable` es **dinámico**: si llegaran datos de octubre de 2026, el corte pasaría solo a enero–octubre.
- `Mes` se ordena por `MesNum`.

## 5. Medidas DAX (tabla `_Medidas`)

| Carpeta | Medida | Fórmula | Control |
|---|---|---|---|
| 1. Ventas | Ventas Netas | `SUM(FactVentas[venta_neta_cop])` | 1.560.062.403 |
| | Costo Estimado | `SUM(FactVentas[costo_estimado_cop])` | 1.131.389.400 |
| | Lineas de Venta | `COUNTROWS(FactVentas)` | 60.000 |
| | Unidades | `SUM(FactVentas[unidades])` | 121.393 |
| 2. Margen | Margen Estimado | `[Ventas Netas] - [Costo Estimado]` | 428.673.003 |
| | Margen Estimado % | `DIVIDE([Margen Estimado], [Ventas Netas])` | 27,48 % |
| 3. Tiempo (Ene-Sep) | Ventas Ene-Sep | `CALCULATE([Ventas Netas], KEEPFILTERS(DimCalendario[EsPeriodoComparable] = TRUE()))` | 2024: 425.113.135 · 2025: 424.805.507 · 2026: 428.753.035 |
| | Ventas Ene-Sep Año Anterior | `CALCULATE([Ventas Ene-Sep], DATEADD(DimCalendario[Fecha], -1, YEAR))` | 2026 → 424.805.507 |
| | Variacion Ventas Ene-Sep | Actual − Año anterior (vacío si no hay año anterior) | 2026: +3.947.528 |
| | Crecimiento Ventas Ene-Sep % | `DIVIDE(Actual − AA, AA)` | 2026: +0,93 % · 2025: −0,07 % |
| | Ventas Ene-Sep Hace 2 Años | `CALCULATE([Ventas Ene-Sep], DATEADD(DimCalendario[Fecha], -2, YEAR))` | 2026 → 425.113.135 |
| | Crecimiento vs Hace 2 Años % | `DIVIDE(Actual − Hace2, Hace2)` | 2026 vs 2024: +0,86 % |
| | Lectura Tendencia | "Crece (sostenido)" / "Cae (sostenido)" / "Oscila (rebote)" / "Estable", según el signo y ±2 % en ambas comparaciones (Fase 4.5) | Orinoquía: Crece (sostenido) |
| 7. Formato condicional | Color Crecimiento | Verde / rojo / naranja / gris según `Lectura Tendencia` | — |

Las medidas que comparan contra años anteriores devuelven vacío si no hay **un solo año** en contexto (`HASONEVALUE(DimCalendario[Año])`).
| 4. Quiebre | Lineas con Quiebre | `SUM(FactVentas[quiebre_flag])` | 4.849 |
| | % Quiebre | `DIVIDE([Lineas con Quiebre], [Lineas de Venta])` | 8,08 % |
| | Ventas con Quiebre | `CALCULATE([Ventas Netas], FactVentas[quiebre_flag] = 1)` | 126.858.302 |
| 5. Por linea | Venta por Linea | `DIVIDE([Ventas Netas], [Lineas de Venta])` | 26.001 |
| | Unidades por Linea | `DIVIDE([Unidades], [Lineas de Venta])` | 2,02 |
| 6. Promocion | Ventas en Promocion | `CALCULATE([Ventas Netas], DimPromocion[Con promocion] = "Sí")` | 618.958.563 |
| | % Ventas en Promocion | `DIVIDE([Ventas en Promocion], [Ventas Netas])` | 39,68 % |
| 9. Referencia guia | Transacciones (ID dataset) | `DISTINCTCOUNT(FactVentas[id_transaccion])` | 21.264 |
| | Ticket Promedio (ID dataset) | `CALCULATE(DIVIDE([Ventas Netas], [Transacciones (ID dataset)]), REMOVEFILTERS())` | 73.366 (fijo) |

**Uso correcto de las medidas de tiempo:** el crecimiento se lee con **un año seleccionado** (segmentador de selección única). Sin año seleccionado, "año anterior" mezcla varios años y la cifra no tiene sentido. Esto se controla en el diseño (Fase 5).

## 6. Validación (después de la primera actualización en Power BI)

Se agrega al reporte una página técnica `Validacion` con una tarjeta por cada cifra de control de la sección 5. Debe coincidir con `python scripts/validacion/01_perfilamiento.py`. Además se comprueba:
- [ ] `DimGeografia` = 12 filas, `DimCondicionVenta` = 24, `DimCalendario` = 1.096.
- [ ] Ninguna relación tiene filas "(en blanco)" en las dimensiones (no hay claves huérfanas).
- [ ] Máximo `descuento_pct` = 32,27.
- [ ] "Bogotá D.C.", "Medellín", "Orinoquía" y "Lácteos" con tildes correctas.
- [ ] El ticket no cambia al filtrar por región.
