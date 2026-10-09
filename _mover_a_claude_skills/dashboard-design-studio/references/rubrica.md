# Paso 6 — Rúbrica de crítica de diseño

Calificar de 1 a 5. **Aprobado para construir: todos ≥ 4 y promedio ≥ 4.3.** Mostrar la tabla al usuario.

| # | Criterio | 1 (mal) | 3 (aceptable) | 5 (excelente) |
|---|---|---|---|---|
| 1 | Concepto | Decoración sin idea | Idea genérica ("corporativo") | Concepto del dominio, explicable en una frase |
| 2 | Jerarquía | Todo pesa igual | Hay foco pero compite | Un protagonista claro en 1 s; prueba de desenfoque OK |
| 3 | Patrón de lectura | Recorrido caótico | Patrón presente pero roto | Z/F/Gutenberg/capas aplicado y coherente con la tarea |
| 4 | Color con significado | Colores arbitrarios | Paleta armónica, semántica ambigua | Roles claros, 60-30-10, semánticos reservados |
| 5 | Accesibilidad | Contraste < 3:1 o solo color | AA en texto principal | AA en todo; daltonismo verificado con `paleta.py`; signos además de color |
| 6 | Retícula y alineación | Desalineado | Mayormente alineado | Todo en la retícula de 12 col; ritmo de 8 px |
| 7 | Tipografía | > 2 familias, tamaños al azar | Escala parcial | Escala modular, 2 familias máx., titulares-hallazgo |
| 8 | Espacio y densidad | Saturado o vacío | Algo apretado | Respira; agrupación por proximidad |
| 9 | Fidelidad a los datos | Cifras pintadas/inventadas | Datos reales, alguna distorsión | Visuales nativos, ejes honestos, cifras validadas |
| 10 | Coherencia y originalidad | Plantilla genérica | Correcto pero olvidable | Memorable y consistente con todas las páginas |

## Pruebas rápidas

- **Desenfoque (squint)**: `render_mockup.py --squint`. Con la imagen borrosa se debe distinguir el
  protagonista y los 2–3 bloques de apoyo.
- **5 segundos**: mostrar 5 s y preguntar "¿de qué trata y qué es lo más importante?".
- **Escala de grises**: la jerarquía debe sobrevivir sin color (`render_mockup.py --gris`).
- **Miniatura**: a 320 px de ancho debe seguir viéndose el concepto.
- **Retícula**: `render_mockup.py --grid`; nada se sale de las columnas.
- **Comparación**: poner la propuesta junto a 2 referencias del moodboard. ¿Está al mismo nivel?

## Formato de reporte

```
Propuesta B — "Tiquete de caja"
| Criterio | Nota | Evidencia |
| Concepto | 5 | La portada es un tiquete: renglones = páginas, total = dato héroe |
| ...      |   |          |
Promedio: 4.5 → aprobada. Ajustes antes de construir: subir contraste del subtítulo (3.8:1 → 4.6:1).
```
