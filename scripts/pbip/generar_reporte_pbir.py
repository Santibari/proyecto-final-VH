"""Fases 5–6 — Genera las páginas del dashboard (formato PBIR) en powerbi/*.Report.

Sigue la skill pbi-report-builder: el proyecto lo crea Power BI Desktop, este script solo
agrega páginas y visuales; detecta la versión de esquema de los visuales existentes;
nombres legibles (pg##/v##); valida todo el JSON al final.

Requisito: Power BI Desktop CERRADO.  Uso:  python scripts/pbip/generar_reporte_pbir.py
Diseño "tiquete + editorial" (skill dashboard-design-studio): papel cálido, azul petróleo, titulares en
serif, cifras tipo caja registradora. Fondos: scripts/pbip/recursos/fondos.py (requiere playwright).
Medidas SVG animadas (podio, tabla de posiciones, KPI, tiquete): scripts/pbip/medidas_diseno.py.
Diseño y justificación: docs/05_diseno_dashboard.md
"""
from pathlib import Path
import json
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import medidas_diseno  # noqa: E402  (tamaños de los SVG: tiquete, KPI)

RAIZ = Path(__file__).resolve().parents[2]
M = "_Medidas"
sys.stdout.reconfigure(encoding="utf-8")

# ------------------------------------------------------------------ paleta semántica
# Validada con .claude/skills/dashboard-design-studio/scripts/paleta.py sobre el papel #F5F0E6
AZUL = "#0E4D64"        # identidad (azul petróleo): dato principal, 2026, encabezados
AZUL_CLARO = "#5E7F8C"  # comparación (año anterior, hace 2 años)
COMP2 = "#C9C2B3"       # comparación lejana (hace 2 años en series)
# Semáforo sin verde ni rojo: tonos de la misma familia del papel y la tinta.
VERDE = "#0E4D64"       # crece sostenido → azul petróleo (identidad)
ROJO = "#9A4A2C"        # cae sostenido → terracota
NARANJA = "#A87B22"     # oscila / rebote / quiebre → ocre
GRIS = "#7D858C"        # neutro / referencia
FONDO = "#F5F0E6"       # papel
TARJETA = "#FFFDF8"     # superficie de las tarjetas
BORDE = "#E2DACB"
TEXTO = "#1E2B2F"       # tinta
SEC = "#5B6770"         # texto secundario
SERIF, MONO, SEMI = "Cambria", "Consolas", "Segoe UI Semibold"

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
    def __init__(self, nombre, titulo, subtitulo, oculta=False, nombre_visible=None, fondo_imagen=None,
                 kicker=None, reescalar=False, tamano=(W, H), tooltip=False):
        self.nombre, self.titulo, self.subtitulo, self.oculta = nombre, titulo, subtitulo, oculta
        self.tamano, self.tooltip = tamano, tooltip  # tooltip = página de información sobre herramientas
        self.nombre_visible = nombre_visible or titulo.split(" — ")[0]
        self.fondo_imagen = fondo_imagen  # archivo en scripts/pbip/recursos/ (se registra en el reporte)
        self.kicker = kicker
        # Las páginas internas se diseñaron con margen de 24 px; se llevan a la retícula de 12 columnas
        # (margen 60, ancho útil 1800) sin tocar las alturas.
        self.reescalar = reescalar
        self.visuales, self.interacciones, self.n = [], [], 0
        self.reglas = []  # (x, y, ancho) de las reglas finas sobre cada bloque, se dibujan en el fondo

    def nombre_visual(self, sufijo):
        self.n += 1
        return f"v{self.n:02d}{sufijo}"[:50]

    def agregar(self, sufijo, x, y, w, h, visual, titulo=None, fondo=True, z=None, escalar=True):
        if self.reescalar and escalar:
            k = 1800 / 1872
            x, w = round(60 + (x - 24) * k), round(w * k)
        nombre = self.nombre_visual(sufijo)
        vco = {}
        if titulo:
            vco["title"] = [{"properties": {"show": lit(True), "text": lit(titulo),
                                            "fontColor": color(TEXTO), "fontSize": lit(12),
                                            "fontFamily": lit(SEMI), "bold": lit(False)}}]
        else:
            vco["title"] = [{"properties": {"show": lit(False)}}]
        vco["subTitle"] = [{"properties": {"show": lit(False)}}]
        # Ningún visual tiene fondo propio: todos comparten el papel de la página. Los bloques ("fondo=True")
        # se separan con una regla fina en la imagen de fondo, al estilo editorial.
        if fondo:
            self.reglas.append((x, y, w))
        vco["background"] = [{"properties": {"show": lit(False)}}]
        vco["border"] = [{"properties": {"show": lit(False)}}]
        # Solo los gráficos se separan de la regla; los textos con relleno superior mostraban barra de desplazamiento.
        arriba = 0 if visual.get("visualType") in ("textbox", "actionButton", "image") else 10
        vco["padding"] = [{"properties": {"top": lit(arriba), "left": lit(0), "right": lit(4), "bottom": lit(0 if arriba == 0 else 4)}}]
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


def estilo(tam=12, negrita=False, col_=TEXTO, fuente=None):
    e = {"fontSize": f"{tam}pt", "color": col_}
    if negrita:
        e["fontWeight"] = "bold"
    if fuente:
        e["fontFamily"] = fuente
    return e


def etiqueta(t, col_=SEC, tam=9.5):
    """Etiqueta editorial en versalitas (el espaciado se imita con espacios finos)."""
    return (t.upper(), estilo(tam, True, col_))


def tarjeta(medida, etiqueta_, col_valor=TEXTO):
    return {"visualType": "card", "query": query(Values=[(med(medida), etiqueta_)]),
            "objects": {"labels": [{"properties": {"color": color(col_valor), "fontSize": lit(28),
                                                   "fontFamily": lit(MONO)}}],
                        "categoryLabels": [{"properties": {"show": lit(True), "color": color(SEC),
                                                           "fontSize": lit(10)}}]}}


