"""Fases 5–6 — Genera las páginas del dashboard (formato PBIR) en powerbi/*.Report.

Sigue la skill pbi-report-builder: el proyecto lo crea Power BI Desktop, este script solo
agrega páginas y visuales; detecta la versión de esquema de los visuales existentes;
nombres legibles (pg##/v##); valida todo el JSON al final.

Requisito: Power BI Desktop CERRADO.  Uso:  python scripts/pbip/generar_reporte_pbir.py
Diseño y justificación: docs/05_diseno_dashboard.md
"""
from pathlib import Path
import json
import shutil
import sys

RAIZ = Path(__file__).resolve().parents[2]
M = "_Medidas"
sys.stdout.reconfigure(encoding="utf-8")

# ------------------------------------------------------------------ paleta semántica
AZUL = "#1F3A5F"       # identidad / dato principal
AZUL_CLARO = "#8FA8C8"  # comparación (año anterior, hace 2 años)
VERDE = "#2E7D32"      # crecimiento sostenido / positivo
ROJO = "#C62828"       # caída sostenida / alerta
NARANJA = "#EF8F00"    # advertencia (rebote, quiebre)
GRIS = "#9E9E9E"       # neutro / referencia
FONDO = "#F4F6F9"
BORDE = "#DDE2EA"
TEXTO = "#2B2B2B"

W, H = 1920, 1080


# ------------------------------------------------------------------ helpers de expresiones
def lit(v):
    if isinstance(v, bool):
        return {"expr": {"Literal": {"Value": "true" if v else "false"}}}
    if isinstance(v, (int, float)):
        return {"expr": {"Literal": {"Value": f"{v}D"}}}
    return {"expr": {"Literal": {"Value": "'" + str(v).replace("'", "''") + "'"}}}


def color(hex_):
    return {"solid": {"color": lit(hex_)}}


def color_medida(medida):
    return {"solid": {"color": {"expr": {"Measure": {"Expression": {"SourceRef": {"Entity": M}},
                                                      "Property": medida}}}}}


def col(tabla, columna):
    return {"Column": {"Expression": {"SourceRef": {"Entity": tabla}}, "Property": columna}}


def med(medida):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": M}}, "Property": medida}}


def proy(campo, nombre=None):
    tipo = "Measure" if "Measure" in campo else "Column"
    tabla = campo[tipo]["Expression"]["SourceRef"]["Entity"]
    prop = campo[tipo]["Property"]
    p = {"field": campo, "queryRef": f"{tabla}.{prop}", "nativeQueryRef": prop}
    if nombre:
        p["displayName"] = nombre
    return p


def query(**roles):
    return {"queryState": {rol: {"projections": [proy(*c) if isinstance(c, tuple) else proy(c) for c in campos]}
                           for rol, campos in roles.items()}}


def orden(campo, desc=True):
    return {"sort": [{"field": campo, "direction": "Descending" if desc else "Ascending"}]}


# ------------------------------------------------------------------ helpers de visuales
class Pagina:
    def __init__(self, nombre, titulo, subtitulo, oculta=False):
        self.nombre, self.titulo, self.subtitulo, self.oculta = nombre, titulo, subtitulo, oculta
        self.visuales, self.interacciones, self.n = [], [], 0

    def nombre_visual(self, sufijo):
        self.n += 1
        return f"v{self.n:02d}{sufijo}"[:50]

    def agregar(self, sufijo, x, y, w, h, visual, titulo=None, fondo=True, z=None):
        nombre = self.nombre_visual(sufijo)
        vco = {}
        if titulo:
            vco["title"] = [{"properties": {"show": lit(True), "text": lit(titulo),
                                            "fontColor": color(AZUL), "fontSize": lit(13),
                                            "bold": lit(True)}}]
        else:
            vco["title"] = [{"properties": {"show": lit(False)}}]
        vco["subTitle"] = [{"properties": {"show": lit(False)}}]
        if fondo:
            vco["background"] = [{"properties": {"show": lit(True), "color": color("#FFFFFF"),
                                                 "transparency": lit(0)}}]
            vco["border"] = [{"properties": {"show": lit(True), "color": color(BORDE), "radius": lit(8)}}]
        visual.setdefault("visualContainerObjects", {}).update(vco)
        self.visuales.append({"name": nombre,
                              "position": {"x": x, "y": y, "z": z if z is not None else 1000 + self.n,
                                           "height": h, "width": w, "tabOrder": self.n},
                              "visual": visual})
        return nombre


