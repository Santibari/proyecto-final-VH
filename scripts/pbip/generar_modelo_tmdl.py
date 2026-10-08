"""Fase 3 — Escribe el modelo estrella (docs/03_modelo.md) en el proyecto PBIP.

Requisitos:
  * Proyecto creado por Power BI Desktop con "Guardar como → Power BI Project (.pbip)"
    dentro de powerbi/ (este script NO crea el proyecto; Desktop genera esos archivos).
  * Power BI Desktop CERRADO mientras se ejecuta.

Qué hace (idempotente: se puede volver a ejecutar):
  * definition/expressions.tmdl  → parámetro RutaCSV + consulta Base (no cargada)
  * definition/tables/*.tmdl      → FactVentas, dimensiones, DimCalendario, _Medidas
  * definition/relationships.tmdl → relaciones 1:* de filtro único
  * definition/model.tmdl         → desactiva fecha/hora automática y referencia las tablas

Uso:  python scripts/pbip/generar_modelo_tmdl.py
"""
from pathlib import Path
import re
import sys
import uuid

RAIZ = Path(__file__).resolve().parents[2]
CSV = RAIZ / "data" / "raw" / "03_cadena_supermercados.csv"
NAMESPACE = uuid.UUID("6f1c2a0e-3b7d-4c55-9a1e-03c0ffee2026")

TABLAS_PROPIAS = ["FactVentas", "DimCalendario", "DimGeografia", "DimFormato",
                  "DimCategoria", "DimPromocion", "DimCondicionVenta", "_Medidas"]


def tag(nombre):
    """lineageTag estable: el mismo objeto conserva su identificador entre ejecuciones."""
    return str(uuid.uuid5(NAMESPACE, nombre))


def q(nombre):
    """Cita un nombre TMDL si tiene espacios o caracteres especiales."""
    return nombre if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", nombre) else f"'{nombre}'"


def indentar(texto, tabs):
    return "\n".join(("\t" * tabs + linea) if linea.strip() else "" for linea in texto.strip("\n").splitlines())


# --------------------------------------------------------------------------- columnas
def columna(tabla, nombre, tipo, *, oculta=False, resumen="none", formato=None,
            origen=None, calculada=False, extra=()):
    lineas = [f"\tcolumn {q(nombre)}",
              f"\t\tdataType: {tipo}"]
    if formato:
        lineas.append(f"\t\tformatString: {formato}")
    if oculta:
        lineas.append("\t\tisHidden")
    lineas += [f"\t\tlineageTag: {tag(f'{tabla}.{nombre}')}",
               f"\t\tsummarizeBy: {resumen}"]
    lineas += [f"\t\t{e}" for e in extra]
    if calculada:
        lineas += ["\t\tisNameInferred", f"\t\tsourceColumn: [{origen or nombre}]"]
    else:
        lineas.append(f"\t\tsourceColumn: {origen or nombre}")
    return "\n".join(lineas) + "\n"


def particion_m(tabla, m):
    return (f"\tpartition {q(tabla)} = m\n\t\tmode: import\n\t\tsource =\n"
            f"{indentar(m, 4)}\n")


def tabla_tmdl(nombre, cuerpo, propiedades=()):
    cab = [f"table {q(nombre)}"] + [f"\t{p}" for p in propiedades] + [f"\tlineageTag: {tag(nombre)}"]
    return "\n".join(cab) + "\n\n" + cuerpo.rstrip("\n") + "\n\n\tannotation PBI_ResultType = Table\n"


def m_dimension(columnas_origen, renombres):
    sel = ", ".join(f'"{c}"' for c in columnas_origen)
    ren = ", ".join(f'{{"{a}", "{b}"}}' for a, b in renombres)
    return f"""
let
    Origen = Base,
    Columnas = Table.SelectColumns(Origen, {{{sel}}}),
    Distintos = Table.Distinct(Columnas),
    Nombres = Table.RenameColumns(Distintos, {{{ren}}})
in
    Nombres
"""


