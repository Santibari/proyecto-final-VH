"""Fases 4 y 4.5 — Exploración y validación de los hallazgos candidatos (docs/02_problema.md §8).

Criterios de solidez:
  * Crecimiento: se compara ene–sep 2026 contra 2025 Y contra 2024. Un crecimiento es
    "tendencia" si es positivo frente a ambos años, y "rebote" si solo lo es frente a 2025.
  * Tasas (quiebre, margen): prueba z de proporciones de cada grupo contra el resto,
    con corrección de Bonferroni por el número de comparaciones de la familia.

Uso:  python scripts/validacion/04_validacion_hallazgos.py
"""
from math import erf, sqrt
from pathlib import Path
import sys

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
CSV = RAIZ / "data" / "raw" / "03_cadena_supermercados.csv"
sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 170)

df = pd.read_csv(CSV, encoding="utf-8-sig", parse_dates=["fecha"])
df["anio"] = df.fecha.dt.year
df["quiebre"] = (df.quiebre_stock_ult_7d == "Sí").astype(int)
comp = df[df.fecha.dt.month <= 9]


def titulo(t):
    print(f"\n{'=' * 70}\n{t}\n{'=' * 70}")


def p_normal(z):
    return 2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2))))


def tendencia(dim):
    p = comp.pivot_table(index=dim, columns="anio", values="venta_neta_cop", aggfunc="sum")
    p["vs_2025"] = p[2026] / p[2025] - 1
    p["vs_2024"] = p[2026] / p[2024] - 1
    p["dif_vs_2025"] = p[2026] - p[2025]
    p["lectura"] = p.apply(lambda r: "TENDENCIA +" if r.vs_2025 > 0.02 and r.vs_2024 > 0.02 else
                           "TENDENCIA -" if r.vs_2025 < -0.02 and r.vs_2024 < -0.02 else
                           "rebote/oscila" if abs(r.vs_2025) > 0.02 else "estable", axis=1)
    return p.sort_values("vs_2025", ascending=False)


def prueba_tasa(dims, columna="quiebre", n_min=0):
    g = df.groupby(dims).agg(n=(columna, "size"), k=(columna, "sum"))
    g = g[g.n >= n_min]
    total_n, total_k = len(df), df[columna].sum()
    resto_n, resto_k = total_n - g.n, total_k - g.k
    p1, p2 = g.k / g.n, resto_k / resto_n
    pc = (g.k + resto_k) / total_n
    z = (p1 - p2) / ((pc * (1 - pc) * (1 / g.n + 1 / resto_n)) ** 0.5)
    g["tasa"] = p1
    g["z"] = z
    g["p"] = z.apply(p_normal)
    g["p_bonf"] = (g.p * len(g)).clip(upper=1)
    return g.sort_values("tasa", ascending=False)


fmt = lambda x: f"{x:,.3f}" if abs(x) < 10 else f"{x:,.0f}"

titulo("H1/H2/H3 — Tendencia vs rebote (ventas ene–sep)")
for dim in ["region", "ciudad", "formato_tienda", "categoria", "canal", "promocion"]:
    print(f"\n--- {dim}")
    print(tendencia(dim)[[2024, 2025, 2026, "vs_2025", "vs_2024", "dif_vs_2025", "lectura"]]
          .to_string(float_format=fmt))

titulo("H3 — Región × formato (ene–sep 2026 vs 2025 y vs 2024, con n de líneas 2026)")
p = comp.pivot_table(index=["region", "formato_tienda"], columns="anio", values="venta_neta_cop", aggfunc="sum")
n26 = comp[comp.anio == 2026].groupby(["region", "formato_tienda"]).size()
p["vs_2025"] = p[2026] / p[2025] - 1
p["vs_2024"] = p[2026] / p[2024] - 1
p["lineas_2026"] = n26
print(p.sort_values("vs_2025")[["vs_2025", "vs_2024", "lineas_2026"]].to_string(float_format=fmt))

titulo("H7 — Quiebre por categoría (z contra el resto, Bonferroni k=8)")
print(prueba_tasa("categoria").round(4).to_string())
titulo("H7 — Quiebre por ciudad (Bonferroni k=12)")
print(prueba_tasa("ciudad").round(4).to_string())
titulo("H7 — Quiebre por formato (Bonferroni k=3)")
print(prueba_tasa("formato_tienda").round(4).to_string())
titulo("H7 — Quiebre ciudad × categoría (Bonferroni k=96) — top 10")
print(prueba_tasa(["ciudad", "categoria"]).head(10).round(4).to_string())
titulo("H7 — Quiebre categoría × formato (Bonferroni k=24) — top 6")
print(prueba_tasa(["categoria", "formato_tienda"]).head(6).round(4).to_string())

titulo("H8 — Quiebre por año (ene–sep) y por trimestre")
print(comp.groupby("anio").quiebre.agg(["mean", "size"]).round(4).to_string())
print(df.groupby(df.fecha.dt.to_period("Q")).quiebre.mean().round(4).to_string())

titulo("H5 — Margen % por grupo (rango)")
for dim in ["region", "formato_tienda", "categoria", "promocion", "canal", "medio_pago", "cliente_fidelizado"]:
    g = df.groupby(dim)[["venta_neta_cop", "costo_estimado_cop"]].sum()
    m = 1 - g.costo_estimado_cop / g.venta_neta_cop
    print(f"{dim:<20} {m.min():.2%} – {m.max():.2%}  (rango {100 * (m.max() - m.min()):.2f} pp)")

titulo("Estacionalidad mensual (ventas por mes, promedio de años con dato)")
mes = df.groupby([df.fecha.dt.month, "anio"]).venta_neta_cop.sum().unstack()
print(mes.to_string(float_format=fmt))
