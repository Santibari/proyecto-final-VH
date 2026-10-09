"""Renderiza un mockup HTML a PNG al tamaño del lienzo de Power BI y genera vistas de control.

Requisito: pip install playwright  (y una vez: python -m playwright install chromium)

Uso:
  python render_mockup.py propuesta_a.html                 # → propuesta_a.png
  python render_mockup.py propuesta_a.html --grid --squint --gris
  python render_mockup.py propuesta_a.html --sin-overlays  # → propuesta_a_fondo.png (para el fondo de página)
  python render_mockup.py propuesta_a.html --posiciones    # → propuesta_a_posiciones.json

Convención en el HTML del mockup:
  Todo elemento que en Power BI será un VISUAL NATIVO (texto editable, tarjeta, gráfico, botón) lleva
  el atributo  data-pbi="NombreVisual"  (p. ej. data-pbi="KpiVentas").
  --sin-overlays los oculta para obtener la imagen de fondo (solo formas).
  --posiciones exporta x, y, ancho y alto de cada uno, listos para pbi-report-builder.

Opciones:
  --ancho/--alto   tamaño del lienzo (default 1920 x 1080)
  --grid           superpone la retícula de 12 columnas (margen 60, medianil 24) y líneas cada 8 px
  --squint         versión desenfocada (prueba de entrecerrar los ojos: ¿se ve la jerarquía?)
  --gris           versión en escala de grises (¿la jerarquía sobrevive sin color?)
  --miniatura      versión de 320 px de ancho
"""
import argparse
import json
from pathlib import Path

GRID_JS = """
([ancho, alto, margen, medianil, cols]) => {
  const g = document.createElement('div');
  g.style.cssText = `position:fixed;inset:0;pointer-events:none;z-index:2147483647`;
  const colW = (ancho - 2*margen - (cols-1)*medianil) / cols;
  for (let i = 0; i < cols; i++) {
    const c = document.createElement('div');
    c.style.cssText = `position:absolute;top:0;height:${alto}px;left:${margen + i*(colW+medianil)}px;` +
      `width:${colW}px;background:rgba(255,0,90,.08);border-left:1px solid rgba(255,0,90,.35);` +
      `border-right:1px solid rgba(255,0,90,.35)`;
    g.appendChild(c);
  }
  const l = document.createElement('div');
  l.style.cssText = `position:absolute;inset:0;background-image:linear-gradient(rgba(0,150,255,.12) 1px, transparent 1px);` +
    `background-size:100% 8px`;
  g.appendChild(l);
  document.body.appendChild(g);
}
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html")
    ap.add_argument("--ancho", type=int, default=1920)
    ap.add_argument("--alto", type=int, default=1080)
    ap.add_argument("--grid", action="store_true")
    ap.add_argument("--squint", action="store_true")
    ap.add_argument("--gris", action="store_true")
    ap.add_argument("--miniatura", action="store_true")
    ap.add_argument("--sin-overlays", action="store_true")
    ap.add_argument("--posiciones", action="store_true")
    a = ap.parse_args()

    from playwright.sync_api import sync_playwright

    src = Path(a.html).resolve()
    base = src.with_suffix("")
    salidas = []
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        pag = nav.new_page(viewport={"width": a.ancho, "height": a.alto})
        pag.goto(src.as_uri())
        pag.wait_for_load_state("networkidle")

        def captura(sufijo, css=None, js=None, arg=None, escala=None):
            if css:
                h = pag.add_style_tag(content=css)
            if js:
                pag.evaluate(js, arg)
            ruta = f"{base}{sufijo}.png"
            if escala:
                p2 = nav.new_page(viewport={"width": a.ancho, "height": a.alto}, device_scale_factor=escala)
                p2.goto(src.as_uri())
                p2.wait_for_load_state("networkidle")
                p2.screenshot(path=ruta)
                p2.close()
            else:
                pag.screenshot(path=ruta)
            salidas.append(ruta)
            if css:
                h.evaluate("e => e.remove()")

        captura("")
        if a.posiciones:
            pos = pag.evaluate("""() => [...document.querySelectorAll('[data-pbi]')].map(e => {
                const r = e.getBoundingClientRect();
                return {visual: e.dataset.pbi, x: Math.round(r.x), y: Math.round(r.y),
                        width: Math.round(r.width), height: Math.round(r.height)};
            })""")
            ruta = f"{base}_posiciones.json"
            Path(ruta).write_text(json.dumps(pos, ensure_ascii=False, indent=2), encoding="utf-8")
            salidas.append(ruta)
            fuera = [p for p in pos if p["x"] != 0 and (p["x"] - 60) % 152 != 0]
            if fuera:
                print("Aviso: visuales que no empiezan en borde de columna (x = 60 + n·152):",
                      ", ".join(f"{p['visual']}(x={p['x']})" for p in fuera))
        if a.squint:
            captura("_squint", css="body{filter:blur(10px)}")
        if a.gris:
            captura("_gris", css="html{filter:grayscale(1)}")
        if a.miniatura:
            captura("_miniatura", escala=320 / a.ancho)
        if a.sin_overlays:
            captura("_fondo", css="[data-pbi]{visibility:hidden !important}")
        if a.grid:
            captura("_grid", js=GRID_JS, arg=[a.ancho, a.alto, 60, 24, 12])
        nav.close()
    print("\n".join(salidas))


if __name__ == "__main__":
    main()
