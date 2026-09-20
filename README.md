# Ski Info

App móvil para consultar de forma rápida las características de estaciones de esquí:
desnivel, km de pista por dificultad, tipos y capacidad de remontes, pendiente real,
esquí nocturno, nieve artificial y fiabilidad histórica de nieve — a partir de datos
abiertos (OpenStreetMap / OpenSkiMap), sin depender del contenido editorial con
copyright de portales como skiresort.com.

## Por qué

skiresort.com reserva expresamente los derechos sobre sus fichas de estación, así
que en vez de scrapearlas usamos datos abiertos (licencia ODbL) procesados por
[OpenSkiMap](https://openskimap.org) a partir de OpenStreetMap. Esto da acceso a
métricas objetivas y calculables (pendiente real, % de nieve artificial, % de
remontes desembragables, orientación) que ninguna app existente muestra de forma
combinada.

## Estructura del repo

- `data-pipeline/` — pipeline en Python que descarga el GeoJSON de OpenSkiMap
  (áreas de esquí, pistas, remontes), lo normaliza y genera una base de datos
  SQLite lista para embeber en la app.
- `mobile-app/` — app móvil (siguiente fase) que consume la base de datos generada
  por el pipeline.

## Roadmap

1. **Pipeline de datos** (en curso) — descarga, transformación y SQLite.
2. **App móvil** — ficha de estación, buscador y filtros por métricas offline.
3. **Enriquecimiento** — precios/temporadas curados a mano para las 300-500
   estaciones más consultadas, y tiempo/nieve en vivo vía API aparte.

## Fuente de datos

[OpenSkiMap](https://openskimap.org) (formato [`openskidata-format`](https://github.com/russellporter/openskidata-format)),
derivado de OpenStreetMap y Skimap.org. Licencia [ODbL](https://opendatacommons.org/licenses/odbl/) — requiere atribución.
