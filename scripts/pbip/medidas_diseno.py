"""Medidas de diseño (rediseño "tiquete + editorial", skill dashboard-design-studio).

Las usa generar_modelo_tmdl.py. Incluye:
  * SVG animados (categoría de datos ImageUrl): podio top 3, tabla de posiciones y bloque del tiquete.
  * Titulares dinámicos y textos de KPI con formato colombiano (coma decimal, punto de miles),
    para que el texto no dependa de la configuración regional de quien abre el reporte.

Los SVG se arman en Python a partir de una plantilla con marcadores ⟨...⟩ que se convierten en
concatenaciones DAX. Las coordenadas son las del mockup aprobado (docs de diseño / mezcla A + C).
"""
import re

# ------------------------------------------------------------------ paleta (validada con paleta.py)
TINTA, SEC, IDENT, BORDE = "#1E2B2F", "#5B6770", "#0E4D64", "#E2DACB"
VERDE, ROJO, NAR, GRIS = "#0E4D64", "#9A4A2C", "#A87B22", "#7D858C"  # sin verde ni rojo: petróleo, terracota, ocre, gris
ORO, PLATA, BRONCE = "#C9A227", "#A9B1B9", "#B9773F"
FUENTE = "Segoe UI, Arial, sans-serif"
MONO = "Consolas, Courier New, monospace"


def a_dax(plantilla):
    """'texto ⟨EXPR⟩ texto' → '"texto" & EXPR & "texto"' (las comillas dobles del SVG no se usan)."""
    partes = re.split(r"⟨(.*?)⟩", plantilla, flags=re.S)
    salida = []
    for i, p in enumerate(partes):
        if i % 2 == 0:
            assert '"' not in p, "Use comillas simples en el SVG"
            if p:
                salida.append('"' + p + '"')
        else:
            salida.append("( " + p + " )")
    return " & ".join(salida) if salida else '""'


def pct_dax(x):
    """Porcentaje con signo y coma decimal: +12,0 %."""
    return (f'IF ( {x} > 0, "+", IF ( {x} < 0, "−", "" ) ) & '
            f'SUBSTITUTE ( FORMAT ( ABS ( {x} ) * 100, "0.0" ), ".", "," ) & " %"')


def uri(svg_var):
    return (f'"data:image/svg+xml;utf8," & SUBSTITUTE ( SUBSTITUTE ( {svg_var}, "%", "%25" ), "#", "%23" )')


# Tabla de regiones con crecimiento actual, vs hace 2 años, del año anterior, puestos y color de lectura
BLOQUE_REGIONES = """VAR Anio = SELECTEDVALUE ( DimCalendario[Año] )
VAR T =
    ADDCOLUMNS (
        ALL ( DimGeografia[Region] ),
        "@g", [Crecimiento Ventas Ene-Sep %],
        "@g2", [Crecimiento vs Hace 2 Años %],
        "@gp", [Crecimiento Año Anterior %]
    )
VAR TV = FILTER ( T, NOT ISBLANK ( [@g] ) )
VAR TP = FILTER ( TV, NOT ISBLANK ( [@gp] ) )
VAR R =
    ADDCOLUMNS (
        TV,
        "@r", RANKX ( TV, [@g], , DESC, SKIP ),
        "@rp", IF ( NOT ISBLANK ( [@gp] ), RANKX ( TP, [@gp], , DESC, SKIP ) ),
        "@c", SWITCH (
            TRUE (),
            [@g] > 0.02 && [@g2] > 0.02, "@@VERDE@@",
            [@g] < -0.02 && [@g2] < -0.02, "@@ROJO@@",
            ABS ( [@g] ) > 0.02, "@@NAR@@",
            "@@GRIS@@"
        )
    )""".replace("@@VERDE@@", VERDE).replace("@@ROJO@@", ROJO).replace("@@NAR@@", NAR).replace("@@GRIS@@", GRIS)

SVG_MENSAJE = ("\"<svg xmlns='http://www.w3.org/2000/svg' width='888' height='380'><text x='444' y='190' "
               f"text-anchor='middle' font-family='{FUENTE}' font-size='22' fill='{SEC}'>\" & Msg & \"</text></svg>\"")


# ------------------------------------------------------------------ podio
SERIF = "Cambria, Georgia, serif"


def cabecera_svg(etiqueta, titular_token):
    return (f"<text x='0' y='16' font-size='13' letter-spacing='2' font-weight='700' fill='{SEC}'>{etiqueta}</text>"
            f"<text x='0' y='52' font-family='{SERIF}' font-size='28' font-weight='700' fill='{TINTA}'>⟨{titular_token}⟩</text>")