def texto(parrafos):
    """parrafos: lista de listas de (texto, estilo)."""
    return {"visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": [
        {"textRuns": [{"value": t, "textStyle": e} for t, e in runs]} for runs in parrafos]}}]}}


def estilo(tam=12, negrita=False, col_=TEXTO):
    e = {"fontSize": f"{tam}pt", "color": col_}
    if negrita:
        e["fontWeight"] = "bold"
    return e


def tarjeta(medida, etiqueta, col_valor=AZUL):
    return {"visualType": "card", "query": query(Values=[(med(medida), etiqueta)]),
            "objects": {"labels": [{"properties": {"color": color(col_valor), "fontSize": lit(26)}}],
                        "categoryLabels": [{"properties": {"show": lit(True), "color": color(TEXTO),
                                                           "fontSize": lit(11)}}]}}


def segmentador(tabla, columna, unico=False, anio_2026=False):
    v = {"visualType": "slicer", "query": query(Values=[col(tabla, columna)]),
         "objects": {"data": [{"properties": {"mode": lit("Dropdown")}}],
                     "selection": [{"properties": {"strictSingleSelect": lit(unico),
                                                   "selectAllCheckboxEnabled": lit(not unico)}}],
                     "header": [{"properties": {"show": lit(True), "fontColor": color(AZUL),
                                                "textSize": lit(11)}}]},
         "syncGroup": {"groupName": columna, "fieldChanges": True, "filterChanges": True}}
    if anio_2026:
        v["objects"]["general"] = [{"properties": {"filter": {"filter": {
            "Version": 2,
            "From": [{"Name": "d", "Entity": tabla, "Type": 0}],
            "Where": [{"Condition": {"In": {
                "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": columna}}],
                "Values": [[{"Literal": {"Value": "2026L"}}]]}}}]}}}}]
    return v


def barras(categoria, medidas, tipo="clusteredBarChart", color_cond=None, colores=None,
           ordenar=None, etiquetas=True, tooltips=()):
    roles = {"Category": [categoria], "Y": medidas}
    if tooltips:
        roles["Tooltips"] = list(tooltips)
    v = {"visualType": tipo, "query": query(**roles), "objects": {}}
    if ordenar is not None:
        v["query"]["sortDefinition"] = orden(ordenar)
    if color_cond:
        v["objects"]["dataPoint"] = [{"properties": {"fill": color_medida(color_cond)},
                                      "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}}]
    elif colores and len(colores) == 1:
        # Una sola medida: el color se aplica a toda la serie (sin selector).
        v["objects"]["dataPoint"] = [{"properties": {"fill": color(colores[0][1])}}]
    elif colores:
        v["objects"]["dataPoint"] = [{"properties": {"fill": color(c)},
                                      "selector": {"metadata": f"{M}.{m}"}} for m, c in colores]
    if etiquetas:
        v["objects"]["labels"] = [{"properties": {"show": lit(True), "fontSize": lit(9)}}]
    v["objects"]["legend"] = [{"properties": {"show": lit(len(medidas) > 1), "position": lit("Top")}}]
    return v


def matriz(filas, valores, columnas=None, color_valores=None, modo="fontColor"):
    roles = {"Rows": filas, "Values": valores}
    if columnas:
        roles["Columns"] = columnas
    v = {"visualType": "pivotTable", "query": query(**roles), "objects": {
        "columnHeaders": [{"properties": {"fontColor": color("#FFFFFF"), "backColor": color(AZUL),
                                          "fontSize": lit(10)}}],
        "rowHeaders": [{"properties": {"fontSize": lit(10)}}],
        "values": [{"properties": {"fontSize": lit(10)}}]}}
    for medida in color_valores or []:
        v["objects"]["values"].append({
            "properties": {modo: color_medida("Color Crecimiento")},
            "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": f"{M}.{medida}"}})
    return v


def colores_serie(campo, valores_colores):
    """Color fijo por valor de la serie (p. ej. Año 2026 = azul de identidad)."""
    return [{"properties": {"fill": color(c)},
             "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": campo,
                                                               "Right": {"Literal": {"Value": valor}}}}}]}}
            for valor, c in valores_colores]


