# Proyecto final BI 2026-2 — Grupo 3: Cadena nacional de supermercados

Dashboard interactivo en Power BI para la gerencia de tiendas y de categoría.

## Estructura

| Carpeta | Contenido |
|---|---|
| `data/raw/` | `03_cadena_supermercados.csv`: dataset original (solo lectura, no se modifica). |
| `docs/` | Entregables de cada fase (perfilamiento, problema, modelo, hallazgos, auditoría). |
| `scripts/validacion/` | Scripts en Python que recalculan las cifras de control desde el CSV. |
| `powerbi/` | Proyecto de Power BI (`.pbip`) y `.pbix` final. |
| `.claude/skills/` | Skills de Claude Code activas: `dashboard-design-studio` (diseño), `pbi-report-builder` (construcción) y `pbip-dependency-analyzer` (auditoría). |
| `.claude/skills_no_instaladas/` | Skills revisadas y descartadas (ver sección 15 del plan). |

## Avance

| Fase | Estado | Documento |
|---|---|---|
| 0 — Entorno | Completa | Este README |
| 1 — Perfilamiento | Aprobada | [docs/01_perfilamiento.md](docs/01_perfilamiento.md) |
| 2 — Problema | Aprobada | [docs/02_problema.md](docs/02_problema.md) |
| 3 — Modelo | Completa (validada en Power BI) | [docs/03_modelo.md](docs/03_modelo.md) |
| 4 / 4.5 — Exploración y hallazgos | Completa | [docs/04_matriz_hallazgos.md](docs/04_matriz_hallazgos.md) |
| 5 — Diseño | Primera versión (se ajusta después) | [docs/05_diseno_dashboard.md](docs/05_diseno_dashboard.md) |
| 6 — Construcción | Completa: 5 páginas + validación | `powerbi/ProyectoFinal.pbip` |
| 7 — Validación técnica | Completa: 14/14 cifras de control | [docs/05_diseno_dashboard.md](docs/05_diseno_dashboard.md) |
| 8 — Auditoría y sustentación | Pendiente | — |
| 9 — Entrega | Pendiente | — |

## Reproducir las cifras de control

```bash
pip install pandas
python scripts/validacion/01_perfilamiento.py
```

```bash
python scripts/validacion/02_evidencia_problema.py
```

```bash
python scripts/validacion/04_validacion_hallazgos.py
```

## Abrir el proyecto en cualquier computador

1. Clonar o descargar el repositorio y abrir `powerbi/ProyectoFinal.pbip` con Power BI Desktop.
2. Hacer clic en **Actualizar**. El CSV se busca así:
   - primero en la ruta local guardada en el parámetro `RutaCSV` (funciona sin internet en el computador de quien la guardó);
   - si esa ruta no existe en este computador, se descarga automáticamente desde GitHub (parámetro `UrlCSV`, repositorio público).
3. Solo la primera vez en cada computador, Power BI pregunta cómo conectarse a `raw.githubusercontent.com`: elegir **Anónimo → Conectar**.

No hay que editar ninguna ruta. El aviso de niveles de privacidad no aparece porque el proyecto tiene activada la opción "Ignorar niveles de privacidad" (`fastCombine` en `model.tmdl`): ambas fuentes son el mismo archivo público.
Requisito: el repositorio debe seguir siendo **público**. Si se vuelve privado, la descarga de respaldo deja de funcionar y hay que corregir `RutaCSV` en *Transformar datos → Parámetros*.

## Regenerar el proyecto de Power BI (con Power BI Desktop cerrado)

```bash
python scripts/pbip/generar_modelo_tmdl.py
```

```bash
python scripts/pbip/generar_reporte_pbir.py
```