def plantilla_podio(w=888, h=460, maxh=170):
    bw, gap = 250, 36
    x0 = (w - (3 * bw + 2 * gap)) / 2
    base = h - 10
    slots = [(2, PLATA, 0.70, 0.25), (1, ORO, 1.0, 0.5), (3, BRONCE, 0.52, 0.0)]
    o = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}' font-family='{FUENTE}'>",
         cabecera_svg("EL PODIO · CRECIMIENTO ENE–SEP FRENTE AL AÑO ANTERIOR", "TIT")]
    for k, (pos, c, f, delay) in enumerate(slots):
        x = x0 + k * (bw + gap)
        cx = x + bw / 2
        ph = round(maxh * f)
        y = base - ph
        ease = "calcMode='spline' keySplines='.2 .8 .2 1'"
        o.append(f"<rect x='{x:.0f}' y='{base}' width='{bw}' height='0' rx='10' fill='{c}' fill-opacity='.16' stroke='{c}' stroke-width='2'>"
                 f"<animate attributeName='height' from='0' to='{ph}' dur='.8s' begin='{delay}s' fill='freeze' {ease}/>"
                 f"<animate attributeName='y' from='{base}' to='{y}' dur='.8s' begin='{delay}s' fill='freeze' {ease}/></rect>")
        o.append(f"<g opacity='0'><animate attributeName='opacity' from='0' to='1' dur='.5s' begin='{delay + .6}s' fill='freeze'/>"
                 f"<text x='{cx:.0f}' y='{y + 52}' text-anchor='middle' font-size='44' font-weight='800' fill='{TINTA}'>⟨P{pos}⟩</text>"
                 f"<text x='{cx:.0f}' y='{y + 80}' text-anchor='middle' font-size='14' fill='{SEC}'>⟨S{pos}⟩</text></g>")
        my = y - 150
        o.append(f"<g opacity='0' transform='translate(0,-30)'>"
                 f"<animate attributeName='opacity' from='0' to='1' dur='.4s' begin='{delay + .7}s' fill='freeze'/>"
                 f"<animateTransform attributeName='transform' type='translate' from='0 -30' to='0 0' dur='.5s' begin='{delay + .7}s' fill='freeze' calcMode='spline' keySplines='.3 1.4 .5 1'/>"
                 f"<path d='M{cx - 18:.0f} {my}h14l8 30h-14z' fill='#7A8A92'/><path d='M{cx + 18:.0f} {my}h-14l-8 30h14z' fill='#52626A'/>"
                 f"<circle cx='{cx:.0f}' cy='{my + 62}' r='36' fill='{c}'/>"
                 f"<circle cx='{cx:.0f}' cy='{my + 62}' r='26' fill='none' stroke='rgba(255,255,255,.6)' stroke-width='2.5'/>"
                 f"<text x='{cx:.0f}' y='{my + 73}' text-anchor='middle' font-size='32' font-weight='800' fill='#fff'>{pos}</text>"
                 f"<text x='{cx:.0f}' y='{my + 128}' text-anchor='middle' font-size='24' font-weight='700' fill='{TINTA}'>⟨N{pos}⟩</text></g>")
    o.append("</svg>")
    return "".join(o)


TIT_PODIO = """VAR RP1_ = MAXX ( FILTER ( R, [@r] = 1 ), [@rp] )
VAR NP_ = COUNTROWS ( TP )
VAR TIT =
    SWITCH (
        TRUE (),
        ISBLANK ( RP1_ ), N1 & " lidera el crecimiento",
        RP1_ = 1, N1 & " repite en el primer puesto",
        RP1_ = NP_, N1 & " pasó del último puesto al primero",
        N1 & " subió del puesto " & RP1_ & " al primero"
    )"""

TIT_POS = """VAR M_ = ADDCOLUMNS ( FILTER ( R, NOT ISBLANK ( [@rp] ) ), "@m", [@rp] - [@r] )
VAR MinM_ = MINX ( M_, [@m] )
VAR Peores_ = FILTER ( M_, [@m] = MinM_ )
VAR TIT =
    SWITCH (
        TRUE (),
        ISEMPTY ( M_ ), "Sin tabla de " & ( Anio - 1 ) & " para comparar puestos",
        MinM_ >= 0, "Ninguna región perdió puestos frente a " & ( Anio - 1 ),
        CONCATENATEX ( Peores_, DimGeografia[Region], " y ", DimGeografia[Region], ASC )
            & IF ( COUNTROWS ( Peores_ ) > 1, " bajaron ", " bajó " ) & ( - MinM_ )
            & IF ( MinM_ = -1, " puesto", " puestos" )
    )"""


def dax_podio():
    lineas = [BLOQUE_REGIONES]
    for p in (1, 2, 3):
        lineas.append(f"VAR F{p} = FILTER ( R, [@r] = {p} )")
        lineas.append(f"VAR N{p} = MAXX ( F{p}, DimGeografia[Region] )")
        lineas.append(f"VAR G{p} = MAXX ( F{p}, [@g] )")
        lineas.append(f"VAR H{p} = MAXX ( F{p}, [@g2] )")
        lineas.append(f"VAR P{p} = IF ( ISBLANK ( N{p} ), \"\", {pct_dax(f'G{p}')} )")
        lineas.append(f"VAR S{p} = IF ( ISBLANK ( N{p} ), \"\", \"vs \" & ( Anio - 1 ) & IF ( ISBLANK ( H{p} ), \"\", \" · \" & {pct_dax(f'H{p}')} & \" vs \" & ( Anio - 2 ) ) )")
    lineas.append(TIT_PODIO)
    lineas.append('VAR Msg = IF ( ISBLANK ( Anio ), "Seleccione un solo año", "Sin año anterior para comparar" )')
    lineas.append(f"VAR Svg = IF ( ISBLANK ( N1 ), {SVG_MENSAJE}, {a_dax(plantilla_podio())} )")
    lineas.append(f"RETURN\n    {uri('Svg')}")
    return "\n".join(lineas)