# --------------------------------------------------------------------------- expresiones
def expresiones():
    ruta = str(CSV).replace('"', '""')
    base = """
let
    Origen = Csv.Document(File.Contents(RutaCSV), [Delimiter = ",", Columns = 19, Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars = true]),
    SinBOM = Table.TransformColumnNames(Encabezados, each Text.Remove(_, {Character.FromNumber(65279)})),
    Tipos = Table.TransformColumnTypes(SinBOM, {
        {"id_linea", type text}, {"id_transaccion", type text}, {"fecha", type date},
        {"ciudad", type text}, {"departamento", type text}, {"region", type text},
        {"formato_tienda", type text}, {"categoria", type text}, {"producto_generico", type text},
        {"unidades", Int64.Type}, {"precio_unitario_cop", Int64.Type}, {"promocion", type text},
        {"descuento_pct", type number}, {"venta_neta_cop", Int64.Type}, {"costo_estimado_cop", Int64.Type},
        {"medio_pago", type text}, {"cliente_fidelizado", type text}, {"canal", type text},
        {"quiebre_stock_ult_7d", type text}}, "en-US")
in
    Tipos
"""
    return (f'expression RutaCSV = "{ruta}" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]\n'
            f"\tlineageTag: {tag('expr.RutaCSV')}\n\n"
            "\tannotation PBI_ResultType = Text\n\n"
            "expression Base =\n"
            f"{indentar(base, 2)}\n"
            f"\tlineageTag: {tag('expr.Base')}\n\n"
            "\tannotation PBI_ResultType = Table\n")


# --------------------------------------------------------------------------- tablas
MONEDA = r"\$#,0;(\$#,0);\$#,0"
ENTERO = "#,0"
PCT = "0.00%;-0.00%;0.00%"


def fact_ventas():
    t = "FactVentas"
    m = """
let
    Origen = Base,
    Quiebre = Table.AddColumn(Origen, "quiebre_flag", each if [quiebre_stock_ult_7d] = "Sí" then 1 else 0, Int64.Type),
    Clave = Table.AddColumn(Quiebre, "clave_condicion", each [canal] & "|" & [medio_pago] & "|" & [cliente_fidelizado], type text),
    Columnas = Table.SelectColumns(Clave, {
        "id_linea", "id_transaccion", "fecha", "ciudad", "formato_tienda", "categoria", "promocion",
        "clave_condicion", "unidades", "precio_unitario_cop", "descuento_pct", "venta_neta_cop",
        "costo_estimado_cop", "quiebre_flag"})
in
    Columnas
"""
    cols = [
        columna(t, "id_linea", "string", oculta=True),
        columna(t, "id_transaccion", "string", oculta=True),
        columna(t, "fecha", "dateTime", oculta=True, formato="dd/mm/yyyy"),
        columna(t, "ciudad", "string", oculta=True),
        columna(t, "formato_tienda", "string", oculta=True),
        columna(t, "categoria", "string", oculta=True),
        columna(t, "promocion", "string", oculta=True),
        columna(t, "clave_condicion", "string", oculta=True),
        columna(t, "unidades", "int64", oculta=True, resumen="sum", formato=ENTERO),
        columna(t, "precio_unitario_cop", "int64", oculta=True, resumen="sum", formato=MONEDA),
        columna(t, "descuento_pct", "double", oculta=True, resumen="sum", formato="0.00"),
        columna(t, "venta_neta_cop", "int64", oculta=True, resumen="sum", formato=MONEDA),
        columna(t, "costo_estimado_cop", "int64", oculta=True, resumen="sum", formato=MONEDA),
        columna(t, "quiebre_flag", "int64", oculta=True, resumen="sum", formato=ENTERO),
    ]
    return tabla_tmdl(t, "\n".join(cols) + "\n" + particion_m(t, m))


def dim_simple(t, columnas_origen, renombres, tipos=None, extra_cols="", m=None):
    tipos = tipos or {}
    cols = [columna(t, nuevo, tipos.get(nuevo, "string")) for _, nuevo in renombres]
    cuerpo = "\n".join(cols) + extra_cols + "\n" + particion_m(t, m or m_dimension(columnas_origen, renombres))
    return tabla_tmdl(t, cuerpo)


def dim_geografia():
    t = "DimGeografia"
    ren = [("region", "Region"), ("departamento", "Departamento"), ("ciudad", "Ciudad")]
    jerarquia = f"""
	hierarchy 'Region - Ciudad'
		lineageTag: {tag(t + '.jerarquia')}

		level Region
			lineageTag: {tag(t + '.jerarquia.Region')}
			column: Region

		level Ciudad
			lineageTag: {tag(t + '.jerarquia.Ciudad')}
			column: Ciudad
"""
    return dim_simple(t, ["region", "departamento", "ciudad"], ren, extra_cols=jerarquia)