def lineas(eje, medidas, serie=None, colores=None, colores_por_serie=None):
    roles = {"Category": [eje], "Y": medidas}
    if serie:
        roles["Series"] = [serie]
    v = {"visualType": "lineChart", "query": query(**roles), "objects": {
        "legend": [{"properties": {"show": lit(True), "position": lit("Top")}}]}}
    if colores_por_serie:
        v["objects"]["dataPoint"] = colores_serie(serie, colores_por_serie)
    elif colores:
        v["objects"]["dataPoint"] = [{"properties": {"fill": color(colores[0][1])}}]
    return v


COLORES_ANIO = [("2024L", "#C4CCD6"), ("2025L", AZUL_CLARO), ("2026L", AZUL)]
COLORES_CANAL = [("'Tienda física'", AZUL), ("'Domicilio'", AZUL_CLARO), ("'Click & Collect'", GRIS)]


def navegador():
    return {"visualType": "pageNavigator", "objects": {}}


# ------------------------------------------------------------------ estructura común
SLICERS = [("DimCalendario", "Año", True, True), ("DimGeografia", "Region", False, False),
           ("DimFormato", "Formato", False, False), ("DimCategoria", "Categoria", False, False)]


def encabezado(p, slicers=True):
    p.agregar("Banda", 0, 0, W, 96, texto([[(" ", estilo(8, False, AZUL))]]), fondo=False, z=50)
    p.visuales[-1]["visual"]["visualContainerObjects"]["background"] = [
        {"properties": {"show": lit(True), "color": color(AZUL), "transparency": lit(0)}}]
    p.agregar("Titulo", 0, 0, 1310, 96, texto([
        [(p.titulo, estilo(20, True, "#FFFFFF"))],
        [(p.subtitulo, estilo(10, False, "#DCE4EF"))]]), fondo=False, z=100)
    p.agregar("Navegador", 1320, 24, 580, 48, navegador(), fondo=False, z=200)
    nombres = []
    if slicers:
        for i, (t, c, unico, anio) in enumerate(SLICERS):
            etiqueta = {"Region": "Región", "Categoria": "Categoría"}.get(c, c)
            v = segmentador(t, c, unico, anio)
            v["query"]["queryState"]["Values"]["projections"][0]["displayName"] = etiqueta
            nombres.append(p.agregar("Seg" + c.replace("ñ", "n"), 24 + i * 300, 108, 284, 64, v, z=500 + i))
    return nombres


def sin_filtro(p, origen, destinos):
    for d in destinos:
        p.interacciones.append({"source": origen, "target": d, "type": "NoFilter"})