# ------------------------------------------------------------------ tabla de posiciones
def dax_posiciones(w=816, fila=50, top=80):
    cero = 380 + (w - 380 - 90) * 0.3
    ancho_pos = (w - 380 - 90) * 0.68
    ancho_neg = (w - 380 - 90) * 0.29
    h = fila * 7 + 44 + top
    cab = (f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}' font-family='{FUENTE}'>"
           + cabecera_svg("TABLA DE POSICIONES · PUESTOS GANADOS O PERDIDOS", "TIT") +
           f"<g transform='translate(0,{top})'>"
           f"<text x='0' y='18' font-size='12' letter-spacing='1.5' font-weight='700' fill='{SEC}'>PUESTO</text>"
           f"<text x='96' y='18' font-size='12' letter-spacing='1.5' font-weight='700' fill='{SEC}'>MOV.</text>"
           f"<text x='170' y='18' font-size='12' letter-spacing='1.5' font-weight='700' fill='{SEC}'>REGIÓN</text>"
           f"<text x='{w - 6}' y='18' text-anchor='end' font-size='12' letter-spacing='1.5' font-weight='700' fill='{SEC}'>VS ⟨Anio - 1⟩</text>"
           f"<line x1='{cero:.1f}' x2='{cero:.1f}' y1='36' y2='⟨36 + NR * {fila}⟩' stroke='{SEC}' stroke-opacity='.5'/>")
    # una fila: los marcadores usan columnas de R y variables calculadas por fila
    medalla = (f"IF ( [@r] <= 3, \"<circle cx='22' cy='\" & ( Y + {fila / 2} ) & \"' r='17' fill='\" & "
               f"SWITCH ( [@r], 1, \"{ORO}\", 2, \"{PLATA}\", \"{BRONCE}\" ) & \"'/><text x='22' y='\" & ( Y + {fila / 2 + 6} ) & "
               f"\"' text-anchor='middle' font-size='17' font-weight='800' fill='#fff'>\" & [@r] & \"</text>\", "
               f"\"<text x='22' y='\" & ( Y + {fila / 2 + 7} ) & \"' text-anchor='middle' font-size='20' font-weight='700' fill='{SEC}'>\" & [@r] & \"</text>\" )")
    mov = (f"SWITCH ( TRUE (), ISBLANK ( [@rp] ), \"\", "
           f"[@rp] > [@r], \"<text x='96' y='\" & ( Y + {fila / 2 + 6} ) & \"' font-size='17' font-weight='700' fill='{VERDE}'>▲ \" & ( [@rp] - [@r] ) & \"</text>\", "
           f"[@rp] < [@r], \"<text x='96' y='\" & ( Y + {fila / 2 + 6} ) & \"' font-size='17' font-weight='700' fill='{ROJO}'>▼ \" & ( [@r] - [@rp] ) & \"</text>\", "
           f"\"<text x='96' y='\" & ( Y + {fila / 2 + 6} ) & \"' font-size='17' fill='{SEC}'>=</text>\" )")
    fila_svg = (f"<line x1='0' x2='{w}' y1='⟨Y + {fila}⟩' y2='⟨Y + {fila}⟩' stroke='{BORDE}'/>"
                f"⟨{medalla}⟩⟨{mov}⟩"
                f"<text x='170' y='⟨Y + {fila / 2 + 7}⟩' font-size='20' font-weight='⟨IF ( [@r] <= 3, 700, 500 )⟩' fill='{TINTA}'>⟨DimGeografia[Region]⟩</text>"
                f"<rect x='{cero:.1f}' y='⟨Y + 15⟩' width='0' height='{fila - 30}' rx='4' fill='⟨[@c]⟩'>"
                f"<animate attributeName='width' from='0' to='⟨FORMAT ( WB, \"0.0\", \"en-US\" )⟩' dur='.9s' begin='0.⟨[@r] - 1⟩s' fill='freeze' calcMode='spline' keySplines='.2 .8 .2 1'/>"
                f"<animate attributeName='x' from='{cero:.1f}' to='⟨FORMAT ( XB, \"0.0\", \"en-US\" )⟩' dur='.9s' begin='0.⟨[@r] - 1⟩s' fill='freeze' calcMode='spline' keySplines='.2 .8 .2 1'/></rect>"
                f"<text x='{w - 6}' y='⟨Y + {fila / 2 + 7}⟩' text-anchor='end' font-size='20' font-weight='700' fill='⟨[@c]⟩'>⟨{pct_dax('[@g]')}⟩</text>")
    fila_dax = a_dax(fila_svg)
    # Las variables por fila se calculan dentro del CONCATENATEX con un VAR local
    fila_expr = (f"VAR Y = 36 + ( [@r] - 1 ) * {fila}\n"
                 f"            VAR WB = ROUND ( ABS ( [@g] ) * Esc, 1 )\n"
                 f"            VAR XB = IF ( [@g] >= 0, {cero:.1f}, {cero:.1f} - WB )\n"
                 f"            RETURN {fila_dax}")
    return "\n".join([
        BLOQUE_REGIONES,
        "VAR NR = COUNTROWS ( R )",
        "VAR MaxP = MAXX ( R, MAX ( [@g], 0 ) )",
        "VAR MaxN = MAXX ( R, MAX ( - [@g], 0 ) )",
        f"VAR Esc = MIN ( IF ( MaxP > 0, {ancho_pos:.1f} / MaxP, 1E9 ), IF ( MaxN > 0, {ancho_neg:.1f} / MaxN, 1E9 ) )",
        f"VAR Filas = CONCATENATEX ( R,\n            {fila_expr},\n        \"\", [@r], ASC )",
        'VAR Msg = IF ( ISBLANK ( Anio ), "Seleccione un solo año", "Sin año anterior para comparar" )',
        TIT_POS,
        f"VAR Svg = IF ( NR = 0, {SVG_MENSAJE}, {a_dax(cab)} & Filas & \"</g></svg>\" )",
        f"RETURN\n    {uri('Svg')}",
    ])