def dim_promocion():
    t = "DimPromocion"
    m = """
let
    Origen = Base,
    Columnas = Table.Distinct(Table.SelectColumns(Origen, {"promocion"})),
    Nombres = Table.RenameColumns(Columnas, {{"promocion", "Promocion"}}),
    ConPromo = Table.AddColumn(Nombres, "Con promocion", each if [Promocion] = "Sin promoción" then "No" else "Sí", type text)
in
    ConPromo
"""
    cols = [columna(t, "Promocion", "string"), columna(t, "Con promocion", "string")]
    return tabla_tmdl(t, "\n".join(cols) + "\n" + particion_m(t, m))


def dim_condicion():
    t = "DimCondicionVenta"
    m = """
let
    Origen = Base,
    Columnas = Table.Distinct(Table.SelectColumns(Origen, {"canal", "medio_pago", "cliente_fidelizado"})),
    Clave = Table.AddColumn(Columnas, "clave_condicion", each [canal] & "|" & [medio_pago] & "|" & [cliente_fidelizado], type text),
    Nombres = Table.RenameColumns(Clave, {{"canal", "Canal"}, {"medio_pago", "Medio de pago"}, {"cliente_fidelizado", "Cliente fidelizado"}})
in
    Nombres
"""
    cols = [columna(t, "clave_condicion", "string", oculta=True),
            columna(t, "Canal", "string"),
            columna(t, "Medio de pago", "string", origen="Medio de pago"),
            columna(t, "Cliente fidelizado", "string", origen="Cliente fidelizado")]
    return tabla_tmdl(t, "\n".join(cols) + "\n" + particion_m(t, m))


def dim_calendario():
    t = "DimCalendario"
    dax = """
VAR PrimeraFecha = MIN ( FactVentas[fecha] )
VAR UltimaFecha = MAX ( FactVentas[fecha] )
VAR Fechas =
    SELECTCOLUMNS (
        CALENDAR ( DATE ( YEAR ( PrimeraFecha ), 1, 1 ), DATE ( YEAR ( UltimaFecha ), 12, 31 ) ),
        "Fecha", [Date]
    )
RETURN
    ADDCOLUMNS (
        Fechas,
        "Año", YEAR ( [Fecha] ),
        "Trimestre", "T" & QUARTER ( [Fecha] ),
        "MesNum", MONTH ( [Fecha] ),
        "Mes", SWITCH ( MONTH ( [Fecha] ),
            1, "Ene", 2, "Feb", 3, "Mar", 4, "Abr", 5, "May", 6, "Jun",
            7, "Jul", 8, "Ago", 9, "Sep", 10, "Oct", 11, "Nov", 12, "Dic" ),
        "AñoMes", FORMAT ( [Fecha], "yyyy-mm" ),
        "EsPeriodoComparable", MONTH ( [Fecha] ) <= MONTH ( UltimaFecha ),
        "TieneDatos", [Fecha] <= UltimaFecha
    )
"""
    cols = [
        columna(t, "Fecha", "dateTime", formato="dd/mm/yyyy", calculada=True, extra=["isKey"]),
        columna(t, "Año", "int64", formato="0", calculada=True),
        columna(t, "Trimestre", "string", calculada=True),
        columna(t, "MesNum", "int64", formato="0", oculta=True, calculada=True),
        columna(t, "Mes", "string", calculada=True, extra=["sortByColumn: MesNum"]),
        columna(t, "AñoMes", "string", calculada=True),
        columna(t, "EsPeriodoComparable", "boolean", calculada=True),
        columna(t, "TieneDatos", "boolean", calculada=True),
    ]
    particion = (f"\tpartition {t} = calculated\n\t\tmode: import\n\t\tsource =\n"
                 f"{indentar(dax, 4)}\n")
    return tabla_tmdl(t, "\n".join(cols) + "\n" + particion, propiedades=["dataCategory: Time"])