def segmentador(tabla, columna, unico=False, anio_2026=False):
    v = {"visualType": "slicer", "query": query(Values=[col(tabla, columna)]),
         "objects": {"data": [{"properties": {"mode": lit("Dropdown")}}],
                     "selection": [{"properties": {"strictSingleSelect": lit(unico),
                                                   "selectAllCheckboxEnabled": lit(not unico)}}],
                     "header": [{"properties": {"show": lit(True), "fontColor": color(SEC),
                                                "textSize": lit(9), "bold": lit(True)}}],
                     "items": [{"properties": {"fontColor": color(TEXTO), "textSize": lit(11),
                                               "background": color(TARJETA)}}]},
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


def matriz(filas, valores, columnas=None, color_valores=None, modo="fontColor", tam=10, relleno=None):
    """tam/relleno: las matrices pequeñas (pocas filas) se agrandan para ocupar su bloque y leerse de lejos."""
    roles = {"Rows": filas, "Values": valores}
    if columnas:
        roles["Columns"] = columnas
    v = {"visualType": "pivotTable", "query": query(**roles), "objects": estilo_tabla(tam=tam)}
    if relleno is not None:
        v["objects"]["grid"][0]["properties"]["rowPadding"] = lit(relleno)
    if modo == "backColor":
        v["objects"]["values"][0]["properties"]["fontColorPrimary"] = color("#FFFFFF")
        v["objects"]["values"][0]["properties"]["fontColorSecondary"] = color("#FFFFFF")
    for medida in color_valores or []:
        v["objects"]["values"].append({
            "properties": {modo: color_medida("Color Crecimiento")},
            "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": f"{M}.{medida}"}})
    return v


def estilo_tabla(texto_celdas=TEXTO, tam=10):
    """Tablas y matrices sobre el papel: encabezado en tinta sobre papel con regla, filas sin rayas blancas."""
    return {
        "columnHeaders": [{"properties": {"fontColor": color(TEXTO), "backColor": color(FONDO), "fontSize": lit(tam),
                                          "fontFamily": lit(SEMI), "outlineStyle": lit(2)}}],
        "rowHeaders": [{"properties": {"fontColor": color(TEXTO), "backColor": color(FONDO), "fontSize": lit(tam)}}],
        "values": [{"properties": {"fontSize": lit(tam), "fontColorPrimary": color(texto_celdas),
                                   "fontColorSecondary": color(texto_celdas),
                                   "backColorPrimary": color(FONDO), "backColorSecondary": color(FONDO)}}],
        "grid": [{"properties": {"gridHorizontal": lit(True), "gridHorizontalColor": color(BORDE),
                                 "gridVertical": lit(False), "outlineColor": color(TEXTO)}}],
        "subTotals": [{"properties": {"backColor": color(FONDO), "fontColor": color(TEXTO)}}],
        "total": [{"properties": {"backColor": color(FONDO), "fontColor": color(TEXTO)}}],
    }


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
        # En los gráficos de líneas el color de una medida necesita el selector de metadatos
        v["objects"]["dataPoint"] = [{"properties": {"fill": color(c)}, "selector": {"metadata": f"{M}.{m}"}}
                                     for m, c in colores]
    return v


COLORES_ANIO = [("2024L", COMP2), ("2025L", AZUL_CLARO), ("2026L", AZUL)]
COLORES_CANAL = [("'Tienda física'", AZUL), ("'Domicilio'", AZUL_CLARO), ("'Click & Collect'", COMP2)]


def imagen_svg(medida):
    """Visual de imagen cuyo origen es una medida SVG (categoría ImageUrl), ajustada a la caja del visual.

    Se usa el visual de imagen y no una tabla: en las tablas la imagen no puede pasar de 512 px de ancho."""
    return {"visualType": "image", "objects": {"image": [{"properties": {
        "sourceType": lit("imageData"),
        "sourceField": {"expr": med(medida)}}}]}}


def agregar_svg(p, sufijo, x, y, w, h, medida, fondo_celda=None):
    """Ubica la imagen SVG exactamente en la caja (x, y, w, h); la caja tiene la misma proporción que el SVG."""
    return p.agregar(sufijo, x, y, w, h, imagen_svg(medida), fondo=False, escalar=False)


def en_reticula(x, w):
    """Convierte coordenadas heredadas (margen 24) a la retícula de 12 columnas (margen 60)."""
    k = 1800 / 1872
    return round(60 + (x - 24) * k), round(w * k)


def boton_pagina(destino):
    """Botón invisible que navega a otra página (Ctrl + clic en Desktop): sin ícono, texto, borde ni relleno
    en ningún estado (predeterminado, al mantener el puntero, presionado y seleccionado)."""
    estados = ["default", "hover", "press", "selected"]
    invisible = lambda extra=None: [{"properties": {"show": lit(False), **(extra or {})}, "selector": {"id": e}}
                                    for e in estados]
    return {"visualType": "actionButton", "objects": {
        "icon": invisible({"shapeType": lit("blank")}),
        "outline": invisible(),
        "text": invisible(),
        "fill": [{"properties": {"show": lit(True), "fillColor": color(TARJETA), "transparency": lit(100)},
                  "selector": {"id": e}} for e in estados]},
        "visualContainerObjects": {"visualLink": [{"properties": {
            "show": lit(True), "type": lit("PageNavigation"), "navigationSection": lit(destino)}}]}}