# ------------------------------------------------------------------ páginas
def pagina_resumen():
    p = Pagina("pg01Resumen", "Resumen ejecutivo — ¿Cómo está el negocio y dónde mirar primero?",
               "Gerencia de tiendas y de categoría · Datos 01/01/2024–30/09/2026 · "
               "Crecimientos comparan ene–sep contra ene–sep (2026 es parcial)")
    seg = encabezado(p)
    kpis = [("Ventas Ene-Sep", "Ventas netas (ene–sep del año)", AZUL),
            ("Crecimiento Ventas Ene-Sep %", "Crecimiento vs año anterior", AZUL),
            ("Margen Estimado %", "Margen estimado %", AZUL),
            ("% Quiebre", "% líneas con quiebre de stock", NARANJA),
            ("Venta por Linea", "Venta promedio por línea", AZUL)]
    for i, (m_, e, c) in enumerate(kpis):
        p.agregar("Kpi" + m_.replace(" ", "").replace("%", "Pct").replace("-", "")[:20],
                  24 + i * 318, 186, 302, 130, tarjeta(m_, e, c))
    ticket = tarjeta("Ticket Promedio (ID dataset)", "Ticket según ID del dataset (referencia global ⓘ)", GRIS)
    ticket["objects"]["labels"][0]["properties"]["fontSize"] = lit(18)
    p.agregar("KpiTicketReferencia", 1614, 186, 282, 130, ticket)

    anios = p.agregar("ColVentasPorAnio", 24, 332, 620, 330,
                      barras(col("DimCalendario", "Año"), [(med("Ventas Ene-Sep"), "Ventas ene–sep")],
                             tipo="clusteredColumnChart", colores=[("Ventas Ene-Sep", AZUL)]),
                      titulo="Ventas ene–sep por año: el total está plano (+0,9 %)")
    mensual = p.agregar("LineaEstacionalidad", 660, 332, 1236, 330,
                        lineas(col("DimCalendario", "Mes"), [(med("Ventas Netas"), "Ventas")],
                               serie=col("DimCalendario", "Año"), colores_por_serie=COLORES_ANIO),
                        titulo="Ventas mensuales por año (el mismo mes se compara entre años)")
    sin_filtro(p, seg[0], [anios, mensual])
    p.agregar("BarCrecRegion", 24, 678, 620, 382,
              barras(col("DimGeografia", "Region"),
                     [(med("Crecimiento Ventas Ene-Sep %"), "Crecimiento vs año anterior")],
                     color_cond="Color Crecimiento", ordenar=med("Crecimiento Ventas Ene-Sep %"),
                     tooltips=[(med("Crecimiento vs Hace 2 Años %"), "Crecimiento vs hace 2 años"),
                               (med("Lectura Tendencia"), "Lectura")]),
              titulo="Crecimiento por región (verde/rojo = sostenido, naranja = rebote)")
    p.agregar("BarCrecCategoria", 660, 678, 620, 382,
              barras(col("DimCategoria", "Categoria"),
                     [(med("Crecimiento Ventas Ene-Sep %"), "Crecimiento vs año anterior")],
                     color_cond="Color Crecimiento", ordenar=med("Crecimiento Ventas Ene-Sep %"),
                     tooltips=[(med("Crecimiento vs Hace 2 Años %"), "Crecimiento vs hace 2 años"),
                               (med("Lectura Tendencia"), "Lectura")]),
              titulo="Crecimiento por categoría")
    p.agregar("TxtHallazgos", 1296, 678, 600, 382, texto([
        [("Dónde mirar primero (2026 vs 2025 y 2024)", estilo(14, True, AZUL))],
        [("▲ ", estilo(12, True, VERDE)), ("Eje Cafetero y Orinoquía crecen de forma sostenida.", estilo(11))],
        [("▼ ", estilo(12, True, ROJO)), ("Nororiente cae de forma sostenida (Bucaramanga, y Cartagena en Caribe).", estilo(11))],
        [("▲ ", estilo(12, True, VERDE)), ("Abarrotes es la única categoría que crece sostenido (+9,1 %).", estilo(11))],
        [("● ", estilo(12, True, GRIS)), ("El margen estimado es igual en todos los grupos (≈27,5 %).", estilo(11))],
        [("● ", estilo(12, True, NARANJA)), ("El quiebre (~8 %) es parejo y estable: problema de toda la cadena.", estilo(11))],
        [("Colores: verde = crece sostenido · rojo = cae sostenido · naranja = rebote/advertencia · gris = estable o referencia.", estilo(9, False, GRIS))]]))
    return p