# ------------------------------------------------------------------ tiquete de la portada
NAV_TIQUETE = ["RESUMEN EJECUTIVO", "DESEMPEÑO COMERCIAL", "PROMOCIONES Y CANALES", "DISPONIBILIDAD", "CONCLUSIONES"]
TIQ_W, TIQ_H, TIQ_NAV_Y, TIQ_NAV_PASO = 568, 760, 500, 46


def plantilla_tiquete(w=TIQ_W, h=TIQ_H):
    c = w / 2
    o = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}' font-family='{MONO}'>",
         f"<text x='{c}' y='26' text-anchor='middle' font-size='25' font-weight='700' letter-spacing='2' fill='{TINTA}'>CADENA NACIONAL</text>",
         f"<text x='{c}' y='56' text-anchor='middle' font-size='18' fill='{TINTA}'>DE SUPERMERCADOS</text>",
         f"<text x='{c}' y='84' text-anchor='middle' font-size='18' fill='{SEC}'>TIQUETE DE VENTAS · ENE–SEP</text>",
         f"<line x1='0' x2='{w}' y1='124' y2='124' stroke='{BORDE}' stroke-width='2' stroke-dasharray='8 6'/>"]
    for i in range(3):
        y = 170 + i * 42
        peso = 700 if i == 2 else 400
        o.append(f"<g opacity='0'><animate attributeName='opacity' from='0' to='1' dur='.25s' begin='{.15 + i * .25:.2f}s' fill='freeze'/>"
                 f"<text x='0' y='{y}' font-size='22' fill='{TINTA}' font-weight='{peso}'>ENE–SEP ⟨A{i}⟩</text>"
                 f"<text x='{w}' y='{y}' text-anchor='end' font-size='22' fill='{TINTA}' font-weight='{peso}'>⟨T{i}⟩</text></g>")
    o.append(f"<line x1='0' x2='{w}' y1='290' y2='290' stroke='{BORDE}' stroke-width='2' stroke-dasharray='8 6'/>"
             f"<g opacity='0'><animate attributeName='opacity' from='0' to='1' dur='.3s' begin='1s' fill='freeze'/>"
             f"<text x='0' y='352' font-size='22' font-weight='700' fill='{TINTA}'>VARIACIÓN</text>"
             f"<text x='{w}' y='362' text-anchor='end' font-size='66' font-weight='700' fill='{IDENT}'>⟨VX⟩</text></g>"
             f"<text x='0' y='410' font-size='15' fill='{SEC}'>* PLANO EN EL TOTAL. POR DENTRO, NO.</text>"
             f"<line x1='0' x2='{w}' y1='446' y2='446' stroke='{BORDE}' stroke-width='2' stroke-dasharray='8 6'/>")
    car = 0.5498 * 20  # ancho de un carácter de Consolas a 20 px
    for i, nombre in enumerate(NAV_TIQUETE):
        y = TIQ_NAV_Y + i * TIQ_NAV_PASO
        x_fin = 40 + len(nombre) * car + 12
        o.append(f"<text x='0' y='{y}' font-size='20' font-weight='700' fill='{IDENT}'>{i + 1:02d}</text>"
                 f"<text x='40' y='{y}' font-size='20' fill='{TINTA}'>{nombre}</text>"
                 f"<line x1='{x_fin:.0f}' x2='{w - 30}' y1='{y - 5}' y2='{y - 5}' stroke='{SEC}' stroke-width='2' stroke-dasharray='1 5' stroke-linecap='round'/>"
                 f"<text x='{w}' y='{y}' text-anchor='end' font-size='20' fill='{TINTA}'>→</text>")
    patron = [3, 1, 4, 2, 1, 3, 2, 1, 4, 1, 3, 2, 1, 4, 2, 1, 3, 1, 2, 4, 1, 3, 2, 1, 3, 2, 1, 4, 2, 1, 3, 2]
    xx, k, barras = 0, 0, []
    while xx < 200:
        b = patron[k % len(patron)]
        barras.append(f"<rect x='{(w - 200) / 2 + xx:.0f}' y='{h - 60}' width='{b}' height='54' fill='{TINTA}'/>")
        xx += b + patron[(k + 5) % len(patron)] % 3 + 2
        k += 1
    o += barras
    o.append("</svg>")
    return "".join(o)


def dax_tiquete():
    lineas = ["VAR Ult = YEAR ( CALCULATE ( MAX ( FactVentas[fecha] ), REMOVEFILTERS () ) )"]
    for i in range(3):
        lineas.append(f"VAR A{i} = Ult - {2 - i}")
        lineas.append(f"VAR V{i} = CALCULATE ( [Ventas Ene-Sep], REMOVEFILTERS ( DimCalendario ), DimCalendario[Año] = A{i} )")
        lineas.append(f'VAR T{i} = "$" & SUBSTITUTE ( FORMAT ( V{i}, "#,0" ), ",", "." )')
    lineas.append("VAR Crec = DIVIDE ( V2 - V1, V1 )")
    lineas.append('VAR VX = IF ( Crec > 0, "+", IF ( Crec < 0, "−", "" ) ) & SUBSTITUTE ( FORMAT ( ABS ( Crec ) * 100, "0.00" ), ".", "," ) & " %"')
    lineas.append(f"VAR Svg = {a_dax(plantilla_tiquete())}")
    lineas.append(f"RETURN\n    {uri('Svg')}")
    return "\n".join(lineas)