def boton_pildora(texto_, enlace):
    """Botón visible en forma de píldora: borde petróleo sobre el papel; al pasar el puntero se rellena de petróleo
    y el texto pasa a blanco. Es el estilo común de «Quitar filtros», «Anterior» y «Siguiente»."""
    estados = ["default", "hover", "press"]
    relleno = {"default": (FONDO, 0), "hover": (AZUL, 0), "press": (AZUL, 0)}
    tinta = {"default": AZUL, "hover": "#FFFFFF", "press": "#FFFFFF"}
    # La entrada sin selector enciende la propiedad para el botón completo. Los botones de navegación traen
    # texto, borde y relleno apagados de fábrica; sin esa entrada, Desktop ignora el "show" de cada estado.
    general = {"properties": {"show": lit(True)}}
    return {"visualType": "actionButton", "objects": {
        "icon": [{"properties": {"show": lit(False)}, "selector": {"id": e}} for e in estados],
        "text": [{"properties": {"show": lit(True), "text": lit(texto_), "fontColor": color(tinta[e]),
                                 "fontSize": lit(9), "fontFamily": lit(SEMI), "bold": lit(True)},
                  "selector": {"id": e}} for e in estados] + [general],
        "outline": [{"properties": {"show": lit(True), "lineColor": color(AZUL), "weight": lit(1)},
                     "selector": {"id": e}} for e in estados] + [general],
        "fill": [{"properties": {"show": lit(True), "fillColor": color(relleno[e][0]),
                                 "transparency": lit(relleno[e][1])}, "selector": {"id": e}} for e in estados]
                + [general],
        # Píldora: rectángulo con esquinas redondeadas (la mitad de la altura del botón).
        "shape": [{"properties": {"tileShape": lit("rectangleRounded"), "roundEdge": lit(14)}}]},
        "visualContainerObjects": {"visualLink": [{"properties": {"show": lit(True), **enlace}}]}}


def boton_quitar_filtros():
    """Botón «Quitar filtros»: borra todos los segmentadores de la página (acción ClearAllSlicers)."""
    return boton_pildora("↺  QUITAR FILTROS", {"type": lit("ClearAllSlicers")})


def boton_ir(texto_, destino):
    """Botón «Anterior» / «Siguiente»: navega a otra página (en Desktop, Ctrl + clic)."""
    return boton_pildora(texto_, {"type": lit("PageNavigation"), "navigationSection": lit(destino)})


def navegador():
    return {"visualType": "pageNavigator", "objects": {}}


# ------------------------------------------------------------------ estructura común
SLICERS = [("DimCalendario", "Año", True, True), ("DimGeografia", "Region", False, False),
           ("DimFormato", "Formato", False, False), ("DimCategoria", "Categoria", False, False)]
SLICER_X = [1196 + i * 168 for i in range(4)]  # mismas posiciones que recursos/fondos.py
SLICER_W = 152


def encabezado(p, slicers=True, titulo_svg=False):
    """Cabecera editorial: regla gruesa (fondo), kicker, titular en serif, subtítulo y segmentadores a la derecha."""
    p.agregar("Kicker", 52, 30, 900, 30, texto([[etiqueta(p.kicker or p.nombre_visible, AZUL)]]),
              fondo=False, escalar=False)
    if p.nombre != "pg00Portada":
        p.agregar("TxtVolver", 1010, 30, 150, 30, texto([[("← TIQUETE", estilo(9.5, True, SEC))]]),
                  fondo=False, escalar=False)
        p.agregar("BtnVolver", 1010, 30, 150, 30, boton_pagina("pg00Portada"), fondo=False, escalar=False)
    if not titulo_svg:
        pregunta = p.titulo.split(" — ")[-1]
        p.agregar("Titulo", 52, 56, 1130, 56, texto([[(pregunta, estilo(24, True, TEXTO, SERIF))]]),
                  fondo=False, escalar=False)
        if p.subtitulo:
            p.agregar("Subtitulo", 52, 110, 1130, 34, texto([[(p.subtitulo, estilo(10.5, False, SEC))]]),
                      fondo=False, escalar=False)
    nombres = []
    if slicers:
        for i, (t, c, unico, anio) in enumerate(SLICERS):
            etiqueta_ = {"Region": "Región", "Categoria": "Categoría"}.get(c, c)
            v = segmentador(t, c, unico, anio)
            v["query"]["queryState"]["Values"]["projections"][0]["displayName"] = etiqueta_
            nombres.append(p.agregar("Seg" + c.replace("ñ", "n"), SLICER_X[i] - 6, 40, SLICER_W + 12, 68, v,
                                     z=500 + i, fondo=False, escalar=False))
    return nombres


def sin_filtro(p, origen, destinos):
    for d in destinos:
        p.interacciones.append({"source": origen, "target": d, "type": "NoFilter"})


# ------------------------------------------------------------------ páginas
FONDO_PORTADA = "fondo_portada.png"
NAV_PORTADA = ["pg01Resumen", "pg02Comercial", "pg03Promociones", "pg04Disponibilidad", "pg05Conclusiones"]


def pagina_portada():
    """Portada: titular editorial a la izquierda y el tiquete (índice navegable) a la derecha."""
    p = Pagina("pg00Portada", "Portada", "", nombre_visible="Portada", fondo_imagen=FONDO_PORTADA)
    p.agregar("TxtCabIzq", 52, 64, 900, 30, texto([[etiqueta("Informe de gestión · ene–sep 2026")]]),
              fondo=False)
    cab_der = texto([[etiqueta("Grupo 3 · Inteligencia de negocios 2026-2")]])
    cab_der["objects"]["general"][0]["properties"]["paragraphs"][0]["horizontalTextAlignment"] = "right"
    p.agregar("TxtCabDer", 1196, 64, 672, 30, cab_der, fondo=False)
    p.agregar("TxtTitulo", 48, 136, 1110, 380, texto([
        [("Las ventas", estilo(72, True, TEXTO, SERIF))],
        [("no crecen.", estilo(72, True, TEXTO, SERIF))],
        [("Las regiones, sí.", estilo(72, True, AZUL, SERIF))]]), fondo=False)
    p.agregar("TxtSub", 52, 508, 920, 140, texto([[(
        "El total de la cadena está plano, pero por dentro las regiones, los formatos y las categorías se mueven "
        "en direcciones opuestas. Este tablero muestra dónde mirar primero.", estilo(17, False, SEC))]]), fondo=False)
    p.agregar("TxtFicha", 52, 700, 1080, 150, texto([
        [etiqueta("Audiencia   "), ("Gerencia de tiendas y gerencia de categoría", estilo(13.5))],
        [etiqueta("Datos   "), ("60.000 líneas de venta · 12 ciudades · 7 regiones · 01/01/2024–30/09/2026",
                                 estilo(13.5))],
        [etiqueta("Integrantes   "), ("Nombre 1 · Nombre 2 · Nombre 3", estilo(13.5))]]), fondo=False)
    # Tiquete: todo su contenido es la medida SVG (cifras vivas + índice); botones invisibles encima
    tx, ty = 1244, 176
    agregar_svg(p, "SvgTiquete", tx, ty, medidas_diseno.TIQ_W, medidas_diseno.TIQ_H, "SVG Tiquete",
                fondo_celda=TARJETA)
    for i, destino in enumerate(NAV_PORTADA):
        y = ty + medidas_diseno.TIQ_NAV_Y + i * medidas_diseno.TIQ_NAV_PASO - 30
        p.agregar(f"BtnNav{i + 1}", tx - 8, y, medidas_diseno.TIQ_W + 16, 40, boton_pagina(destino), fondo=False)
    p.agregar("TxtAyuda", 52, 1004, 1000, 30,
              texto([[etiqueta("Ctrl + clic en una línea del tiquete para ir a esa página")]]), fondo=False)
    return p


