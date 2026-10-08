"""Fase 1 — Perfilamiento de 03_cadena_supermercados.csv.

Recalcula desde el CSV original todas las cifras de control que se usan en
docs/01_perfilamiento.md y en las validaciones de Power BI. No modifica el CSV.

Uso:  python scripts/validacion/01_perfilamiento.py
"""
from pathlib import Path
import sys

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
CSV = RAIZ / "data" / "raw" / "03_cadena_supermercados.csv"

sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 20)


def titulo(texto):
    print(f"\n{'=' * 70}\n{texto}\n{'=' * 70}")


def pct_si(serie):
    return (serie == "Sí").mean()


df = pd.read_csv(CSV, encoding="utf-8-sig", parse_dates=["fecha"])
CATEGORICAS = ["ciudad", "departamento", "region", "formato_tienda", "categoria",
               "producto_generico", "promocion", "medio_pago", "cliente_fidelizado",
               "canal", "quiebre_stock_ult_7d"]
NUMERICAS = ["unidades", "precio_unitario_cop", "descuento_pct",
             "venta_neta_cop", "costo_estimado_cop"]

# ---------------------------------------------------------------- estructura
titulo("1. Estructura")
print(f"Filas: {len(df):,} | Columnas: {df.shape[1]}")
print(f"id_linea únicos: {df.id_linea.nunique():,}")
print(f"id_transaccion distintos: {df.id_transaccion.nunique():,}")
print(f"Faltantes: {int(df.isna().sum().sum())} | Filas duplicadas: {int(df.duplicated().sum())}")
print(f"Fechas: {df.fecha.min().date()} a {df.fecha.max().date()} "
      f"({df.fecha.dt.to_period('M').nunique()} meses, {df.fecha.nunique()} días con datos)")
crudo = pd.read_csv(CSV, encoding="utf-8-sig", dtype=str, keep_default_na=False)
CENTINELAS = ["NA", "N/A", "NULL", "null", "None", "nan", "-", "?", "ND", "Sin dato", "Desconocido"]
ocultos = {c: int((crudo[c].isin(CENTINELAS) | (crudo[c] != crudo[c].str.strip())).sum())
           for c in crudo.columns}
print(f"Celdas vacías: {int((crudo == '').sum().sum())} | "
      f"textos centinela o con espacios sobrantes: {sum(ocultos.values())}")
print(f"descuento_pct = 0: {(df.descuento_pct == 0).sum():,} | "
      f"líneas 'Sin promoción': {(df.promocion == 'Sin promoción').sum():,}")
print("\nTipos inferidos:")
print(df.dtypes.astype(str).to_string())

# ------------------------------------------------------------- categóricas
titulo("2. Variables categóricas (cardinalidad y frecuencias)")
for col in CATEGORICAS:
    vc = df[col].value_counts()
    print(f"\n{col} — {len(vc)} valores")
    print((vc.to_frame("lineas").assign(pct=lambda t: (t.lineas / len(df) * 100).round(2))).to_string())

# ---------------------------------------------------------------- numéricas
titulo("3. Variables numéricas")
print(df[NUMERICAS].describe(percentiles=[.01, .25, .5, .75, .99]).T.round(2).to_string())
print(f"\nValores <= 0: { {c: int((df[c] <= 0).sum()) for c in NUMERICAS if c != 'descuento_pct'} }")
print(f"Valores de unidades: {sorted(df.unidades.unique())}")

# ----------------------------------------------------------- totales control
titulo("4. Cifras de control (deben coincidir en Power BI)")
ventas = df.venta_neta_cop.sum()
costo = df.costo_estimado_cop.sum()
print(f"Ventas netas:      {ventas:,}")
print(f"Costo estimado:    {costo:,}")
print(f"Margen estimado:   {ventas - costo:,}  ({(ventas - costo) / ventas:.4%})")
print(f"Unidades:          {df.unidades.sum():,}")
print(f"Líneas con quiebre:{(df.quiebre_stock_ult_7d == 'Sí').sum():,}  ({pct_si(df.quiebre_stock_ult_7d):.4%})")
print(f"Líneas fidelizadas:{(df.cliente_fidelizado == 'Sí').sum():,}  ({pct_si(df.cliente_fidelizado):.4%})")
print(f"Venta por línea:   {ventas / len(df):,.2f}")
print(f"Máx descuento_pct: {df.descuento_pct.max()}")

# --------------------------------------------------------------- fechas
titulo("5. Cobertura temporal")
anio = df.fecha.dt.year
print(df.groupby(anio).agg(lineas=("id_linea", "count"), ventas=("venta_neta_cop", "sum"),
                           meses=("fecha", lambda s: s.dt.month.nunique()),
                           desde=("fecha", "min"), hasta=("fecha", "max")).to_string())
comp = df[df.fecha.dt.month <= 9].groupby(anio[df.fecha.dt.month <= 9]).venta_neta_cop.sum()
print("\nPeriodo comparable ene–sep:")
print(comp.to_string())
print(f"Var 2025 vs 2024: {comp[2025] / comp[2024] - 1:+.4%} | Var 2026 vs 2025: {comp[2026] / comp[2025] - 1:+.4%}")
print(f"Año completo 2026 vs 2025 (INCORRECTO, solo referencia): "
      f"{df[anio == 2026].venta_neta_cop.sum() / df[anio == 2025].venta_neta_cop.sum() - 1:+.2%}")
