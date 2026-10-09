"""Genera las imágenes de fondo (1920 x 1080) del rediseño "tiquete + editorial".

Solo formas: papel con grano, reglas editoriales, líneas bajo los segmentadores y el papel del tiquete.
Todo texto y toda cifra son visuales de Power BI encima (ver generar_reporte_pbir.py).

Uso:  python scripts/pbip/recursos/fondos.py      (requiere: pip install playwright)
"""
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PAPEL, TARJETA, TINTA, BORDE, IDENT = "#F5F0E6", "#FFFDF8", "#1E2B2F", "#E2DACB", "#0E4D64"
W, H = 1920, 1080

GRANO = ("url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'>"
         "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/>"
         "<feColorMatrix values='0 0 0 0 0.35  0 0 0 0 0.3  0 0 0 0 0.2  0 0 0 .06 0'/></filter>"
         "<rect width='100%' height='100%' filter='url(%23n)'/></svg>\")")

CSS = f"""*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;overflow:hidden;background:{PAPEL};background-image:{GRANO}}}
.a{{position:absolute}} .r3{{position:absolute;height:3px;background:{TINTA}}} .r1{{position:absolute;height:1px;background:{TINTA}}}
.v1{{position:absolute;width:1px;background:{BORDE}}} .s{{position:absolute;height:1.5px;background:{TINTA}}}
.tiquete{{position:absolute;background:{TARJETA};box-shadow:0 18px 40px rgba(60,50,30,.12)}}
.zz{{position:absolute;left:0;width:100%;height:14px;background:linear-gradient(-45deg,{PAPEL} 7px,transparent 0),
  linear-gradient(45deg,{PAPEL} 7px,transparent 0);background-size:14px 14px}}"""

# Retícula y cabecera comunes (deben coincidir con generar_reporte_pbir.py)
SLICER_X = [1196 + i * 168 for i in range(4)]
SLICER_W = 152


def cabecera(slicers=True):
    s = "".join(f'<div class="s" style="left:{x}px;top:104px;width:{SLICER_W}px"></div>' for x in SLICER_X) if slicers else ""
    return (f'<div class="r3" style="left:60px;top:24px;width:1800px"></div>{s}'
            f'<div class="r1" style="left:60px;top:150px;width:1800px"></div>')


def portada():
    return (f'<div class="r3" style="left:60px;top:56px;width:1800px"></div>'
            f'<div class="r1" style="left:60px;top:102px;width:1800px"></div>'
            f'<div class="a" style="left:60px;top:676px;width:120px;height:6px;background:{IDENT}"></div>'
            f'<div class="tiquete" style="left:1196px;top:128px;width:664px;height:860px">'
            f'<div class="zz" style="top:-1px;transform:rotate(180deg)"></div><div class="zz" style="bottom:-1px"></div></div>')


def resumen():
    return (cabecera()
            + '<div class="r1" style="left:60px;top:318px;width:1800px"></div>'
            + '<div class="v1" style="left:1020px;top:338px;height:470px"></div>'
            + '<div class="r1" style="left:60px;top:826px;width:1800px"></div>'
            + '<div class="v1" style="left:1220px;top:846px;height:214px"></div>')


FONDOS = {
    "fondo_portada.png": portada(),
    "fondo_resumen.png": resumen(),
    "fondo_interna.png": cabecera(),
    "fondo_sin_filtros.png": cabecera(slicers=False),
}


def con_reglas(reglas, slicers=True):
    """Cabecera + una regla fina sobre cada bloque (x, y, ancho) de una página interna."""
    r = "".join(f'<div class="r1" style="left:{x}px;top:{y}px;width:{w}px;opacity:.55"></div>' for x, y, w in reglas)
    return cabecera(slicers) + r


def generar(archivos):
    """archivos: {nombre_png: cuerpo_html}. Requiere playwright."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        pag = nav.new_page(viewport={"width": W, "height": H})
        for nombre, cuerpo in archivos.items():
            pag.set_content(f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{cuerpo}</body></html>")
            pag.wait_for_timeout(200)
            pag.screenshot(path=str(AQUI / nombre))
            print("✓", nombre)
        nav.close()


def main():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        pag = nav.new_page(viewport={"width": W, "height": H})
        for nombre, cuerpo in FONDOS.items():
            pag.set_content(f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{cuerpo}</body></html>")
            pag.wait_for_timeout(200)
            pag.screenshot(path=str(AQUI / nombre))
            print("✓", nombre)
        nav.close()


if __name__ == "__main__":
    main()