def pagina_resumen():
    p = Pagina("pg01Resumen", "Resumen ejecutivo — ¿Cómo está el negocio y dónde mirar primero?", "",
               kicker="01 · Resumen ejecutivo", fondo_imagen="fondo_resumen.png")
    seg = encabezado(p, titulo_svg=True)
    agregar_svg(p, "SvgTitulo", 60, 66, 1110, 60, "SVG Titulo Resumen")
    agregar_svg(p, "SvgKpis", 60, 186, medidas_diseno.KPI_W, medidas_diseno.KPI_H, "SVG KPIs")
    # Antes: podio SVG con el top 3 (repetía la tabla de posiciones y, al ser imagen, no filtraba).
    # Ahora: barras nativas de las 7 regiones; un clic en una región filtra toda la página.
    p.agregar("TxtRegiones", 52, 338, 900, 26,
              texto([[etiqueta("Regiones · crecimiento ene–sep frente al año anterior")]]), fondo=False, escalar=False)
    p.agregar("TitRegiones", 52, 360, 900, 44,
              texto([[("Clic en una región para filtrar la página", estilo(18, True, TEXTO, SERIF))]]),
              fondo=False, escalar=False)
    reg = barras(col("DimGeografia", "Region"),
                 [(med("Crecimiento Ventas Ene-Sep %"), "Crecimiento vs año anterior")],
                 color_cond="Color Crecimiento", ordenar=med("Crecimiento Ventas Ene-Sep %"),
                 tooltips=[(med("Crecimiento vs Hace 2 Años %"), "Crecimiento vs hace 2 años"),
                           (med("Lectura Tendencia"), "Lectura")])
    reg["objects"]["valueAxis"] = [{"properties": {"show": lit(False)}}]
    reg["objects"]["categoryAxis"] = [{"properties": {"fontSize": lit(11), "labelColor": color(TEXTO)}}]
    reg["objects"]["labels"] = [{"properties": {"show": lit(True), "fontSize": lit(11), "color": color(TEXTO)}}]
    reg["visualContainerObjects"] = {"visualTooltip": tooltip_region()}
    p.agregar("BarCrecRegion", 52, 410, 900, 398, reg, fondo=False, escalar=False)
    agregar_svg(p, "SvgPosiciones", 1044, 338, 816, 474, "SVG Posiciones")
    # Antes: ventas mensuales por año (líneas que se cruzan sin patrón). Ahora: ventas acumuladas ene–sep:
    # las tres curvas casi se superponen, que es el mensaje "el negocio está plano".
    p.agregar("TxtLinea", 52, 838, 1150, 26,
              texto([[etiqueta("Ventas acumuladas ene–sep por año · las tres curvas casi se superponen (historia completa)")]]),
              fondo=False)
    linea = lineas(col("DimCalendario", "Mes"), [(med("Ventas Acumuladas Ene-Sep"), "Ventas acumuladas")],
                   serie=col("DimCalendario", "Año"), colores_por_serie=COLORES_ANIO)
    linea["objects"]["legend"] = [{"properties": {"show": lit(True), "position": lit("TopRight"),
                                                  "fontSize": lit(9), "labelColor": color(SEC)}}]
    linea["objects"]["valueAxis"] = [{"properties": {"start": lit(0), "labelDisplayUnits": lit(1000000),
                                                     "fontSize": lit(8), "labelColor": color(SEC)}}]
    acumulado =p.agregar("LineaAcumulado", 52, 862, 1150, 206, linea, fondo=False)
    sin_filtro(p, seg[0], [acumulado])
    p.agregar("TxtCat", 1240, 838, 620, 26,
              texto([[etiqueta("Categorías · crecimiento frente al año anterior")]]), fondo=False)
    cat = barras(col("DimCategoria", "Categoria"),
                 [(med("Crecimiento Ventas Ene-Sep %"), "Crecimiento vs año anterior")],
                 color_cond="Color Crecimiento", ordenar=med("Crecimiento Ventas Ene-Sep %"),
                 tooltips=[(med("Crecimiento vs Hace 2 Años %"), "Crecimiento vs hace 2 años"),
                           (med("Lectura Tendencia"), "Lectura")])
    # Sin eje de valores (las barras llevan etiqueta) y letra pequeña: caben las 8 categorías sin desplazamiento
    cat["objects"]["valueAxis"] = [{"properties": {"show": lit(False)}}]
    cat["objects"]["categoryAxis"] = [{"properties": {"fontSize": lit(8), "labelColor": color(SEC),
                                                      "innerPadding": lit(15)}}]
    cat["objects"]["labels"] = [{"properties": {"show": lit(True), "fontSize": lit(8)}}]
    p.agregar("BarCrecCategoria", 1236, 856, 628, 214, cat, fondo=False)
    return p