MEDIDAS = [
    # (carpeta, nombre, DAX, formato)
    ("1. Ventas", "Ventas Netas", "SUM ( FactVentas[venta_neta_cop] )", MONEDA),
    ("1. Ventas", "Costo Estimado", "SUM ( FactVentas[costo_estimado_cop] )", MONEDA),
    ("1. Ventas", "Lineas de Venta", "COUNTROWS ( FactVentas )", ENTERO),
    ("1. Ventas", "Unidades", "SUM ( FactVentas[unidades] )", ENTERO),
    ("2. Margen", "Margen Estimado", "[Ventas Netas] - [Costo Estimado]", MONEDA),
    ("2. Margen", "Margen Estimado %", "DIVIDE ( [Margen Estimado], [Ventas Netas] )", PCT),
    ("3. Tiempo (Ene-Sep)", "Ventas Ene-Sep",
     "CALCULATE ( [Ventas Netas], KEEPFILTERS ( DimCalendario[EsPeriodoComparable] = TRUE () ) )", MONEDA),
    ("3. Tiempo (Ene-Sep)", "Ventas Ene-Sep Año Anterior",
     "-- Solo con un año en contexto: con varios años la comparación no tiene sentido\n"
     "IF (\n    HASONEVALUE ( DimCalendario[Año] ),\n"
     "    CALCULATE ( [Ventas Ene-Sep], DATEADD ( DimCalendario[Fecha], -1, YEAR ) )\n)", MONEDA),
    ("3. Tiempo (Ene-Sep)", "Variacion Ventas Ene-Sep",
     "VAR Anterior = [Ventas Ene-Sep Año Anterior]\nRETURN\n    IF ( NOT ISBLANK ( Anterior ), [Ventas Ene-Sep] - Anterior )", MONEDA),
    ("3. Tiempo (Ene-Sep)", "Crecimiento Ventas Ene-Sep %",
     "VAR Anterior = [Ventas Ene-Sep Año Anterior]\nRETURN\n    DIVIDE ( [Ventas Ene-Sep] - Anterior, Anterior )", PCT),
    ("3. Tiempo (Ene-Sep)", "Ventas Ene-Sep Hace 2 Años",
     "IF (\n    HASONEVALUE ( DimCalendario[Año] ),\n"
     "    CALCULATE ( [Ventas Ene-Sep], DATEADD ( DimCalendario[Fecha], -2, YEAR ) )\n)", MONEDA),
    ("3. Tiempo (Ene-Sep)", "Crecimiento vs Hace 2 Años %",
     "VAR Base = [Ventas Ene-Sep Hace 2 Años]\nRETURN\n    DIVIDE ( [Ventas Ene-Sep] - Base, Base )", PCT),
    ("3. Tiempo (Ene-Sep)", "Lectura Tendencia",
     "-- Tendencia = mismo signo y > ±2 % frente al año anterior Y frente a hace 2 años\n"
     "VAR A = [Crecimiento Ventas Ene-Sep %]\nVAR B = [Crecimiento vs Hace 2 Años %]\nRETURN\n"
     "    SWITCH (\n        TRUE (),\n        ISBLANK ( A ) || ISBLANK ( B ), BLANK (),\n"
     "        A > 0.02 && B > 0.02, \"Crece (sostenido)\",\n"
     "        A < -0.02 && B < -0.02, \"Cae (sostenido)\",\n"
     "        ABS ( A ) > 0.02, \"Oscila (rebote)\",\n        \"Estable\"\n    )", None),
    ("7. Formato condicional", "Color Crecimiento",
     "-- Verde = crece sostenido, rojo = cae sostenido, naranja = oscila, gris = estable\n"
     "SWITCH (\n    [Lectura Tendencia],\n    \"Crece (sostenido)\", \"#2E7D32\",\n"
     "    \"Cae (sostenido)\", \"#C62828\",\n    \"Oscila (rebote)\", \"#EF8F00\",\n    \"#9E9E9E\"\n)", None),
    ("4. Quiebre", "Lineas con Quiebre", "SUM ( FactVentas[quiebre_flag] )", ENTERO),
    ("4. Quiebre", "% Quiebre", "DIVIDE ( [Lineas con Quiebre], [Lineas de Venta] )", PCT),
    ("4. Quiebre", "Ventas con Quiebre", "CALCULATE ( [Ventas Netas], FactVentas[quiebre_flag] = 1 )", MONEDA),
    ("5. Por linea", "Venta por Linea", "DIVIDE ( [Ventas Netas], [Lineas de Venta] )", MONEDA),
    ("5. Por linea", "Unidades por Linea", "DIVIDE ( [Unidades], [Lineas de Venta] )", "0.00"),
    ("6. Promocion", "Ventas en Promocion",
     'CALCULATE ( [Ventas Netas], DimPromocion[Con promocion] = "Sí" )', MONEDA),
    ("6. Promocion", "% Ventas en Promocion", "DIVIDE ( [Ventas en Promocion], [Ventas Netas] )", PCT),
    ("9. Referencia guia (id_transaccion)", "Transacciones (ID dataset)",
     "DISTINCTCOUNT ( FactVentas[id_transaccion] )", ENTERO),
    ("9. Referencia guia (id_transaccion)", "Ticket Promedio (ID dataset)",
     "-- Valor global fijo: el id_transaccion del dataset sintetico no agrupa compras reales\n"
     "-- (ver docs/01_perfilamiento.md, seccion 5). No se segmenta.\n"
     "CALCULATE (\n    DIVIDE ( [Ventas Netas], [Transacciones (ID dataset)] ),\n    REMOVEFILTERS ()\n)", MONEDA),
]


