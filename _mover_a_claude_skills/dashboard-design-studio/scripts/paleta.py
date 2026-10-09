"""Valida y genera paletas para dashboards (sin dependencias externas).

Usos:
  # Validar una paleta: contraste WCAG contra el fondo y entre texto/fondo, y daltonismo
  python paleta.py --fondo "#F7F4EE" --texto "#1E2A2F" --colores "#0F5C4D,#E3A33B,#2E7D32,#C62828"

  # Generar la escala tonal (OKLCH) de un color de identidad
  python paleta.py --escala "#0F5C4D"

  # Ambas cosas y salida JSON (para guardar en el brief)
  python paleta.py --fondo "#FFFFFF" --texto "#222222" --colores "#1F3A5F,#8FA8C8" --escala "#1F3A5F" --json

Criterios: texto >= 4.5:1 (AA), elementos gráficos >= 3:1 contra el fondo, colores categóricos con
diferencia CIE76 dE >= 10 en visión normal y con deuteranopia/protanopia/tritanopia (Machado et al., 2009).
"""
import argparse
import json
import math
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ------------------------------------------------------------------ conversiones
def hex_a_rgb(h):
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        raise ValueError(f"Color inválido: #{h}")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def rgb_a_hex(rgb):
    return "#" + "".join(f"{round(min(1, max(0, c)) * 255):02X}" for c in rgb)