# ------------------------------------------------------------------ fila de KPI y titular del resumen
KPI_W, KPI_H, KPI_PASO = 1800, 112, 364


def plantilla_kpis(w=KPI_W, h=KPI_H):
    etiquetas = ["VENTAS ENE–SEP", "FRENTE A ⟨Anio - 1⟩", "MARGEN ESTIMADO", "LÍNEAS CON QUIEBRE", "VENTA POR LÍNEA"]
    o = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}' font-family='{FUENTE}'>"]
    for i, e in enumerate(etiquetas):
        x = i * KPI_PASO
        if i:
            o.append(f"<line x1='{x - 16}' x2='{x - 16}' y1='0' y2='{h}' stroke='{BORDE}'/>")
        o.append(f"<text x='{x}' y='14' font-size='13' letter-spacing='2' font-weight='700' fill='{SEC}'>{e}</text>"
                 f"<g opacity='0' transform='translate(0,12)'>"
                 f"<animate attributeName='opacity' from='0' to='1' dur='.4s' begin='{i * .12:.2f}s' fill='freeze'/>"
                 f"<animateTransform attributeName='transform' type='translate' from='0 12' to='0 0' dur='.5s' begin='{i * .12:.2f}s' fill='freeze' calcMode='spline' keySplines='.2 .8 .2 1'/>"
                 f"<text x='{x}' y='68' font-family='{MONO}' font-size='46' font-weight='700' fill='⟨C{i}⟩'>⟨K{i}⟩</text></g>"
                 f"<text x='{x}' y='100' font-size='14' fill='{SEC}'>⟨N{i}⟩</text>")
    o.append("</svg>")
    return "".join(o)


def dax_kpis():
    mill = lambda v: f'"$" & SUBSTITUTE ( FORMAT ( {v} / 1E6, "0.0" ), ".", "," ) & " M"'
    return "\n".join([
        "VAR Anio = SELECTEDVALUE ( DimCalendario[Año] )",
        "VAR V = [Ventas Ene-Sep]",
        "VAR C = [Crecimiento Ventas Ene-Sep %]",
        "VAR Lect = [Lectura Tendencia]",
        "VAR A1 = CALCULATE ( [Ventas Ene-Sep], DimCalendario[Año] = Anio - 1 )",
        "VAR A2 = CALCULATE ( [Ventas Ene-Sep], DimCalendario[Año] = Anio - 2 )",
        f"VAR K0 = IF ( ISBLANK ( V ), \"—\", {mill('V')} )",
        "VAR K1 = IF ( ISBLANK ( C ), \"—\", IF ( C > 0, \"▲ \", IF ( C < 0, \"▼ \", \"\" ) ) & SUBSTITUTE ( FORMAT ( ABS ( C ) * 100, \"0.00\" ), \".\", \",\" ) & \" %\" )",
        'VAR K2 = SUBSTITUTE ( FORMAT ( [Margen Estimado %] * 100, "0.0" ), ".", "," ) & " %"',
        'VAR K3 = SUBSTITUTE ( FORMAT ( [% Quiebre] * 100, "0.0" ), ".", "," ) & " %"',
        'VAR K4 = "$" & SUBSTITUTE ( FORMAT ( [Venta por Linea], "#,0" ), ",", "." )',
        f'VAR C0 = "{TINTA}"',
        f'VAR C1 = SWITCH ( Lect, "Crece (sostenido)", "{VERDE}", "Cae (sostenido)", "{ROJO}", "{IDENT}" )',
        f'VAR C2 = "{TINTA}"',
        f'VAR C3 = "{NAR}"',
        f'VAR C4 = "{TINTA}"',
        "VAR N0 = IF ( ISBLANK ( Anio ), \"Seleccione un solo año\", IF ( ISBLANK ( A1 ), \"Primer año de la serie\", "
        f"( Anio - 1 ) & \": \" & {mill('A1')} & IF ( ISBLANK ( A2 ), \"\", \" · \" & ( Anio - 2 ) & \": \" & {mill('A2')} ) ) )",
        'VAR N1 = SWITCH ( TRUE (), ISBLANK ( C ), "Sin año anterior", ABS ( C ) < 0.02, "Plano: no es tendencia", '
        'Lect = "Crece (sostenido)", "Crece frente a dos años", Lect = "Cae (sostenido)", "Cae frente a dos años", "Rebote: no es tendencia" )',
        'VAR N2 = "Igual en todos los grupos"',
        'VAR N3 = "Parejo en toda la cadena"',
        'VAR N4 = "Ticket ref. ID: $" & SUBSTITUTE ( FORMAT ( [Ticket Promedio (ID dataset)], "#,0" ), ",", "." ) & " ⓘ"',
        f"VAR Svg = {a_dax(plantilla_kpis())}",
        f"RETURN\n    {uri('Svg')}",
    ])