def pagina_comercial():
    p = Pagina("pg02Comercial", "Desempeño comercial — ¿Qué regiones, ciudades, formatos y categorías explican el resultado?",
               "Seleccione una región o categoría para filtrar los demás gráficos · "
               "Tendencia = mismo signo frente a 2025 y a 2024",
               kicker="02 · Desempeño comercial", reescalar=True, fondo_imagen="fondo_interna.png")
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
                     color_valores=["Crecimiento Ventas Ene-Sep %"], modo="backColor", tam=12, relleno=8),
              titulo="Región × formato: crecimiento (petróleo = crece sostenido, terracota = cae, ocre = rebote)")
    p.agregar("BarCategoriaDosComp", 24, 642, 930, 418,
              barras(col("DimCategoria", "Categoria"),
                     [(med("Crecimiento Ventas Ene-Sep %"), "vs año anterior"),
                      (med("Crecimiento vs Hace 2 Años %"), "vs hace 2 años")],
                     colores=[("Crecimiento Ventas Ene-Sep %", AZUL), ("Crecimiento vs Hace 2 Años %", AZUL_CLARO)],
                     ordenar=med("Crecimiento Ventas Ene-Sep %")),
              titulo="Categorías: crecimiento frente a dos años base (solo Abarrotes crece en ambos)")
    # Antes: barras de aporte en $ por ciudad (repetían la columna «Variación $» de la matriz).
    # Ahora: cascada de la variación total por región (se puede bajar a ciudad con la flecha ↓ del visual).
    cascada = {"visualType": "waterfallChart",
               "query": query(Category=[col("DimGeografia", "Region"), col("DimGeografia", "Ciudad")],
                              Y=[(med("Variacion Ventas Ene-Sep"), "Variación $ vs año ant.")]),
               "objects": {
                   "sentimentColors": [{"properties": {"increaseFill": color(VERDE), "decreaseFill": color(ROJO),
                                                       "totalFill": color(GRIS)}}],
                   "labels": [{"properties": {"show": lit(True), "fontSize": lit(9)}}],
                   "legend": [{"properties": {"show": lit(False)}}]},
               "visualContainerObjects": {"visualTooltip": tooltip_region()}}
    cascada["query"]["sortDefinition"] = orden(med("Variacion Ventas Ene-Sep"))
    p.agregar("CascadaRegion", 970, 642, 926, 418, cascada,
              titulo="De dónde sale la variación total: suman las regiones que crecen y restan las que caen")
    return p