def pagina_comercial():
    p = Pagina("pg02Comercial", "Desempeño comercial — ¿Qué regiones, ciudades, formatos y categorías explican el resultado?",
               "Seleccione una región o categoría para filtrar los demás gráficos · "
               "Tendencia = mismo signo frente a 2025 y a 2024")
    encabezado(p)
    p.agregar("MatGeografia", 24, 186, 930, 440,
              matriz([col("DimGeografia", "Region"), col("DimGeografia", "Ciudad")],
                     [(med("Ventas Ene-Sep"), "Ventas ene–sep"),
                      (med("Variacion Ventas Ene-Sep"), "Variación $ vs año ant."),
                      (med("Crecimiento Ventas Ene-Sep %"), "Crec. vs año ant."),
                      (med("Crecimiento vs Hace 2 Años %"), "Crec. vs hace 2 años"),
                      (med("Lectura Tendencia"), "Lectura")],
                     color_valores=["Crecimiento Ventas Ene-Sep %", "Crecimiento vs Hace 2 Años %",
                                    "Lectura Tendencia"]),
              titulo="Región → ciudad (expanda con +): ventas y crecimiento")
    p.agregar("MatRegionFormato", 970, 186, 926, 440,
              matriz([col("DimGeografia", "Region")],
                     [(med("Crecimiento Ventas Ene-Sep %"), "Crec. vs año ant.")],
                     columnas=[col("DimFormato", "Formato")],
                     color_valores=["Crecimiento Ventas Ene-Sep %"], modo="backColor"),
              titulo="Región × formato: crecimiento (fondo verde/rojo = sostenido, naranja = rebote)")
    p.agregar("BarCategoriaDosComp", 24, 642, 930, 418,
              barras(col("DimCategoria", "Categoria"),
                     [(med("Crecimiento Ventas Ene-Sep %"), "vs año anterior"),
                      (med("Crecimiento vs Hace 2 Años %"), "vs hace 2 años")],
                     colores=[("Crecimiento Ventas Ene-Sep %", AZUL), ("Crecimiento vs Hace 2 Años %", AZUL_CLARO)],
                     ordenar=med("Crecimiento Ventas Ene-Sep %")),
              titulo="Categorías: crecimiento frente a dos años base (solo Abarrotes crece en ambos)")
    p.agregar("BarVariacionCiudad", 970, 642, 926, 418,
              barras(col("DimGeografia", "Ciudad"), [(med("Variacion Ventas Ene-Sep"), "Variación $ vs año ant.")],
                     color_cond="Color Crecimiento", ordenar=med("Variacion Ventas Ene-Sep"),
                     tooltips=[(med("Crecimiento Ventas Ene-Sep %"), "Crec. vs año ant."),
                               (med("Crecimiento vs Hace 2 Años %"), "Crec. vs hace 2 años")]),
              titulo="Aporte en $ de cada ciudad a la variación (color = lectura de tendencia)")
    return p