def dax_titulo_resumen(w=1110, h=60):
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}' font-family='{SERIF}'>"
           f"<text x='0' y='42' font-size='38' font-weight='700' fill='{TINTA}'>⟨T1⟩<tspan fill='{IDENT}'>⟨T2⟩</tspan>⟨T3⟩</text></svg>")
    return "\n".join([
        "VAR C = [Crecimiento Ventas Ene-Sep %]",
        'VAR P = IF ( C > 0, "+", IF ( C < 0, "−", "" ) ) & SUBSTITUTE ( FORMAT ( ABS ( C ) * 100, "0.0" ), ".", "," ) & " %"',
        'VAR T1 = SWITCH ( TRUE (), ISBLANK ( C ), "Seleccione un año con año anterior", ABS ( C ) < 0.02, "El negocio está plano (", C > 0, "El negocio crece (", "El negocio cae (" )',
        'VAR T2 = IF ( ISBLANK ( C ), "", P )',
        'VAR T3 = IF ( ISBLANK ( C ), "", "), pero las regiones se mueven" )',
        f"VAR Svg = {a_dax(svg)}",
        f"RETURN\n    {uri('Svg')}",
    ])


# ------------------------------------------------------------------ titulares y textos
DAX_TITULAR_PODIO = BLOQUE_REGIONES + """
VAR F1 = FILTER ( R, [@r] = 1 )
VAR N1 = MAXX ( F1, DimGeografia[Region] )
VAR RP1 = MAXX ( F1, [@rp] )
VAR NP = COUNTROWS ( TP )
RETURN
    SWITCH (
        TRUE (),
        ISBLANK ( Anio ), "Seleccione un solo año",
        ISBLANK ( N1 ), "Sin año anterior para comparar",
        ISBLANK ( RP1 ), N1 & " lidera el crecimiento",
        RP1 = 1, N1 & " repite en el primer puesto",
        RP1 = NP, N1 & " pasó del último puesto al primero",
        N1 & " subió del puesto " & RP1 & " al primero"
    )"""

DAX_TITULAR_POSICIONES = BLOQUE_REGIONES + """
VAR M = ADDCOLUMNS ( FILTER ( R, NOT ISBLANK ( [@rp] ) ), "@m", [@rp] - [@r] )
VAR MinM = MINX ( M, [@m] )
VAR Peores = FILTER ( M, [@m] = MinM )
VAR Nombres = CONCATENATEX ( Peores, DimGeografia[Region], " y ", DimGeografia[Region], ASC )
VAR Plural = COUNTROWS ( Peores ) > 1
RETURN
    SWITCH (
        TRUE (),
        ISBLANK ( Anio ), "Seleccione un solo año",
        ISEMPTY ( M ), "Sin tabla de " & ( Anio - 1 ) & " para comparar",
        MinM >= 0, "Ninguna región perdió puestos frente a " & ( Anio - 1 ),
        Nombres & IF ( Plural, " bajaron ", " bajó " ) & ( - MinM ) & IF ( MinM = -1, " puesto", " puestos" )
    )"""

DAX_KPI_VENTAS = 'VAR V = [Ventas Ene-Sep]\nRETURN\n    IF ( NOT ISBLANK ( V ), "$" & SUBSTITUTE ( FORMAT ( V / 1E6, "0.0" ), ".", "," ) & " M" )'
DAX_KPI_CREC = ("VAR C = [Crecimiento Ventas Ene-Sep %]\nRETURN\n    IF ( ISBLANK ( C ), \"—\", "
                "IF ( C > 0, \"▲ \", IF ( C < 0, \"▼ \", \"\" ) ) & SUBSTITUTE ( FORMAT ( ABS ( C ) * 100, \"0.00\" ), \".\", \",\" ) & \" %\" )")
DAX_KPI_MARGEN = 'SUBSTITUTE ( FORMAT ( [Margen Estimado %] * 100, "0.0" ), ".", "," ) & " %"'
DAX_KPI_QUIEBRE = 'SUBSTITUTE ( FORMAT ( [% Quiebre] * 100, "0.0" ), ".", "," ) & " %"'
DAX_KPI_LINEA = '"$" & SUBSTITUTE ( FORMAT ( [Venta por Linea], "#,0" ), ",", "." )'
DAX_NOTA_VENTAS = """VAR Anio = SELECTEDVALUE ( DimCalendario[Año] )
VAR A1 = CALCULATE ( [Ventas Ene-Sep], DimCalendario[Año] = Anio - 1 )
VAR A2 = CALCULATE ( [Ventas Ene-Sep], DimCalendario[Año] = Anio - 2 )
VAR F = ( x ) => x
RETURN
    IF (
        ISBLANK ( Anio ), "Seleccione un solo año",
        IF ( ISBLANK ( A1 ), "Primer año de la serie",
            ( Anio - 1 ) & ": $" & SUBSTITUTE ( FORMAT ( A1 / 1E6, "0.0" ), ".", "," ) & " M"
            & IF ( ISBLANK ( A2 ), "", " · " & ( Anio - 2 ) & ": $" & SUBSTITUTE ( FORMAT ( A2 / 1E6, "0.0" ), ".", "," ) & " M" )
        )
    )""".replace("VAR F = ( x ) => x\n", "")
DAX_NOTA_TICKET = '"Ticket ref. ID: $" & SUBSTITUTE ( FORMAT ( [Ticket Promedio (ID dataset)], "#,0" ), ",", "." ) & " ⓘ"'
DAX_CREC_ANTERIOR = "CALCULATE ( [Crecimiento Ventas Ene-Sep %], DATEADD ( DimCalendario[Fecha], -1, YEAR ) )"