def medidas():
    t = "_Medidas"
    bloques = []
    for carpeta, nombre, dax, formato in MEDIDAS:
        if "\n" in dax:
            cuerpo = f"\tmeasure {q(nombre)} = ```\n{indentar(dax, 3)}\n\t\t\t```\n"
        else:
            cuerpo = f"\tmeasure {q(nombre)} = {dax}\n"
        if formato:
            cuerpo += f"\t\tformatString: {formato}\n"
        cuerpo += (f"\t\tdisplayFolder: {carpeta}\n"
                   f"\t\tlineageTag: {tag('medida.' + nombre)}\n")
        bloques.append(cuerpo)
    m = """
let
    Fuente = #table(type table [Medidas = text], {})
in
    Fuente
"""
    col = columna(t, "Medidas", "string", oculta=True)
    return tabla_tmdl(t, "\n".join(bloques) + "\n" + col + "\n" + particion_m(t, m))


RELACIONES = [
    ("FactVentas", "fecha", "DimCalendario", "Fecha"),
    ("FactVentas", "ciudad", "DimGeografia", "Ciudad"),
    ("FactVentas", "formato_tienda", "DimFormato", "Formato"),
    ("FactVentas", "categoria", "DimCategoria", "Categoria"),
    ("FactVentas", "promocion", "DimPromocion", "Promocion"),
    ("FactVentas", "clave_condicion", "DimCondicionVenta", "clave_condicion"),
]


def relaciones():
    salida = []
    for ft, fc, tt, tc in RELACIONES:
        salida.append(f"relationship {tag(f'rel.{ft}.{fc}')}\n"
                      f"\tfromColumn: {ft}.{q(fc)}\n"
                      f"\ttoColumn: {tt}.{q(tc)}\n")
    return "\n".join(salida)


# --------------------------------------------------------------------------- main
def ubicar_modelo():
    candidatos = list((RAIZ / "powerbi").glob("*.SemanticModel/definition"))
    if len(candidatos) != 1:
        sys.exit(f"Se esperaba un único *.SemanticModel en powerbi/, encontrados: {candidatos}. "
                 "Cree el proyecto con Power BI Desktop (Guardar como → .pbip).")
    return candidatos[0]


def actualizar_model_tmdl(defin):
    ruta = defin / "model.tmdl"
    texto = ruta.read_text(encoding="utf-8")
    if "__PBI_TimeIntelligenceEnabled" in texto:
        texto = re.sub(r"annotation __PBI_TimeIntelligenceEnabled = \d", "annotation __PBI_TimeIntelligenceEnabled = 0", texto)
    else:
        texto = texto.rstrip("\n") + "\n\nannotation __PBI_TimeIntelligenceEnabled = 0\n"
    faltantes = [t for t in TABLAS_PROPIAS if not re.search(rf"^ref table {re.escape(q(t))}\s*$", texto, re.M)]
    if faltantes:
        texto = texto.rstrip("\n") + "\n\n" + "\n".join(f"ref table {q(t)}" for t in faltantes) + "\n"
    ruta.write_text(texto, encoding="utf-8")


def main():
    defin = ubicar_modelo()
    tablas = defin / "tables"
    tablas.mkdir(exist_ok=True)
    archivos = {
        "FactVentas": fact_ventas(),
        "DimCalendario": dim_calendario(),
        "DimGeografia": dim_geografia(),
        "DimFormato": dim_simple("DimFormato", ["formato_tienda"], [("formato_tienda", "Formato")]),
        "DimCategoria": dim_simple("DimCategoria", ["categoria"], [("categoria", "Categoria")]),
        "DimPromocion": dim_promocion(),
        "DimCondicionVenta": dim_condicion(),
        "_Medidas": medidas(),
    }
    for nombre, contenido in archivos.items():
        (tablas / f"{nombre}.tmdl").write_text(contenido, encoding="utf-8")
    (defin / "expressions.tmdl").write_text(expresiones(), encoding="utf-8")
    (defin / "relationships.tmdl").write_text(relaciones(), encoding="utf-8")
    actualizar_model_tmdl(defin)
    print(f"Modelo escrito en {defin}")
    for f in sorted(defin.rglob("*.tmdl")):
        print("  ", f.relative_to(defin))


if __name__ == "__main__":
    main()