def pagina_promociones():
    p = Pagina("pg03Promociones", "Promociones, clientes y canales — ¿Qué palancas comerciales muestran oportunidades?",
               "El margen estimado no cambia entre grupos: las oportunidades están en el volumen y el crecimiento")
    encabezado(p)
    kpis = [("% Ventas en Promocion", "% de las ventas con promoción"),
            ("Margen Estimado %", "Margen estimado % (igual en todos los grupos)"),
            ("Unidades por Linea", "Unidades por línea")]
    for i, (m_, e) in enumerate(kpis):
        p.agregar("Kpi" + str(i + 1), 24 + i * 300, 186, 284, 120, tarjeta(m_, e))
    p.agregar("TxtLectura", 924, 186, 972, 120, texto([
        [("Lectura: ", estilo(12, True, AZUL)),
         ("“Puntos dobles” cae de forma sostenida (−7,1 % vs 2025; −8,2 % vs 2024). "
          "El crecimiento de Domicilio es un rebote (cayó en 2025). Fidelización y medio de pago no muestran diferencias.",
          estilo(11))]]))
    p.agregar("BarPromocion", 24, 322, 930, 360,
              barras(col("DimPromocion", "Promocion"),
                     [(med("Crecimiento Ventas Ene-Sep %"), "Crecimiento vs año anterior")],
                     color_cond="Color Crecimiento", ordenar=med("Crecimiento Ventas Ene-Sep %"),
                     tooltips=[(med("Crecimiento vs Hace 2 Años %"), "Crec. vs hace 2 años"),
                               (med("Ventas Ene-Sep"), "Ventas ene–sep")]),
              titulo="Crecimiento por tipo de promoción")
    p.agregar("ColMixCanalFormato", 970, 322, 926, 360,
              {"visualType": "hundredPercentStackedColumnChart",
               "query": query(Category=[col("DimFormato", "Formato")], Y=[(med("Ventas Ene-Sep"), "Ventas")],
                              Series=[col("DimCondicionVenta", "Canal")]),
               "objects": {"legend": [{"properties": {"show": lit(True), "position": lit("Top")}}],
                           "labels": [{"properties": {"show": lit(True), "fontSize": lit(9)}}],
                           "dataPoint": colores_serie(col("DimCondicionVenta", "Canal"), COLORES_CANAL)}},
              titulo="Mezcla de canales por formato (% de ventas)")
    p.agregar("BarCanal", 24, 698, 618, 362,
              barras(col("DimCondicionVenta", "Canal"),
                     [(med("Crecimiento Ventas Ene-Sep %"), "vs año anterior"),
                      (med("Crecimiento vs Hace 2 Años %"), "vs hace 2 años")],
                     colores=[("Crecimiento Ventas Ene-Sep %", AZUL), ("Crecimiento vs Hace 2 Años %", AZUL_CLARO)]),
              titulo="Canales: crecimiento frente a dos años base")
    p.agregar("BarFidelizacion", 658, 698, 618, 362,
              barras(col("DimCondicionVenta", "Cliente fidelizado"),
                     [(med("Venta por Linea"), "Venta por línea")], tipo="clusteredColumnChart",
                     colores=[("Venta por Linea", GRIS)],
                     tooltips=[(med("Ventas Ene-Sep"), "Ventas ene–sep"),
                               (med("Margen Estimado %"), "Margen estimado %")]),
              titulo="Fidelizados vs no fidelizados: misma venta por línea")
    p.agregar("BarMedioPago", 1292, 698, 604, 362,
              barras(col("DimCondicionVenta", "Medio de pago"), [(med("Ventas Ene-Sep"), "Ventas ene–sep")],
                     colores=[("Ventas Ene-Sep", AZUL)], ordenar=med("Ventas Ene-Sep"),
                     tooltips=[(med("Crecimiento Ventas Ene-Sep %"), "Crec. vs año ant.")]),
              titulo="Ventas por medio de pago")
    return p


def pagina_disponibilidad():
    p = Pagina("pg04Disponibilidad", "Disponibilidad — ¿Dónde los quiebres de stock requieren atención?",
               "Quiebre = la línea se vendió con quiebre de stock en los últimos 7 días (no mide ventas perdidas)")
    seg = encabezado(p)
    kpis = [("% Quiebre", "% líneas con quiebre", NARANJA),
            ("Lineas con Quiebre", "Líneas con quiebre", AZUL),
            ("Ventas con Quiebre", "Ventas registradas con quiebre", AZUL)]
    for i, (m_, e, c) in enumerate(kpis):
        p.agregar("Kpi" + str(i + 1), 24 + i * 300, 186, 284, 120, tarjeta(m_, e, c))
    p.agregar("TxtLectura", 924, 186, 972, 120, texto([
        [("Lectura: ", estilo(12, True, AZUL)),
         ("el quiebre es parejo (~8 %) en categorías, formatos y ciudades: ninguna diferencia es estadísticamente "
          "significativa y es estable en el tiempo. Es un problema de toda la cadena; se prioriza por volumen afectado.",
          estilo(11))]]))
    tendencia = lineas(col("DimCalendario", "AñoMes"), [(med("% Quiebre"), "% quiebre")],
                       colores=[("% Quiebre", NARANJA)])
    linea = p.agregar("LineaQuiebreMes", 24, 322, 1872, 300, tendencia,
                      titulo="% de quiebre por mes, 2024–2026 (historia completa; no responde al filtro de año): "
                             "estable alrededor de 8 %, sin mejora")
    sin_filtro(p, seg[0], [linea])
    p.agregar("BarVentasQuiebreCiudad", 24, 638, 618, 422,
              barras(col("DimGeografia", "Ciudad"), [(med("Ventas con Quiebre"), "Ventas con quiebre")],
                     colores=[("Ventas con Quiebre", AZUL)], ordenar=med("Ventas con Quiebre"),
                     tooltips=[(med("% Quiebre"), "% quiebre"), (med("Lineas con Quiebre"), "Líneas")]),
              titulo="Volumen afectado por ciudad (dónde priorizar reposición)")
    p.agregar("BarVentasQuiebreCategoria", 658, 638, 618, 422,
              barras(col("DimCategoria", "Categoria"), [(med("Ventas con Quiebre"), "Ventas con quiebre")],
                     colores=[("Ventas con Quiebre", AZUL)], ordenar=med("Ventas con Quiebre"),
                     tooltips=[(med("% Quiebre"), "% quiebre"), (med("Lineas con Quiebre"), "Líneas")]),
              titulo="Volumen afectado por categoría")
    p.agregar("MatQuiebreCatFormato", 1292, 638, 604, 422,
              matriz([col("DimCategoria", "Categoria")], [(med("% Quiebre"), "% quiebre")],
                     columnas=[col("DimFormato", "Formato")]),
              titulo="% quiebre categoría × formato (diferencias no significativas)")
    return p