lin_mes = df.groupby(df.fecha.dt.to_period("M")).size()
print(f"\nLíneas por mes: min {lin_mes.min()}, max {lin_mes.max()}, media {lin_mes.mean():.0f}")
todas = pd.date_range(df.fecha.min(), df.fecha.max())
print(f"Días del rango sin ventas: {len(todas.difference(df.fecha.unique()))}")

# --------------------------------------------------------- consistencias
titulo("6. Reglas de consistencia")
calc = df.unidades * df.precio_unitario_cop * (1 - df.descuento_pct / 100)
dif = df.venta_neta_cop - calc
print(f"venta_neta = unidades*precio*(1-desc): {(dif.abs() <= 2).sum():,} exactas (±2 COP); "
      f"{(dif.abs() > 2).sum():,} con diferencia; diferencia relativa máx "
      f"{(dif / calc).abs().max():.4%}")
print(f"Sin promoción con descuento > 0: {((df.promocion == 'Sin promoción') & (df.descuento_pct > 0)).sum()}")
print(f"Con promoción y descuento = 0:   {((df.promocion != 'Sin promoción') & (df.descuento_pct == 0)).sum()}")
print("Descuento por tipo de promoción:")
print(df.groupby("promocion").descuento_pct.describe().round(2).to_string())
ratio = df.costo_estimado_cop / df.venta_neta_cop
print(f"\nCosto > venta: {(df.costo_estimado_cop > df.venta_neta_cop).sum()} | "
      f"costo/venta min {ratio.min():.3f}, max {ratio.max():.3f}")
print(f"Ciudades con >1 departamento: {(df.groupby('ciudad').departamento.nunique() > 1).sum()} | "
      f"con >1 región: {(df.groupby('ciudad').region.nunique() > 1).sum()}")
print("Ciudad → departamento → región:")
print(df[["region", "departamento", "ciudad"]].drop_duplicates().sort_values(["region", "ciudad"]).to_string(index=False))
print(f"\nproducto_generico distintos por categoría: "
      f"{df.groupby('categoria').producto_generico.nunique().to_dict()}")
print(f"Combinaciones ciudad × formato: {df.groupby(['ciudad', 'formato_tienda']).ngroups}")

# ------------------------------------------------------ id_transaccion
titulo("7. Prueba de id_transaccion (¿representa una compra?)")
n = df.groupby("id_transaccion").size()
multi = df[df.id_transaccion.isin(n[n > 1].index)]
print(f"IDs con 1 línea: {(n == 1).sum():,} | IDs con >1 línea: {(n > 1).sum():,} | máx líneas por ID: {n.max()}")
atributos = ["fecha", "ciudad", "formato_tienda", "canal", "medio_pago", "cliente_fidelizado"]
inconsist = multi.groupby("id_transaccion")[atributos].nunique().gt(1)
for a in atributos:
    print(f"  IDs multilínea con más de un valor de {a:<20}: {inconsist[a].sum():,} de {len(inconsist):,}")
print(f"  IDs multilínea totalmente consistentes: {(~inconsist.any(axis=1)).sum():,}")
dias = multi.groupby("id_transaccion").fecha.agg(lambda s: (s.max() - s.min()).days)
print(f"  Separación entre la primera y la última fecha del mismo ID: mediana {dias.median():.0f} días, máx {dias.max()}")
print("\nEjemplo T-0003774:")
print(df[df.id_transaccion == "T-0003774"][["id_linea", "fecha", "ciudad", "formato_tienda",
                                            "canal", "medio_pago", "venta_neta_cop"]].to_string(index=False))
print(f"\nReferencia (guía): Transacciones = {df.id_transaccion.nunique():,}; "
      f"Ticket promedio = {ventas / df.id_transaccion.nunique():,.2f}")
print(f"Correlación número de ID vs fecha: {df.id_transaccion.str[2:].astype(int).corr(df.fecha.astype('int64')):.4f}")
print(f"Grupos id_transaccion + fecha: {df.groupby(['id_transaccion', 'fecha']).ngroups:,} (≈ 1 por línea)")
print("\nTicket por ID segmentado por región (prueba de incoherencia):")
t = df.groupby("region").agg(ventas=("venta_neta_cop", "sum"), tx=("id_transaccion", "nunique"),
                             lineas=("id_linea", "count"))
t["ticket_id"] = (t.ventas / t.tx).round(0)
t["venta_linea"] = (t.ventas / t.lineas).round(0)
print(t.to_string())
print(f"Suma de transacciones por región: {t.tx.sum():,} vs total {df.id_transaccion.nunique():,}")

# ----------------------------------------------------- señal por dimensión
titulo("8. Variación entre grupos (insumo para la regla de materialidad)")
for col in ["region", "formato_tienda", "categoria", "promocion", "canal", "medio_pago", "cliente_fidelizado"]:
    g = df.groupby(col).agg(lineas=("id_linea", "count"), ventas=("venta_neta_cop", "sum"),
                            costo=("costo_estimado_cop", "sum"),
                            quiebre=("quiebre_stock_ult_7d", pct_si),
                            venta_linea=("venta_neta_cop", "mean"))
    g["margen_pct"] = 1 - g.costo / g.ventas
    print(f"\n{col}: margen% {g.margen_pct.min():.2%}–{g.margen_pct.max():.2%} | "
          f"quiebre {g.quiebre.min():.2%}–{g.quiebre.max():.2%} | "
          f"venta/línea {g.venta_linea.min():,.0f}–{g.venta_linea.max():,.0f}")