def a_lineal(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def a_srgb(c):
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def luminancia(rgb):
    r, g, b = (a_lineal(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(a, b):
    la, lb = sorted((luminancia(a), luminancia(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def rgb_a_lab(rgb):
    r, g, b = (a_lineal(c) for c in rgb)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 1.0
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116
    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def delta_e(a, b):
    return math.dist(rgb_a_lab(a), rgb_a_lab(b))


def rgb_a_oklab(rgb):
    r, g, b = (a_lineal(c) for c in rgb)
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = (math.copysign(abs(v) ** (1 / 3), v) for v in (l, m, s))
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def oklab_a_rgb_lineal(L, a, b):
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
            -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
            -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)


def oklch(rgb):
    L, a, b = rgb_a_oklab(rgb)
    return L, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360


def desde_oklch(L, C, H):
    """Convierte OKLCH a sRGB reduciendo el croma hasta que quepa en la gama."""
    for _ in range(60):
        a, b = C * math.cos(math.radians(H)), C * math.sin(math.radians(H))
        lin = oklab_a_rgb_lineal(L, a, b)
        if all(-1e-4 <= c <= 1 + 1e-4 for c in lin):
            return tuple(a_srgb(min(1, max(0, c))) for c in lin)
        C *= 0.95
    return tuple(a_srgb(min(1, max(0, c))) for c in lin)


# ------------------------------------------------------------------ daltonismo (Machado 2009, severidad 1)
MATRICES = {
    "deuteranopia": ((0.367322, 0.860646, -0.227968), (0.280085, 0.672501, 0.047413), (-0.011820, 0.042940, 0.968881)),
    "protanopia": ((0.152286, 1.052583, -0.204868), (0.114503, 0.786281, 0.099216), (-0.003882, -0.048116, 1.051998)),
    "tritanopia": ((1.255528, -0.076749, -0.178779), (-0.078411, 0.930809, 0.147602), (0.004733, 0.691367, 0.303900)),
}


def simular(rgb, tipo):
    lin = [a_lineal(c) for c in rgb]
    out = [sum(m * c for m, c in zip(fila, lin)) for fila in MATRICES[tipo]]
    return tuple(a_srgb(min(1, max(0, c))) for c in out)


# ------------------------------------------------------------------ reportes
def validar(fondo, texto, colores, umbral_de=10.0):
    res = {"fondo": fondo, "texto": texto, "colores": [], "pares_confusos": [], "aprobado": True}
    f = hex_a_rgb(fondo)
    if texto:
        c = contraste(hex_a_rgb(texto), f)
        res["texto_vs_fondo"] = round(c, 2)
        if c < 4.5:
            res["aprobado"] = False
    for h in colores:
        rgb = hex_a_rgb(h)
        L, C, H = oklch(rgb)
        c = contraste(rgb, f)
        fila = {"color": h.upper(), "contraste_fondo": round(c, 2), "grafico_ok(>=3)": c >= 3,
                "texto_ok(>=4.5)": c >= 4.5, "oklch": [round(L, 3), round(C, 3), round(H, 1)]}
        if c < 3:
            res["aprobado"] = False
        res["colores"].append(fila)
    rgbs = [hex_a_rgb(h) for h in colores]
    for vision in ["normal", *MATRICES]:
        sim = rgbs if vision == "normal" else [simular(c, vision) for c in rgbs]
        for i in range(len(sim)):
            for j in range(i + 1, len(sim)):
                d = delta_e(sim[i], sim[j])
                if d < umbral_de:
                    res["pares_confusos"].append({"vision": vision, "a": colores[i].upper(),
                                                  "b": colores[j].upper(), "dE": round(d, 1)})
    return res


def escala(base, pasos=(0.97, 0.93, 0.86, 0.76, 0.66, 0.56, 0.46, 0.37, 0.29, 0.22)):
    L0, C0, H = oklch(hex_a_rgb(base))
    out = []
    for L in pasos:
        # croma máximo en los tonos medios, menor en los extremos
        factor = max(0.15, 1 - abs(L - 0.55) * 1.6)
        rgb = desde_oklch(L, C0 * factor * 1.1, H)
        out.append({"L": round(L * 100), "hex": rgb_a_hex(rgb),
                    "contraste_blanco": round(contraste(rgb, (1, 1, 1)), 2),
                    "contraste_negro": round(contraste(rgb, (0, 0, 0)), 2)})
    return {"base": base.upper(), "oklch_base": [round(L0, 3), round(C0, 3), round(H, 1)], "escala": out}


def imprimir_validacion(r):
    print(f"\nFondo {r['fondo']}" + (f" · texto {r['texto']} → contraste {r['texto_vs_fondo']}:1 "
                                     f"{'OK' if r['texto_vs_fondo'] >= 4.5 else 'FALLA (< 4.5)'}" if r.get('texto') else ""))
    print(f"{'Color':9} {'Contraste':>9}  Gráfico≥3  Texto≥4.5   OKLCH (L, C, H)")
    for c in r["colores"]:
        print(f"{c['color']:9} {c['contraste_fondo']:>8}:1  {'sí' if c['grafico_ok(>=3)'] else 'NO':^9}  "
              f"{'sí' if c['texto_ok(>=4.5)'] else 'no':^9}   {c['oklch']}")
    if r["pares_confusos"]:
        print("\nPares difíciles de distinguir (dE < 10):")
        for p in r["pares_confusos"]:
            print(f"  [{p['vision']}] {p['a']} vs {p['b']}  dE={p['dE']}  → agregar signo/forma/etiqueta o cambiar luminosidad")
    else:
        print("\nSin pares confusos en visión normal ni con daltonismo.")
    print("\nRESULTADO:", "APROBADA" if r["aprobado"] and not r["pares_confusos"] else
          ("APROBADA CON ADVERTENCIAS" if r["aprobado"] else "NO APROBADA"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fondo", default="#FFFFFF")
    ap.add_argument("--texto")
    ap.add_argument("--colores", help="lista separada por comas")
    ap.add_argument("--escala", help="color base para generar la escala tonal")
    ap.add_argument("--umbral", type=float, default=10.0, help="dE mínimo entre colores (default 10)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if not a.colores and not a.escala:
        ap.error("indique --colores y/o --escala")
    salida = {}
    if a.colores:
        salida["validacion"] = validar(a.fondo, a.texto, [c.strip() for c in a.colores.split(",") if c.strip()],
                                       a.umbral)
    if a.escala:
        salida["escala"] = escala(a.escala)
    if a.json:
        print(json.dumps(salida, ensure_ascii=False, indent=2))
        return
    if "validacion" in salida:
        imprimir_validacion(salida["validacion"])
    if "escala" in salida:
        e = salida["escala"]
        print(f"\nEscala tonal de {e['base']} (OKLCH base {e['oklch_base']})")
        print(f"{'L':>4}  {'Hex':8} {'vs blanco':>9} {'vs negro':>9}")
        for p in e["escala"]:
            print(f"{p['L']:>4}  {p['hex']:8} {p['contraste_blanco']:>8}:1 {p['contraste_negro']:>8}:1")


if __name__ == "__main__":
    main()