# ------------------------------------------------------------------ KPI de las páginas internas y fidelización
def plantilla_kpis_n(etiquetas, paso, w, h=112, colores=None):
    o = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}' font-family='{FUENTE}'>"]
    for i, e in enumerate(etiquetas):
        x = i * paso
        if i:
            o.append(f"<line x1='{x - 16}' x2='{x - 16}' y1='0' y2='{h}' stroke='{BORDE}'/>")
        o.append(f"<text x='{x}' y='14' font-size='13' letter-spacing='2' font-weight='700' fill='{SEC}'>{e}</text>"
                 f"<g opacity='0' transform='translate(0,12)'>"
                 f"<animate attributeName='opacity' from='0' to='1' dur='.4s' begin='{i * .12:.2f}s' fill='freeze'/>"
                 f"<animateTransform attributeName='transform' type='translate' from='0 12' to='0 0' dur='.5s' begin='{i * .12:.2f}s' fill='freeze' calcMode='spline' keySplines='.2 .8 .2 1'/>"
                 f"<text x='{x}' y='68' font-family='{MONO}' font-size='44' font-weight='700' fill='{(colores or {}).get(i, TINTA)}'>⟨K{i}⟩</text></g>"
                 f"<text x='{x}' y='100' font-size='14' fill='{SEC}'>⟨N{i}⟩</text>")
    o.append("</svg>")
    return "".join(o)


KPI_INT_W, KPI_INT_PASO = 870, 290
PCT1 = lambda v: f'SUBSTITUTE ( FORMAT ( {v} * 100, "0.0" ), ".", "," ) & " %"'
MILL = lambda v: f'"$" & SUBSTITUTE ( FORMAT ( {v} / 1E6, "0.0" ), ".", "," ) & " M"'
ENTERO = lambda v: f'SUBSTITUTE ( FORMAT ( {v}, "#,0" ), ",", "." )'


def dax_kpis_promociones():
    # El tercer KPI era «Unidades por línea» (2,03): no respondía ninguna pregunta. Ahora compara el crecimiento
    # de las ventas con promoción frente a las ventas sin promoción (decisión D4: reasignar la inversión promocional).
    svg = plantilla_kpis_n(["VENTAS CON PROMOCIÓN", "MARGEN ESTIMADO", "CRECIMIENTO CON PROMOCIÓN"],
                           KPI_INT_PASO, KPI_INT_W)
    return "\n".join([
        f"VAR K0 = {PCT1('[% Ventas en Promocion]')}",
        f"VAR K1 = {PCT1('[Margen Estimado %]')}",
        "VAR CP = [Crecimiento Ventas en Promocion %]",
        "VAR SP = [Crecimiento Ventas sin Promocion %]",
        f'VAR K2 = IF ( ISBLANK ( CP ), "—", {pct_dax("CP")} )',
        f'VAR N0 = {MILL("[Ventas en Promocion]")} & " de " & {MILL("[Ventas Netas]")}',
        'VAR N1 = "Igual en todos los grupos"',
        f'VAR N2 = IF ( ISBLANK ( SP ), "Seleccione un año", "Sin promoción: " & {pct_dax("SP")} & " vs año ant." )',
        f"VAR Svg = {a_dax(svg)}",
        f"RETURN\n    {uri('Svg')}",
    ])


def dax_kpis_disponibilidad():
    svg = plantilla_kpis_n(["LÍNEAS CON QUIEBRE", "LÍNEAS AFECTADAS", "VENTAS CON QUIEBRE"], KPI_INT_PASO, KPI_INT_W,
                           colores={0: NAR})
    return "\n".join([
        f"VAR K0 = {PCT1('[% Quiebre]')}",
        f"VAR K1 = {ENTERO('[Lineas con Quiebre]')}",
        f"VAR K2 = {MILL('[Ventas con Quiebre]')}",
        'VAR N0 = "Estable: cerca de 8 % en 2024–2026"',
        f'VAR N1 = "de " & {ENTERO("[Lineas de Venta]")} & " líneas de venta"',
        'VAR N2 = "Registradas en quiebre; no son pérdidas"',
        f"VAR Svg = {a_dax(svg)}",
        f"RETURN\n    {uri('Svg')}",
    ])


FID_W, FID_H = 594, 362