def pagina_promociones():
    p = Pagina("pg03Promociones", "Promociones, clientes y canales — ¿Qué palancas comerciales muestran oportunidades?",
               "El margen estimado no cambia entre grupos: las oportunidades están en el volumen y el crecimiento",
               kicker="03 · Promociones, clientes y canales", reescalar=True, fondo_imagen="fondo_interna.png")
    encabezado(p)
    agregar_svg(p, "SvgKpis", 60, 190, medidas_diseno.KPI_INT_W, 112, "SVG KPIs Promociones")
    p.agregar("TxtLectura", 924, 186, 972, 120, texto([
        [("LECTURA  ", estilo(9.5, True, AZUL)),
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
    # Antes: mezcla 100 % de canales por formato (Tienda física ≈ 81 % en todos: no decía nada nuevo).
    # Ahora: mapa de calor canal × formato con la lectura de tendencia, que sí muestra dónde hay movimiento.
    p.agregar("MatCanalFormato", 970, 322, 926, 360,
              matriz([col("DimCondicionVenta", "Canal")],
                     [(med("Crecimiento Ventas Ene-Sep %"), "Crec. vs año ant.")],
                     columnas=[col("DimFormato", "Formato")],
                     color_valores=["Crecimiento Ventas Ene-Sep %"], modo="backColor", tam=15, relleno=14),
              titulo="Canal × formato: crecimiento (ocre = rebote; ningún canal crece de forma sostenida)")
    # Antes: barras de canales (repetían la matriz canal × formato) y ventas por medio de pago (solo reparto, sin
    # hallazgo). Ahora: matriz de oportunidad por categoría, que responde directamente la P2.
    oportunidad = {"visualType": "scatterChart",
                   "query": query(Category=[col("DimCategoria", "Categoria")],
                                  X=[(med("Participacion Ventas Ene-Sep %"), "Peso en las ventas ene–sep")],
                                  Y=[(med("Crecimiento Ventas Ene-Sep %"), "Crecimiento vs año anterior")],
                                  Size=[(med("Ventas Ene-Sep"), "Ventas ene–sep")],
                                  Tooltips=[(med("Crecimiento vs Hace 2 Años %"), "Crecimiento vs hace 2 años"),
                                            (med("Lectura Tendencia"), "Lectura")]),
                   "objects": {
                       "dataPoint": [{"properties": {"fill": color_medida("Color Crecimiento")},
                                      "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}}],
                       "categoryLabels": [{"properties": {"show": lit(True), "fontSize": lit(10),
                                                          "color": color(TEXTO)}}],
                       "legend": [{"properties": {"show": lit(False)}}]}}
    p.agregar("DispOportunidad", 24, 698, 1252, 362, oportunidad,
              titulo="Matriz de oportunidad por categoría: arriba = crece, a la derecha = pesa más en las ventas "
                     "(tamaño = ventas ene–sep)")
    # Comparación directa fidelizados vs no fidelizados (cifra contra cifra) y su participación.
    fx, fw = en_reticula(1292, 604)
    p.reglas.append((fx, 698, fw))
    agregar_svg(p, "SvgFidelizacion", fx, 712, fw, round(fw * medidas_diseno.FID_H / medidas_diseno.FID_W),
                "SVG Fidelizacion")
    return p


def pagina_disponibilidad():
    p = Pagina("pg04Disponibilidad", "Disponibilidad — ¿Dónde los quiebres de stock requieren atención?",
               "Quiebre = la línea se vendió con quiebre de stock en los últimos 7 días (no mide ventas perdidas)",
               kicker="04 · Disponibilidad", reescalar=True, fondo_imagen="fondo_interna.png")
    seg = encabezado(p)
    agregar_svg(p, "SvgKpis", 60, 190, medidas_diseno.KPI_INT_W, 112, "SVG KPIs Disponibilidad")
    p.agregar("TxtLectura", 924, 186, 972, 120, texto([
        [("LECTURA  ", estilo(9.5, True, AZUL)),
         ("el quiebre es parejo (~8 %) en categorías, formatos y ciudades: ninguna diferencia es estadísticamente "
          "significativa y es estable en el tiempo. Es un problema de toda la cadena; se prioriza por volumen afectado.",
          estilo(11))]]))
    tendencia = lineas(col("DimCalendario", "AñoMes"), [(med("% Quiebre"), "% quiebre")],
                       colores=[("% Quiebre", NARANJA)])
    tendencia["objects"]["valueAxis"] = [{"properties": {"start": lit(0)}}]  # eje desde 0 %: no exagera la variación
    linea = p.agregar("LineaQuiebreMes", 24, 322, 1872, 300, tendencia,
                      titulo="% de quiebre por mes, 2024–2026 (historia completa, eje desde 0 %; no responde al filtro de año): "
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
    # Antes: matriz categoría × formato (invitaba a leer «focos» que no son significativos).
    # Ahora: % de quiebre por categoría contra la línea del promedio de la cadena: todas quedan cerca.
    combo = {"visualType": "lineClusteredColumnComboChart",
             "query": query(Category=[col("DimCategoria", "Categoria")],
                            # En esta versión de Desktop los roles del combinado son Y (columnas) y Y2 (línea).
                            Y=[(med("% Quiebre"), "% quiebre de la categoría")],
                            Y2=[(med("% Quiebre Cadena"), "Promedio de la cadena")],
                            Tooltips=[(med("Lineas con Quiebre"), "Líneas con quiebre")]),
             "objects": {
                 # Color por defecto (columnas) en ocre de quiebre; la línea del promedio en tinta.
                 "dataPoint": [{"properties": {"fill": color(NARANJA)}},
                               {"properties": {"fill": color(TEXTO)}, "selector": {"metadata": f"{M}.% Quiebre Cadena"}}],
                 # Un solo eje: con eje secundario la línea quedaba en otra escala y no se comparaba con las columnas.
                 "valueAxis": [{"properties": {"start": lit(0), "secShow": lit(False), "alignZeros": lit(True)}}],
                 "labels": [{"properties": {"show": lit(True), "fontSize": lit(8)}}],
                 "legend": [{"properties": {"show": lit(True), "position": lit("Top")}}]}}
    combo["query"]["sortDefinition"] = orden(med("% Quiebre"))
    p.agregar("ComboQuiebreCategoria", 1292, 638, 604, 422, combo,
              titulo="% quiebre por categoría frente al promedio de la cadena: todas cerca de 8 %")
    return p


def pagina_conclusiones():
    p = Pagina("pg05Conclusiones", "Conclusiones — ¿Qué decisiones debe tomar la gerencia?",
               "Síntesis de los hallazgos validados (docs/04_matriz_hallazgos.md)",
               kicker="05 · Conclusiones y decisiones", nombre_visible="Conclusiones y decisiones",
               reescalar=True, fondo_imagen="fondo_sin_filtros.png")
    encabezado(p, slicers=False)
    filas = [
        (VERDE, "Replicar lo que funciona", "+12,0 %  ·  +8,3 %",
         "Orinoquía y Eje Cafetero crecen frente a 2025 y a 2024. Eje Cafetero–Hipermercado y "
         "Suroccidente–Supermercado lideran por formato.", "Gerencia de tiendas"),
        (ROJO, "Plan de recuperación", "−4,6 %  ·  −8,6 %",
         "Nororiente (Bucaramanga) y Cartagena caen de forma sostenida. Combinaciones críticas: "
         "Nororiente–Supermercado, Caribe–Express y Centro–Express.", "Gerencia de tiendas"),
        (VERDE, "Impulsar Abarrotes", "+9,1 %  ·  +$5,7 M",
         "Única categoría con crecimiento sostenido y el mayor aporte en pesos. Las demás categorías "
         "están estables.", "Gerencia de categoría"),
        (NARANJA, "Revisar «Puntos dobles»", "−7,1 %  ·  −8,2 %",
         "Cae frente a 2025 y frente a 2024. Evaluar reasignar esa inversión promocional.",
         "Gerencia de categoría"),
        (GRIS, "Gestionar volumen, no margen", "≈ 27,5 %",
         "El margen estimado es igual en todos los grupos: las palancas comerciales no cambian la "
         "rentabilidad.", "Ambas gerencias"),
        (NARANJA, "Reposición para toda la cadena", "≈ 8 %  ·  4.849 líneas",
         "El quiebre es parejo y estable: no hay focos aislados. Priorizar por volumen afectado "
         "(Bogotá y Carnes).", "Operaciones"),
    ]
    for i, (c, t, cifra, d, quien) in enumerate(filas):
        x = 60 + (i % 3) * 608
        y = 186 + (i // 3) * 436
        p.agregar(f"TxtConclusion{i + 1}", x, y, 584, 412, texto([
            [(f"{i + 1:02d}", estilo(12, True, c, MONO)), ("   " + quien.upper(), estilo(9.5, True, SEC))],
            [(" ", estilo(6))],
            [(t, estilo(24, True, TEXTO, SERIF))],
            [(" ", estilo(6))],
            [(cifra, estilo(28, True, c, MONO))],
            [(" ", estilo(6))],
            [(d, estilo(13, False, TEXTO))]]), escalar=False)
    return p


TOOLTIP_REGION = "pg98TooltipRegion"


def tooltip_region():
    """Configuración del visual para usar la página de tooltip de región en lugar del tooltip estándar."""
    return [{"properties": {"show": lit(True), "type": lit("Canvas"), "section": lit(TOOLTIP_REGION)}}]


def pagina_tooltip_region():
    """Tooltip personalizado (oculto): al pasar sobre una región muestra sus ventas, las dos comparaciones y la lectura."""
    p = Pagina(TOOLTIP_REGION, "Tooltip región", "", oculta=True, nombre_visible="Tooltip región",
               tamano=(380, 250), tooltip=True)
    nombre = {"visualType": "card", "query": query(Values=[(med("Region Seleccionada"), "Región")]),
              "objects": {"labels": [{"properties": {"color": color(AZUL), "fontSize": lit(18),
                                                     "fontFamily": lit(SERIF)}}],
                          "categoryLabels": [{"properties": {"show": lit(False)}}]}}
    p.agregar("TarRegion", 10, 6, 360, 52, nombre, fondo=False, escalar=False)
    celdas = [("Ventas Ene-Sep", "Ventas ene–sep"), ("Lectura Tendencia", "Lectura"),
              ("Crecimiento Ventas Ene-Sep %", "Vs año anterior"), ("Crecimiento vs Hace 2 Años %", "Vs hace 2 años")]
    for i, (m_, e) in enumerate(celdas):
        t = tarjeta(m_, e, AZUL)
        t["objects"]["labels"][0]["properties"]["fontSize"] = lit(15)
        t["objects"]["categoryLabels"][0]["properties"]["fontSize"] = lit(9)
        p.agregar(f"Tar{i + 1}", 10 + (i % 2) * 182, 62 + (i // 2) * 92, 176, 86, t, fondo=False, escalar=False)
    return p


def pagina_validacion():
    p = Pagina("pg99Validacion", "Validación técnica — Cifras de control contra el CSV",
               "Valores esperados: scripts/validacion/01_perfilamiento.py y docs/03_modelo.md", oculta=True,
               kicker="99 · Validación técnica (oculta)", reescalar=True, fondo_imagen="fondo_sin_filtros.png")
    encabezado(p, slicers=False)
    medidas_ctrl = ["Ventas Netas", "Costo Estimado", "Margen Estimado", "Margen Estimado %", "Lineas de Venta",
                    "Unidades", "Lineas con Quiebre", "% Quiebre", "Ventas con Quiebre", "Ventas en Promocion",
                    "% Ventas en Promocion", "Venta por Linea", "Transacciones (ID dataset)",
                    "Ticket Promedio (ID dataset)"]
    p.agregar("TablaTotales", 24, 186, 1872, 160,
              {"visualType": "tableEx", "objects": estilo_tabla(), "query": query(Values=[med(m_) for m_ in medidas_ctrl])},
              titulo="Totales (esperado: 1.560.062.403 · 1.131.389.400 · 428.673.003 · 27,48 % · 60.000 · "
                     "121.393 · 4.849 · 8,08 % · 126.858.302 · 618.958.563 · 39,68 % · 26.001 · 21.264 · 73.366)")
    p.agregar("TablaAnios", 24, 362, 930, 300,
              {"visualType": "tableEx", "objects": estilo_tabla(), "query": query(Values=[
                  col("DimCalendario", "Año"), med("Ventas Ene-Sep"), med("Ventas Ene-Sep Año Anterior"),
                  med("Crecimiento Ventas Ene-Sep %"), med("Crecimiento vs Hace 2 Años %")])},
              titulo="Por año (esperado ene–sep: 425.113.135 · 424.805.507 · 428.753.035; 2026: +0,93 %)")
    p.agregar("TablaRegion", 970, 362, 926, 300,
              {"visualType": "tableEx", "objects": estilo_tabla(), "query": query(Values=[
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


def registrar_imagen(defin, archivo):
    """Copia la imagen a StaticResources/RegisteredResources y la registra en report.json (idempotente)."""
    origen = RAIZ / "scripts" / "pbip" / "recursos" / archivo
    if not origen.exists():
        sys.exit(f"Falta la imagen {origen}. Genérela con:  python scripts/pbip/recursos/fondos.py")
    destino = defin.parent / "StaticResources" / "RegisteredResources" / archivo
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(origen, destino)
    ruta = defin / "report.json"
    rep = json.loads(ruta.read_text(encoding="utf-8"))
    paquetes = rep.setdefault("resourcePackages", [])
    reg = next((r for r in paquetes if r.get("name") == "RegisteredResources"), None)
    if reg is None:
        reg = {"name": "RegisteredResources", "type": "RegisteredResources", "items": []}
        paquetes.append(reg)
    if not any(i.get("name") == archivo for i in reg["items"]):
        reg["items"].append({"name": archivo, "path": archivo, "type": "Image"})
    ruta.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")


TEMA = "TiqueteEditorial.json"


def registrar_tema(defin):
    """Tema propio (paleta y tipografías) registrado como CustomTheme en report.json."""
    tema = {
        "name": "Tiquete editorial",
        "dataColors": [AZUL, AZUL_CLARO, COMP2, NARANJA, ROJO, GRIS, "#9C7A12", "#3F6B5E"],
        "background": TARJETA, "foreground": TEXTO, "tableAccent": AZUL,
        "good": VERDE, "bad": ROJO, "neutral": NARANJA,
        "textClasses": {
            "label": {"fontFace": "Segoe UI", "fontSize": 10, "color": SEC},
            "callout": {"fontFace": MONO, "fontSize": 28, "color": TEXTO},
            "title": {"fontFace": SEMI, "fontSize": 12, "color": TEXTO},
            "header": {"fontFace": SEMI, "fontSize": 12, "color": TEXTO},
        },
    }
    destino = defin.parent / "StaticResources" / "RegisteredResources" / TEMA
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(tema, ensure_ascii=False, indent=2), encoding="utf-8")
    ruta = defin / "report.json"
    rep = json.loads(ruta.read_text(encoding="utf-8"))
    paquetes = rep.setdefault("resourcePackages", [])
    reg = next((r for r in paquetes if r.get("name") == "RegisteredResources"), None)
    if reg is None:
        reg = {"name": "RegisteredResources", "type": "RegisteredResources", "items": []}
        paquetes.append(reg)
    if not any(i.get("name") == TEMA for i in reg["items"]):
        reg["items"].append({"name": TEMA, "path": TEMA, "type": "CustomTheme"})
    base = rep["themeCollection"]["baseTheme"]
    rep["themeCollection"]["customTheme"] = {"name": TEMA, "reportVersionAtImport": base["reportVersionAtImport"],
                                             "type": "RegisteredResources"}
    ruta.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")


def fondos_por_pagina(paginas):
    """Las páginas internas llevan su propio fondo: cabecera + reglas finas sobre cada bloque.

    Si playwright está instalado se regeneran los PNG en scripts/pbip/recursos/; si no, se usan los existentes."""
    sys.path.insert(0, str(RAIZ / "scripts" / "pbip" / "recursos"))
    import fondos
    archivos = {}
    for p in paginas:
        if p.fondo_imagen in ("fondo_interna.png", "fondo_sin_filtros.png") and p.reglas:
            nombre = f"fondo_{p.nombre}.png"
            archivos[nombre] = fondos.con_reglas(p.reglas, slicers=p.fondo_imagen == "fondo_interna.png")
            p.fondo_imagen = nombre
    try:
        fondos.generar(archivos)
    except ImportError:
        print("playwright no está instalado: se usan los fondos ya generados en scripts/pbip/recursos/")


def escribir(defin, paginas):
    sv, sp = esquema_visual(defin), esquema_pagina(defin)
    registrar_tema(defin)
    pages_dir = defin / "pages"
    # Se reemplazan las páginas que genera este script y la página de muestra inicial.
    for d in pages_dir.iterdir():
        if d.is_dir():
            shutil.rmtree(d)
    fondos_por_pagina(paginas)
    for p in paginas:
        pdir = pages_dir / p.nombre
        (pdir / "visuals").mkdir(parents=True)
        fondo = {"color": color(FONDO), "transparency": lit(0)}
        if p.fondo_imagen:
            registrar_imagen(defin, p.fondo_imagen)
            fondo["transparency"] = lit(0)
            fondo["image"] = {"image": {
                "name": lit(p.fondo_imagen),
                "url": {"expr": {"ResourcePackageItem": {"PackageName": "RegisteredResources", "PackageType": 1,
                                                         "ItemName": p.fondo_imagen}}},
                "scaling": lit("Fit")}}
        ancho, alto = p.tamano
        page = {"$schema": sp, "name": p.nombre, "displayName": p.nombre_visible,
                "displayOption": "FitToPage", "height": alto, "width": ancho,
                "objects": {"background": [{"properties": fondo}]}}
        if p.oculta:
            page["visibility"] = "HiddenInViewMode"
        if p.tooltip:
            # Ambas propiedades son necesarias: sin "type" Desktop no ofrece la página como tooltip.
            page["pageBinding"] = {"name": p.nombre, "type": "Tooltip", "parameters": []}
            page["type"] = "Tooltip"
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


BTN_W, BTN_H, BTN_SEP = 150, 28, 12


def agregar_navegacion(paginas):
    """Botones «← Anterior» y «Siguiente →» en el orden de lectura de las páginas visibles.

    Portada: solo «Siguiente». Conclusiones (última): «Siguiente» vuelve a la portada.
    Validación (oculta): «Anterior» a conclusiones y vuelta a la portada."""
    visibles = [p for p in paginas if not p.oculta]
    x_sig = 1858 - BTN_W
    x_ant = x_sig - BTN_SEP - BTN_W
    for i, p in enumerate(paginas):
        if p.tooltip:
            continue
        if p.oculta:
            anterior, siguiente = visibles[-1], visibles[0]
        else:
            j = visibles.index(p)
            anterior = visibles[j - 1] if j > 0 else None
            siguiente = visibles[j + 1] if j + 1 < len(visibles) else visibles[0]
        texto_sig = "PORTADA  ↺" if siguiente is visibles[0] else "SIGUIENTE  →"
        # En la portada no hay cabecera: los botones van abajo, a la altura de la ayuda del tiquete.
        y = 1002 if p.nombre == "pg00Portada" else 114
        if anterior is not None:
            p.agregar("BtnAnterior", x_ant, y, BTN_W, BTN_H, boton_ir("←  ANTERIOR", anterior.nombre),
                      z=610, fondo=False, escalar=False)
        p.agregar("BtnSiguiente", x_sig, y, BTN_W, BTN_H, boton_ir(texto_sig, siguiente.nombre),
                  z=611, fondo=False, escalar=False)


def main():
    reportes = list((RAIZ / "powerbi").glob("*.Report/definition"))
    if len(reportes) != 1:
        sys.exit(f"Se esperaba un único *.Report en powerbi/, encontrados: {reportes}")
    defin = reportes[0]
    paginas = [pagina_portada(), pagina_resumen(), pagina_comercial(), pagina_promociones(),
               pagina_disponibilidad(), pagina_conclusiones(), pagina_validacion(), pagina_tooltip_region()]
    # Se agregan al final para no renumerar los visuales existentes. Fila bajo los segmentadores (y = 114):
    # «Quitar filtros» alineado con el primer segmentador y la navegación alineada al borde derecho (x = 1858).
    for p in paginas:
        if any(v["visual"]["visualType"] == "slicer" for v in p.visuales):
            p.agregar("BtnQuitarFiltros", SLICER_X[0] - 6, 114, 176, 28, boton_quitar_filtros(),
                      z=600, fondo=False, escalar=False)
    agregar_navegacion(paginas)
    escribir(defin, paginas)
    total = sum(len(p.visuales) for p in paginas)
    print(f"{len(paginas)} páginas y {total} visuales escritos en {defin}")
    print("✓ JSON válido" if validar(defin) else "✗ Hay JSON inválido")


if __name__ == "__main__":
    main()