def pagina_conclusiones():
    p = Pagina("pg05Conclusiones", "Conclusiones y decisiones para la gerencia",
               "Síntesis de los hallazgos validados (docs/04_matriz_hallazgos.md)")
    encabezado(p, slicers=False)
    filas = [
        (VERDE, "1. Replicar lo que funciona", "Eje Cafetero y Orinoquía crecen frente a 2025 y 2024; "
         "Eje Cafetero–Hipermercado y Suroccidente–Supermercado lideran por formato.", "Gerencia de tiendas"),
        (ROJO, "2. Plan de recuperación", "Nororiente (Bucaramanga) y Cartagena caen de forma sostenida; "
         "Nororiente–Supermercado, Caribe–Express y Centro–Express son las combinaciones críticas.", "Gerencia de tiendas"),
        (VERDE, "3. Impulsar Abarrotes", "Única categoría con crecimiento sostenido (+9,1 %) y mayor aporte "
         "en pesos (+$5,7 M). Las demás categorías están estables.", "Gerencia de categoría"),
        (NARANJA, "4. Revisar “Puntos dobles”", "Cae de forma sostenida (−7,1 % y −8,2 %). Evaluar reasignar "
         "esa inversión promocional.", "Gerencia de categoría"),
        (GRIS, "5. Gestionar volumen, no margen", "El margen estimado es ≈27,5 % en todos los grupos: "
         "las palancas comerciales no cambian la rentabilidad.", "Ambas"),
        (NARANJA, "6. Reposición para toda la cadena", "El quiebre (~8 %) es parejo y estable: no hay focos "
         "aislados. Priorizar por volumen afectado (Bogotá y Carnes).", "Operaciones"),
    ]
    for i, (c, t, d, quien) in enumerate(filas):
        x = 24 + (i % 2) * 944
        y = 120 + (i // 2) * 180
        p.agregar(f"TxtConclusion{i + 1}", x, y, 928, 164, texto([
            [("■ ", estilo(18, True, c)), (t, estilo(16, True, AZUL))],
            [(d, estilo(12))],
            [("Responsable: " + quien, estilo(10, False, GRIS))]]))
    return p


def pagina_validacion():
    p = Pagina("pg99Validacion", "Validación técnica — cifras de control contra el CSV",
               "Valores esperados: scripts/validacion/01_perfilamiento.py y docs/03_modelo.md", oculta=True)
    encabezado(p, slicers=False)
    medidas_ctrl = ["Ventas Netas", "Costo Estimado", "Margen Estimado", "Margen Estimado %", "Lineas de Venta",
                    "Unidades", "Lineas con Quiebre", "% Quiebre", "Ventas con Quiebre", "Ventas en Promocion",
                    "% Ventas en Promocion", "Venta por Linea", "Transacciones (ID dataset)",
                    "Ticket Promedio (ID dataset)"]
    p.agregar("TablaTotales", 24, 120, 1872, 160,
              {"visualType": "tableEx", "query": query(Values=[med(m_) for m_ in medidas_ctrl])},
              titulo="Totales (esperado: 1.560.062.403 · 1.131.389.400 · 428.673.003 · 27,48 % · 60.000 · "
                     "121.393 · 4.849 · 8,08 % · 126.858.302 · 618.958.563 · 39,68 % · 26.001 · 21.264 · 73.366)")
    p.agregar("TablaAnios", 24, 296, 930, 300,
              {"visualType": "tableEx", "query": query(Values=[
                  col("DimCalendario", "Año"), med("Ventas Ene-Sep"), med("Ventas Ene-Sep Año Anterior"),
                  med("Crecimiento Ventas Ene-Sep %"), med("Crecimiento vs Hace 2 Años %")])},
              titulo="Por año (esperado ene–sep: 425.113.135 · 424.805.507 · 428.753.035; 2026: +0,93 %)")
    p.agregar("TablaRegion", 970, 296, 926, 300,
              {"visualType": "tableEx", "query": query(Values=[
                  col("DimGeografia", "Region"), med("Venta por Linea"), med("Ticket Promedio (ID dataset)"),
                  med("Lineas de Venta")])},
              titulo="Por región (el ticket NO debe cambiar; Centro venta/línea = 25.980)")
    return p


# ------------------------------------------------------------------ escritura
def esquema_visual(defin):
    for f in defin.glob("pages/*/visuals/*/visual.json"):
        s = json.loads(f.read_text(encoding="utf-8")).get("$schema")
        if s:
            return s
    return "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.0.0/schema.json"


def esquema_pagina(defin):
    for f in defin.glob("pages/*/page.json"):
        s = json.loads(f.read_text(encoding="utf-8")).get("$schema")
        if s:
            return s
    return "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json"


def escribir(defin, paginas):
    sv, sp = esquema_visual(defin), esquema_pagina(defin)
    pages_dir = defin / "pages"
    # Se reemplazan las páginas que genera este script y la página de muestra inicial.
    for d in pages_dir.iterdir():
        if d.is_dir():
            shutil.rmtree(d)
    for p in paginas:
        pdir = pages_dir / p.nombre
        (pdir / "visuals").mkdir(parents=True)
        page = {"$schema": sp, "name": p.nombre, "displayName": p.titulo.split(" — ")[0],
                "displayOption": "FitToPage", "height": H, "width": W,
                "objects": {"background": [{"properties": {"color": color(FONDO), "transparency": lit(0)}}]}}
        if p.oculta:
            page["visibility"] = "HiddenInViewMode"
        if p.interacciones:
            page["visualInteractions"] = p.interacciones
        (pdir / "page.json").write_text(json.dumps(page, ensure_ascii=False, indent=2), encoding="utf-8")
        for v in p.visuales:
            vdir = pdir / "visuals" / v["name"]
            vdir.mkdir()
            (vdir / "visual.json").write_text(json.dumps({"$schema": sv, **v}, ensure_ascii=False, indent=2),
                                              encoding="utf-8")
    meta = {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
            "pageOrder": [p.nombre for p in paginas], "activePageName": paginas[0].nombre}
    (pages_dir / "pages.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def validar(defin):
    ok = True
    for f in defin.rglob("*.json"):
        try:
            json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print("JSON INVÁLIDO:", f, e)
            ok = False
    return ok


def main():
    reportes = list((RAIZ / "powerbi").glob("*.Report/definition"))
    if len(reportes) != 1:
        sys.exit(f"Se esperaba un único *.Report en powerbi/, encontrados: {reportes}")
    defin = reportes[0]
    paginas = [pagina_resumen(), pagina_comercial(), pagina_promociones(),
               pagina_disponibilidad(), pagina_conclusiones(), pagina_validacion()]
    escribir(defin, paginas)
    total = sum(len(p.visuales) for p in paginas)
    print(f"{len(paginas)} páginas y {total} visuales escritos en {defin}")
    print("✓ JSON válido" if validar(defin) else "✗ Hay JSON inválido")


if __name__ == "__main__":
    main()