def dax_fidelizacion(w=FID_W, h=FID_H):
    c1, c2 = w * 0.25, w * 0.75
    barra_y = 296
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}' font-family='{FUENTE}'>"
           f"<text x='0' y='16' font-size='13' letter-spacing='2' font-weight='700' fill='{SEC}'>FIDELIZADOS VS NO FIDELIZADOS</text>"
           f"<text x='0' y='50' font-family='{SERIF}' font-size='24' font-weight='700' fill='{TINTA}'>⟨TIT⟩</text>"
           f"<text x='{c1:.0f}' y='100' text-anchor='middle' font-size='13' letter-spacing='2' font-weight='700' fill='{IDENT}'>FIDELIZADOS</text>"
           f"<text x='{c2:.0f}' y='100' text-anchor='middle' font-size='13' letter-spacing='2' font-weight='700' fill='{SEC}'>NO FIDELIZADOS</text>"
           f"<text x='{w / 2:.0f}' y='178' text-anchor='middle' font-size='64' font-weight='300' fill='{GRIS}'>⟨SIG⟩</text>"
           f"<text x='{c1:.0f}' y='160' text-anchor='middle' font-family='{MONO}' font-size='40' font-weight='700' fill='{TINTA}'>⟨VS⟩</text>"
           f"<text x='{c2:.0f}' y='160' text-anchor='middle' font-family='{MONO}' font-size='40' font-weight='700' fill='{TINTA}'>⟨VN⟩</text>"
           f"<text x='{c1:.0f}' y='182' text-anchor='middle' font-size='13' fill='{SEC}'>venta por línea</text>"
           f"<text x='{c2:.0f}' y='182' text-anchor='middle' font-size='13' fill='{SEC}'>venta por línea</text>"
           f"<text x='{c1:.0f}' y='236' text-anchor='middle' font-family='{MONO}' font-size='28' font-weight='700' fill='{TINTA}'>⟨MS⟩</text>"
           f"<text x='{c2:.0f}' y='236' text-anchor='middle' font-family='{MONO}' font-size='28' font-weight='700' fill='{TINTA}'>⟨MN⟩</text>"
           f"<text x='{c1:.0f}' y='256' text-anchor='middle' font-size='13' fill='{SEC}'>margen estimado</text>"
           f"<text x='{c2:.0f}' y='256' text-anchor='middle' font-size='13' fill='{SEC}'>margen estimado</text>"
           f"<rect x='0' y='{barra_y}' width='{w}' height='18' rx='3' fill='#C9C2B3'/>"
           f"<rect x='0' y='{barra_y}' width='0' height='18' rx='3' fill='{IDENT}'>"
           f"<animate attributeName='width' from='0' to='⟨FORMAT ( PS * {w}, \"0.0\", \"en-US\" )⟩' dur='.9s' fill='freeze' calcMode='spline' keySplines='.2 .8 .2 1'/></rect>"
           f"<text x='0' y='{barra_y + 42}' font-size='14' fill='{TINTA}'><tspan font-weight='700'>⟨PST⟩</tspan> de las ventas ene–sep</text>"
           f"<text x='{w}' y='{barra_y + 42}' text-anchor='end' font-size='14' fill='{SEC}'><tspan font-weight='700'>⟨PNT⟩</tspan></text></svg>")
    return "\n".join([
        'VAR FS = DimCondicionVenta[Cliente fidelizado] = "Sí"',
        'VAR VLS = CALCULATE ( [Venta por Linea], DimCondicionVenta[Cliente fidelizado] = "Sí" )',
        'VAR VLN = CALCULATE ( [Venta por Linea], DimCondicionVenta[Cliente fidelizado] = "No" )',
        'VAR MGS = CALCULATE ( [Margen Estimado %], DimCondicionVenta[Cliente fidelizado] = "Sí" )',
        'VAR MGN = CALCULATE ( [Margen Estimado %], DimCondicionVenta[Cliente fidelizado] = "No" )',
        'VAR PS = DIVIDE ( CALCULATE ( [Ventas Ene-Sep], DimCondicionVenta[Cliente fidelizado] = "Sí" ), [Ventas Ene-Sep] )',
        "VAR Dif = DIVIDE ( VLS - VLN, VLN )",
        'VAR Igual = ABS ( Dif ) < 0.02 && ABS ( MGS - MGN ) < 0.01',
        'VAR TIT = IF ( Igual, "Misma venta por línea y mismo margen", "La venta por línea difiere " & SUBSTITUTE ( FORMAT ( ABS ( Dif ) * 100, "0.0" ), ".", "," ) & " %" )',
        'VAR SIG = IF ( Igual, "=", "≠" )',
        f"VAR VS = {ENTERO('VLS').replace('SUBSTITUTE', '\"$\" & SUBSTITUTE', 1)}",
        f"VAR VN = {ENTERO('VLN').replace('SUBSTITUTE', '\"$\" & SUBSTITUTE', 1)}",
        f"VAR MS = {PCT1('MGS')}",
        f"VAR MN = {PCT1('MGN')}",
        f'VAR PST = SUBSTITUTE ( FORMAT ( PS * 100, "0" ), ".", "," ) & " %"',
        f'VAR PNT = SUBSTITUTE ( FORMAT ( ( 1 - PS ) * 100, "0" ), ".", "," ) & " % no fidelizados"',
        f"VAR Svg = {a_dax(svg)}",
        f"RETURN\n    {uri('Svg')}",
    ]).replace('VAR FS = DimCondicionVenta[Cliente fidelizado] = "Sí"\n', '')


def medidas():
    """(carpeta, nombre, DAX, formato, categoría de datos)."""
    c = "8. Diseño (SVG y textos)"
    return [
        ("3. Tiempo (Ene-Sep)", "Crecimiento Año Anterior %", DAX_CREC_ANTERIOR, "0.00%;-0.00%;0.00%", None),
        (c, "SVG Podio", dax_podio(), None, "ImageUrl"),
        (c, "SVG Posiciones", dax_posiciones(), None, "ImageUrl"),
        (c, "SVG Tiquete", dax_tiquete(), None, "ImageUrl"),
        (c, "SVG KPIs", dax_kpis(), None, "ImageUrl"),
        (c, "SVG Titulo Resumen", dax_titulo_resumen(), None, "ImageUrl"),
        (c, "SVG KPIs Promociones", dax_kpis_promociones(), None, "ImageUrl"),
        (c, "SVG KPIs Disponibilidad", dax_kpis_disponibilidad(), None, "ImageUrl"),
        (c, "SVG Fidelizacion", dax_fidelizacion(), None, "ImageUrl"),
    ]


if __name__ == "__main__":
    for carpeta, n, d, f, cat in medidas():
        print(f"--- {n} ({len(d)} car.)")
    print(dax_tiquete())
