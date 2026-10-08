"""Fase 2 — Evidencia preliminar para formular el problema y las preguntas.

Verifica que cada pregunta analítica tenga datos suficientes para responderse.
No son hallazgos definitivos: se validan en las Fases 4 y 4.5.
Periodo comparable: enero–septiembre de cada año.

Uso:  python scripts/validacion/02_evidencia_problema.py
"""
from pathlib import Path
import sys

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
CSV = RAIZ / "data" / "raw" / "03_cadena_supermercados.csv"

sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 160)

df = pd.read_csv(CSV, encoding="utf-8-sig", parse_dates=["fecha"])
df["anio"] = df.fecha.dt.year
df["quiebre"] = (df.quiebre_stock_ult_7d == "Sí").astype(int)
comp = df[df.fecha.dt.month <= 9]


def titulo(texto):
    print(f"\n{'=' * 70}\n{texto}\n{'=' * 70}")


def crecimiento(dim):
    """Ventas ene–sep por año, variación 2026 vs 2025 y participación 2026."""
    p = comp.pivot_table(index=dim, columns="anio", values="venta_neta_cop", aggfunc="sum")
    p["var_26_25"] = p[2026] / p[2025] - 1
    p["var_25_24"] = p[2025] / p[2024] - 1
    p["dif_abs_26_25"] = p[2026] - p[2025]
    p["part_2026"] = p[2026] / p[2026].sum()
    return p.sort_values("var_26_25", ascending=False)


# ------------------------------------------------------------------ P1
titulo("P1. Crecimiento ene–sep por dimensión")
tot = comp.groupby("anio").venta_neta_cop.sum()
print(f"Total: 2024 {tot[2024]:,} | 2025 {tot[2025]:,} | 2026 {tot[2026]:,} "
      f"| var 26/25 {tot[2026] / tot[2025] - 1:+.2%}")
for dim in ["region", "ciudad", "formato_tienda", "categoria"]:
    print(f"\n--- {dim}")
    print(crecimiento(dim).to_string(float_format=lambda x: f"{x:,.3f}" if abs(x) < 10 else f"{x:,.0f}"))

titulo("P1. Región × formato (var 26/25, ene–sep)")
p = comp.pivot_table(index=["region", "formato_tienda"], columns="anio",
                     values="venta_neta_cop", aggfunc="sum")
p["var_26_25"] = p[2026] / p[2025] - 1
print(p["var_26_25"].unstack().round(3).to_string())

# ------------------------------------------------------------------ P2
titulo("P2. Mix y crecimiento por palancas comerciales (ene–sep)")
for dim in ["promocion", "canal", "medio_pago", "cliente_fidelizado"]:
    print(f"\n--- {dim}")
    print(crecimiento(dim)[["var_26_25", "var_25_24", "part_2026"]].round(3).to_string())

titulo("P2. Participación de promoción por categoría (total del periodo)")
mix = df.assign(con_promo=df.promocion != "Sin promoción") \
        .groupby("categoria").apply(lambda g: pd.Series({
            "pct_ventas_promo": g.loc[g.con_promo, "venta_neta_cop"].sum() / g.venta_neta_cop.sum(),
            "margen_pct": 1 - g.costo_estimado_cop.sum() / g.venta_neta_cop.sum(),
            "venta_linea": g.venta_neta_cop.mean()}), include_groups=False)
print(mix.round(3).to_string())

titulo("P2. Canal × formato: participación 2026 y var 26/25")
p = comp.pivot_table(index=["formato_tienda", "canal"], columns="anio",
                     values="venta_neta_cop", aggfunc="sum")
p["var_26_25"] = p[2026] / p[2025] - 1
print(p[["var_26_25"]].round(3).unstack().to_string())

# ------------------------------------------------------------------ P3
titulo("P3. Quiebre de stock: tasa, líneas y ventas afectadas")
for dim in ["categoria", "formato_tienda", "ciudad", "region"]:
    g = df.groupby(dim).agg(lineas=("id_linea", "count"), lin_quiebre=("quiebre", "sum"),
                            ventas_quiebre=("venta_neta_cop", lambda s: s[df.loc[s.index, "quiebre"] == 1].sum()))
    g["tasa"] = g.lin_quiebre / g.lineas
    print(f"\n--- {dim}")
    print(g.sort_values("tasa", ascending=False).round(4).to_string())

titulo("P3. Focos categoría × formato (tasa de quiebre, n líneas)")
g = df.groupby(["categoria", "formato_tienda"]).agg(n=("id_linea", "count"), tasa=("quiebre", "mean"))
print(g.sort_values("tasa", ascending=False).head(8).round(4).to_string())
print(f"Tasa global: {df.quiebre.mean():.4f}")

titulo("P3. Focos ciudad × categoría (n >= 300)")
g = df.groupby(["ciudad", "categoria"]).agg(n=("id_linea", "count"), tasa=("quiebre", "mean"))
print(g[g.n >= 300].sort_values("tasa", ascending=False).head(10).round(4).to_string())

titulo("P3. Evolución del quiebre por año (ene–sep)")
print(comp.groupby("anio").quiebre.mean().round(4).to_string())
