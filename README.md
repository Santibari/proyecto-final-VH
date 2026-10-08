# Proyecto final BI 2026-2 — Grupo 3: Cadena nacional de supermercados

Dashboard interactivo en Power BI para la gerencia de tiendas y de categoría.
Hoja de ruta: [.claude/Plan_Implementacion_Claude_PowerBI_V3.md](.claude/Plan_Implementacion_Claude_PowerBI_V3.md).

## Estructura

| Carpeta | Contenido |
|---|---|
| `data/raw/` | `03_cadena_supermercados.csv`: dataset original (solo lectura, no se modifica). |
| `docs/` | Entregables de cada fase (perfilamiento, problema, modelo, hallazgos, auditoría). |
| `scripts/validacion/` | Scripts en Python que recalculan las cifras de control desde el CSV. |
| `powerbi/` | Proyecto de Power BI (`.pbip`) y `.pbix` final. |
| `.claude/skills/` | Skills de Claude Code activas: `pbi-report-builder` y `pbip-dependency-analyzer`. |
| `.claude/skills_no_instaladas/` | Skills revisadas y descartadas (ver sección 15 del plan). |

## Avance

| Fase | Estado | Documento |
|---|---|---|
| 0 — Entorno | Completa | Este README |
| 1 — Perfilamiento | En revisión del equipo | [docs/01_perfilamiento.md](docs/01_perfilamiento.md) |
| 2 — Problema | Pendiente | — |
| 3 — Modelo | Pendiente | — |
| 4 / 4.5 — Exploración y hallazgos | Pendiente | — |
| 5 — Diseño | Pendiente | — |
| 6 — Construcción | Pendiente | — |
| 7 — Validación técnica | Pendiente | — |
| 8 — Auditoría y sustentación | Pendiente | — |
| 9 — Entrega | Pendiente | — |

## Reproducir las cifras de control

```bash
pip install pandas
python scripts/validacion/01_perfilamiento.py
```
