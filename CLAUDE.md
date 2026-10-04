# Ski Info — guía para Claude

Web y app de estaciones de esquí: **https://skiinfoapp.com**. Tiene mapa de pistas sobre satélite, el perfil de pendiente de cada pista, remontes, servicios y la previsión de nieve a 7 días de **1.409 estaciones en 45 países**, en 7 idiomas (es, en, fr, de, it, nl, pl). Los datos vienen de OpenStreetMap a través de OpenSkiMap (licencia ODbL: siempre hay que atribuirlos). También hay una app Android que es un envoltorio WebView de la web.

El propietario es **Francisco Sospedra** (GitHub `Sospi01`), usuario no técnico. **Háblale siempre en español**, claro y sin jerga. Cuando tenga que hacer algo en una consola (Play Console, Firebase, Search Console, GitHub), dale los pasos exactos uno a uno.

---

## 1. Reglas de trabajo (obligatorias)

- **Rama:** `claude/ski-stations-database-rhvohj`. Es la rama por defecto del repo y **la que se despliega**. Todo se desarrolla, se commitea y se sube a esa rama (`git push -u origin claude/ski-stations-database-rhvohj`). Nunca subas a otra rama sin permiso. No abras PRs salvo que se pidan.
- **Commits:** mensajes claros en inglés. **Nunca pongas identificadores de modelo** en commits, código ni PRs. Las líneas de atribución las indica el sistema en cada sesión.
- **Secretos:** nunca subas el keystore de Android, contraseñas ni claves. Viven en los *secrets* de GitHub Actions.
- **Panel de estadísticas:** los datos de `/stats` solo los puede leer `fsospedra2@gmail.com`. Lo imponen las reglas de Firestore y no se debe relajar.
- **Afiliados:** no activar CJ ni otros programas de afiliados hasta que haya tráfico real. El de Booking todavía no está activo: `AFFILIATE.bookingDeepLinkPrefix` está vacío en `index.html`.
- **Textos visibles:** todo texto nuevo de `docs/index.html` (marcado o `T('…')`) debe tener traducción en `docs/i18n/{en,fr,de,it,nl,pl}.js`. La clave es el texto en español. **El build falla** si falta alguna traducción del marcado. Los textos idénticos en todos los idiomas van en `SAME_IN_BOTH` (`build_seo_pages.py`).
- **Reglas de Firestore:** si añades un tipo de evento o un campo en `docs/track.js`, actualiza `firestore.rules` y **pide al usuario que las publique** en la consola de Firebase: no se despliegan solas.
  - Los campos nuevos van también en `NEW_FIELDS` de `track.js`. Así, si las reglas aún son las viejas, el evento se reenvía sin ese campo en vez de perderse.
  - Un tipo de evento nuevo no tiene esa red: se pierde hasta que se publiquen las reglas.
- **No ejecutes `build_seo_pages.py --inject-home` en local.** Reescribe `docs/index.html`: rellena `<script id="home-data">` con datos, cuyo valor en el repo debe ser `null`. En local ejecútalo **sin** `--inject-home`. Si lo usas, restaura el `null` antes de commitear.
- **Antes de hacer push:** ejecuta la prueba de humo (sección 4) y, si tocas el pipeline, `pytest`.
- **Después de un push:** el despliegue tarda de 5 a 10 minutos. GitHub Pages puede servir la versión anterior unos 10 minutos más.

## 2. Limitaciones del entorno (sandbox en la nube)

- **Dominios bloqueados por el proxy:** skiinfoapp.com, api.open-meteo.com, OpenSkiMap, las teselas de satélite de Esri (server.arcgisonline.com), Google, Reddit y la mayoría de webs de noticias.
  - Todo se prueba en local, contra `docs/`, simulando Open-Meteo.
  - No se puede "ver" la web real: pide capturas al usuario.
- **GitHub:** sin `gh` CLI. Se usan las herramientas MCP `mcp__github__*`, que se cargan con ToolSearch: ejecuciones de Actions, commits, etc.
- **Android:** no se puede compilar aquí, porque falta el SDK. Lo compila GitHub Actions.
- **Chromium:** preinstalado para Playwright, en `/opt/pw-browsers/chromium`. Los módulos de Node están en `/opt/node22/lib/node_modules`.
- **Servidor local:** se pierde cuando se reinicia el contenedor. Para relanzarlo:
  `cd docs && (setsid nohup python3 -m http.server 8903 >/dev/null 2>&1 &)`

## 3. Arquitectura

### 3.1 Web (`docs/`, servida por GitHub Pages con dominio propio)

| Archivo | Qué es |
|---|---|
| `index.html` | **La app**: SPA de ~3.800 líneas con un único IIFE de JS inline y el CSS inline. Pantallas: portada, lista de país, mapa de país y ficha de estación (paneles Info / Mapa). URL: `?estacion=<id>` y `&vista=mapa`. |
| `stations.js` | `STATIONS`: catálogo con id, nombre, región, km, país, lat y lon. También lo leen los scripts del pipeline. |
| `data/<id>.json` | Una estación completa: `runs` y `lifts` con `geom` [lon, lat, ele], estadísticas, `services`, `run_convention`, etc. `data/borders` son las fronteras. |
| `i18n.js` + `i18n/{en,fr,de,it,nl,pl}.js` | Traducción: `T('texto en español', args…)` con `{0}`. `SKI_LANG` y `SKI_LOCALE`. Los diccionarios son `window.SKI_I18N = {…}`. |
| `lang.js` | Selector de idioma con banderas (`mountLangPicker`), barra "esta página también está en…" (usa `<link rel=alternate hreflang>`) y elección recordada en `localStorage.si_lang`. |
| `station-actions.js` | "Cómo llegar" (a la base, el punto de remonte más bajo), "Compartir" (puente Android `SkiInfoAndroid.share`, luego `navigator.share`, luego portapapeles) y **favoritos** (`localStorage.si_favs`, `setupFavButton`). |
| `snow.js` / `snow.css` | Tiempo y previsión desde Open-Meteo, en el navegador, con 5 s de tiempo máximo. `snow.json` es el ranking de nieve que genera el despliegue. |
| `profile.js` | Perfil de pendiente de una pista (panel del mapa). |
| `static-pages.js` / `.css` | JS y CSS de las páginas generadas: fichas de estación, países y guías. |
| `sw.js` | Service worker, `VERSION = 'v6'`. Las navegaciones y los datos se piden primero a la red y, si falla, a la caché. Sube `VERSION` si cambia la lista de archivos del shell. |
| `track.js` | Contador de uso anónimo, sin cookies (ver 3.4). |
| `stats.html` | Panel privado de estadísticas (ver 3.4). |
| `privacy.html`, `privacy-{en,fr,de,it,nl,pl}.html` | Política de privacidad en los 7 idiomas (archivos fijos, enlazados por idioma con `LOC[lang]['privacy']` de `build_seo_pages.py`). |
| `flags/*.svg`, `icons/`, `fonts/` | Recursos. Las fuentes se sirven desde la propia web: Barlow Condensed e IBM Plex Sans. |

**Generado en cada despliegue (está en `.gitignore`, no se commitea):**
- `estacion/`, `pais/`, `guias/`, `app/`, `en/`, `fr/`, `de/`, `it/`, `nl/`, `pl/`;
- `og/` (imágenes para compartir);
- `sitemap.xml` (~10.300 URLs), `snow.json`, `slugs.json`, `guias.json`.

**Rutas por idioma:**

| Idioma | Estación | País | Guías |
|---|---|---|---|
| es | `/estacion/` | `/pais/` | `/guias/` |
| en | `/en/resort/` | `/en/country/` | `/en/guides/` |
| fr | `/fr/station/` | `/fr/pays/` | `/fr/guides/` |
| de | `/de/skigebiet/` | `/de/land/` | `/de/ratgeber/` |
| it | `/it/stazione/` | `/it/paese/` | `/it/guide/` |
| nl | `/nl/skigebied/` | `/nl/land/` | `/nl/gidsen/` |
| pl | `/pl/osrodek/` | `/pl/kraj/` | `/pl/poradniki/` |

- La app tiene una copia por idioma (`/en/`, `/fr/`…), que genera `build_localized_app`.
- fr, de, it, nl y pl reutilizan las imágenes OG en inglés (`/og/en/`) para no pasar de 1 GB en GitHub Pages.
- **Tamaño:** cada idioma suma ~73 MB. Con 7 idiomas la web ronda los 760 MB (609 MB sin imágenes OG): caben 2–3 idiomas más como mucho.
- Añadir un idioma toca: `i18n/<xx>.js`, `i18n.js` (`SKI_LOCALE`, `SKI_LANG_CHOICES`), `lang.js`, `sw.js`, `flags/`, `index.html` (hreflang, `lang-redirect`, enlaces del pie, `PATHS`, `FEATURED`, `POPULAR`, Booking), `LOC`/`FMT`/`LANG_NAMES`/`HOME_GUIDES` de `build_seo_pages.py`, `page_texts.py`, `guide_texts.py`, `.gitignore`, la política de privacidad y `smoke.js`.
- En polaco los números van tras dos puntos ("trasy: 12") cuando la palabra cambiaría según la cifra. Las guías polacas incluyen rankings propios de Polonia (zona `poland`).

**Piezas clave de `index.html`:**
- `loadStation`: limpia la ficha, descarga `data/<id>.json` y la previsión, y llama a `renderDashboard`.
- `buildMap`: mapa SVG con teselas de satélite de Esri y proyección equirectangular. El satélite cubre un 20 % más allá de la estación por cada lado (`MAP_SLACK`) y el mapa se puede arrastrar ese margen aunque no haya zoom (el 50 % con un panel abierto). La capa base es un solo nivel de zoom para toda la estación (máx. 160 teselas); al acercarse, `refineMapTiles` añade encima teselas más nítidas solo de la zona visible (hasta `TILE_MAX_ZOOM` = 17, máx. 48 por vez).
- **Nombres en el mapa** (5 de octubre): pistas y remontes con nombre llevan su nombre escrito a lo largo de la línea.
  - 2D: `layoutLabels` (en el controlador del mapa; `relabelMap` al construirlo) los coloca en pantalla cada vez que la vista se para: primero los más largos, sobre un tramo casi recto, sin solaparse (rejilla de 10 px) y lejos de los botones; al hacer zoom caben más. Van fuera del grupo con zoom (`mapState.labelG`): al arrastrar solo se desplazan; al hacer zoom o girar se ocultan y se recolocan a los 160 ms. Máx. 90. Con una ruta abierta, al 50 %.
  - 3D: capa `labels` de MapLibre (`symbol-placement: line`), con cada nombre dibujado en un canvas (`drawLabel`, `styleimagemissing`), así que no hace falta servidor de fuentes; MapLibre quita los que chocan.
- `renderMapPreview`: tarjeta del mapa en el móvil, sobre satélite; solo por debajo de 1000 px.
- `trackMapUse`: cuenta el uso real del mapa una vez por estación. En el móvil, al abrirlo; en el ordenador, al arrastrar, hacer zoom o pulsar.
- `displayName`: nombres en alfabeto latino.
- `DIFF`, `DIFF_ORDER`, `DIFF_SHOWN_AS` y `shownDifficulty`: colores por región.
  - Norteamérica: *easy* → verde, *intermediate* → azul, *expert* → doble negra (`double`).
  - Japón: *easy* → verde.
  - Lo replican `build_guides.py`, `build_seo_pages.py` y `build_share_images.py`.
- `renderFavs`: sección "Mis estaciones" de la portada, con la nieve a 7 días.
- Portada para quien llega por primera vez: botones "Populares" (`POPULAR`, por idioma o Norteamérica) y "Cerca de ti" (por zona horaria, `TZ_COORDS`, o ubicación real guardada redondeada en `si_loc`). Botón "Instalar como app" (`beforeinstallprompt`).
- Mapa de estación: modo de color "Dificultad | Pendiente" (`setMapMode`, `si_map_mode`), botón "Dónde estoy" (`locDraw`, `watchPosition`), compartir desde el mapa (`#mapa` al final de la URL de la ficha: `static-pages.js` salta al mapa), y el perfil de cada pista se puede recorrer con el dedo (`addProfileScrubber` en `profile.js`, que marca el punto en el mapa con `window.onProfilePoint`).
- Portada: buscador `#global-search`, ranking de nieve, destacadas y guías. `#home-data` es el JSON que inyecta el despliegue.
- **Vista 3D** (`docs/map3d.js` + MapLibre GL 5 en `docs/vendor/maplibre-gl-5.24.0/`, que solo se descargan al pulsar el botón "3D" del mapa):
  - **abierta a todos desde el 4 de octubre** (antes, escondida tras `?3d=1`): el botón sale si el navegador tiene WebGL. El usuario la probó en la web y en la app y va bien;
  - en pantallas de alta resolución (devicePixelRatio ≥ 2) el satélite se declara con `tileSize: 128` para que pida un nivel más de detalle;
  - relieve de AWS Terrain Tiles (Mapzen, gratis, sin clave; sí se pueden descargar desde el sandbox) e imágenes de Esri;
  - dibuja `mapState.features` (las mismas pistas y remontes que el 2D) y devuelve los toques al 2D: panel de pista en el ordenador y ventana con el perfil en el móvil. Reutiliza los botones de zoom, el modo Dificultad/Pendiente, "Dónde estoy" y el punto del perfil;
  - cámara: mira ladera arriba (del punto más bajo al más alto) salvo que girarla hasta 90° encuadre mucho mejor la estación (`frame()`); botón para dar una vuelta (`spin`);
  - arranca con `style.load`, no con `load` (que espera a todas las teselas y se queda colgado si alguna está bloqueada). Se abre directamente en la vista final (inclinada) y oculta, y aparece con un fundido al primer `idle` o a los 5 s: la animación inicial de inclinación se quitó porque pedía teselas de todos los niveles intermedios y el relieve aparecía a saltos.
- **Planificador de rutas** (`docs/routes.js`, se descarga al primer uso; **escondido** tras `?rutas=1` o el código `rutas=1` del buscador, que se recuerda en `localStorage.si_routes`):
  - botón "Ruta hasta aquí" en la ventana (móvil) o el panel (ordenador) de cada pista, remonte o servicio; el panel de la ruta (`renderRoute`, reutiliza `#map-run-panel`) deja elegir el origen, solo dos opciones (el usuario quitó "La base"/"Pie de pistas"): "Mi ubicación" (si el aparato la da; se elige sola si ya está activa) o "Punto en el mapa": el panel solo pide tocar el mapa cerca de una pista o remonte y, al tocar, calcula la ruta (`routePlaceRow` muestra la salida elegida; el usuario descartó la lista de lugares por complicada). Un toque sin nada debajo se engancha al lugar de `routePlaces` más cercano a menos de 250 m, también en 3D; el panel se vuelve a abrir 350 ms después del toque para que el clic fantasma del móvil no pulse un botón del panel) y el nivel (todas, sin negras, verdes y azules; `si_route_level`), y lista los pasos con el tiempo estimado. La ruta se dibuja en 2D (`drawRoute2D`) y en 3D (`map3d.showRoute`), atenuando el resto;
  - la red (`SkiRoutes.build`): pistas solo cuesta abajo (en los dos sentidos si son casi llanas: menos de 5 m o del 3 %), remontes solo hacia arriba con 90 s de espera, y enlaces a pie entre lo que se toca (35 m; 60 m junto a remontes; hasta 150 m por llano, como el Pla de Beret), sin subir más de 8 m ni bajar por un cortado. Dijkstra por tiempo estimado;
  - calidad de la red (`SkiRoutes.quality`, % de pares de remontes conectados; `node web-tests/route-quality.js`): a 4 de octubre, 1.023 de 1.409 estaciones superan el 80 % (Formigal 100 %, Baqueira 94 %). Por debajo del 80 % el panel avisa de que puede haber huecos;
  - pasos legibles: se omiten enlaces (caminatas < 80 m, trocitos de otra pista), un remonte dibujado en varios tramos es un paso (su duración se reparte por longitud y la espera se cuenta una vez), una pista usada en parte dice "200 m de 2,6 km", y si ya estás en el destino dice "Ya estás en…";
  - las pistas dibujadas como un bucle (bajan por un carril y suben por otro, o al revés) se parten en dos carriles hacia abajo: en el perfil (`splitOutAndBack` de `profile.js`), en las flechas del mapa y en las rutas (`splitLoop`);
  - no sabe qué está abierto: el panel lo advierte siempre.
  - al calcular, la ruta se encuadra sola (`fitRoute` → `fitMapTo` en 2D, `map3d.fitRoute` en 3D) junto al panel (ordenador) o encima (móvil). En la ruta, remontes en discontinua y tramos a pie en puntos;
  - elegir la salida tocando: con "Punto en el mapa" elegido, cualquier toque en el mapa es la salida (`routePickArmed`; un remonte → su salida o llegada más cercana, un servicio → él mismo, una pista → el punto tocado; los servicios tienen prioridad sobre la pista de debajo). Con otro origen, tocar algo con la ruta abierta abre una ventanita con "Salir desde aquí" y "Ruta hasta aquí" (en el ordenador no se cierra al mover el ratón: `dataset.sticky`).
- **Modo de prueba de "Dónde estoy"** (escondido): tras abrir la web con `?simular=1` (se recuerda en `localStorage.si_fake_loc`; `?simular=0` lo quita), el botón no pide la ubicación real: mueve el punto por la pista más larga de la estación a unos 8 m/s (`locFakeWalk`). Sirve para probar desde casa y para grabar vídeos. En modo prueba el botón sale aunque el aparato no dé ubicación (app 1.0.5).
- **Códigos en el buscador de la portada** (la app Android no tiene barra de direcciones): `simular=1`/`simular=0` y `rutas=1`/`rutas=0` activan o quitan esos modos y recargan la página.

### 3.2 Pipeline (`data-pipeline/`)

- `ski_pipeline/`: CLI que descarga el GeoJSON de OpenSkiMap y crea un SQLite: `python -m ski_pipeline.cli --db data/ski_info.db -v`. Tests: `cd data-pipeline && python3 -m pytest -q` (39 pasan).
- `scripts/`:
  - `build_seo_pages.py`: fichas, países, página `/app`, sitemap, copias por idioma de la app y datos de la portada. Opciones: `--inject-home` (solo en el despliegue), `--write-slugs` para estaciones nuevas y `--base-url`.
  - `build_guides.py`: guías generadas con los datos; los textos están en `guide_texts.py`.
  - `page_texts.py`: textos de las páginas en fr, de, it, nl y pl.
  - `fetch_snow_forecast.py`: previsión de todas las estaciones, que se guarda en `docs/snow.json`.
  - `build_share_images.py`: imágenes OG. Necesita Pillow y tarda unos 3 minutos.
  - `refresh_stations.py`: actualización semanal de `docs/data` desde OpenSkiMap. Nunca añade ni quita estaciones. Si una estación pierde más de la mitad de pistas o km, la deja como estaba. Si más del 20 % parecen rotas, no escribe nada. Detecta estaciones cuyo id ha cambiado. Tiene sus tests.
  - `detect_domain_groups.py`: agrupa las estaciones que forman un mismo dominio esquiable.
  - `add_stations.py`: añade estaciones que faltan de un país (mismo criterio que el catálogo original, con un mínimo de km), salta las que ya están, las que quedan a menos de 1,5 km de una existente y las mucho más pequeñas a menos de 3,5 km o dentro del terreno de otra (partes de otra estación), y las que no tienen remontes en funcionamiento; crea su ficha sin servicios. Se lanza con el workflow manual `add-stations.yml` (primero en modo prueba, que solo lista; luego de verdad, que commitea y despliega). Tiene sus tests.
- `station_slugs.json`: id → slug. Es estable: no cambies slugs existentes, rompería URLs indexadas.

### 3.3 GitHub Actions (`.github/workflows/`)

- **`deploy-pages.yml`:** se lanza con cada push a la rama si cambian `docs/**` o los scripts de build y textos. Además, se ejecuta a diario a las **04:17 y 11:07 UTC** para refrescar la previsión; las ejecuciones programadas de GitHub no están garantizadas, por eso hay dos. Pasos: previsión, luego `build_seo_pages.py --inject-home`, luego imágenes OG (en caché, clave `og-v2-…`), luego Pages. `concurrency: pages` cancela los despliegues antiguos.
- **`refresh-stations.yml`:** los **lunes a las 02:37 UTC**. Commitea los datos actualizados y lanza el despliegue (un push hecho con `GITHUB_TOKEN` no lanza workflows).
- **`build-android.yml`:** compila el AAB y el APK firmados con los secretos `SKIINFO_KEYSTORE_*` y los deja como artifact `ski-info-release`, que dura 14 días.
- **`add-stations.yml`:** manual. Añade las estaciones que faltan de un país (`add_stations.py`); por defecto `dry_run` (solo lista en el resumen de la ejecución).
- `fetch-stations.yml`, `data-analysis.yml` y `pipeline-smoke-test.yml`: utilidades del pipeline, de lanzamiento manual o por rutas.

### 3.4 Estadísticas propias (sin Google Analytics en la web)

- **`docs/track.js`** escribe eventos directamente en Firestore mediante la API REST: proyecto `ski-info-9910e`, colección `events`.
  - Solo cuenta en `skiinfoapp.com` o `*.github.io`, nunca en localhost.
  - **Ignora robots:** Googlebot, la inspección de Search Console, Lighthouse, Bing, etc., y cualquier navegador con `navigator.webdriver`. Activo desde el 29 de septiembre a las 22:00 UTC.
  - Tipos de evento: `open`, `station`, `map`, `booking`, `time`, `page`, `fav`, `map3d` (abre la vista 3D) y `locate` (activa "Dónde estoy"); estos dos, una vez por estación y visita, desde el 4 de octubre.
  - Campos: `uid` (id anónimo en localStorage), `sid` (sesión compartida entre pestañas; caduca tras 30 minutos sin actividad), `platform` (android/web), `lang`, `src`/`ref`/`lp` (procedencia y página de entrada) y `tz` (zona horaria, que da el país sin usar la IP; desde el 29 de septiembre).
  - Los enlaces con `?ref=nombre` aparecen en el panel como "Enlace marcado".
- **`firestore.rules`:** solo permite crear eventos bien formados. Leer y borrar solo puede hacerlo el propietario. **Hay que publicarlas a mano** en Firebase → Firestore Database → Reglas; la versión publicada incluye `fav` y `tz`. `map3d` y `locate` se añadieron y publicaron el 4 de octubre.
- **`docs/stats.html`:** panel con acceso por Google (solo el propietario), en `/stats.html`.
  - Muestra resumen, gráficos, web o app, procedencia, países, Booking, fidelización y tiempo de uso.
  - Lista de usuarios con país, procedencia, estaciones vistas y guardadas (⭐), insignias "3D" y 📍 (con las estaciones donde abrió el 3D o activó "Dónde estoy"), y botón "Ocultar este usuario". En el resumen, aperturas del 3D y usuarios que lo abren o activan "Dónde estoy"; en Fidelización, "Abren la vista 3D". En Fidelización, "Guardan alguna estación"; en Estaciones más vistas, cuántos la guardan.
  - Guarda en caché local `si_stats_cache_v2`. Los usuarios ocultos se guardan en localStorage.
  - `?demo=1` muestra datos de ejemplo, útil para probar sin Firebase.
  - `BOT_FILTER_SINCE` separa los usuarios sin actividad (probables robots) de antes y después del filtro.
- **Firebase Analytics** solo existe en la app Android. La referencia de tráfico es `/stats`.

### 3.5 App Android (`mobile-app/`)

- Envoltorio mínimo: una sola `MainActivity.java` con un WebView que carga `https://skiinfoapp.com/`. Incluye el puente JS `SkiInfoAndroid.share` y Firebase Analytics.
- Paquete `com.sospedra.skiinfo`, versión **1.0.6** (versionCode 9; la 8 se descartó porque excluía aparatos sin GPS) en el repo; en Play sigue la 1.0.5 hasta que el usuario suba el AAB nuevo. minSdk 24, targetSdk 36.
- Desde 1.0.6:
  - permiso de ubicación (solo al pulsar "Dónde estoy" o "Usar mi ubicación"; se usa solo en el móvil);
  - `SkiInfoAndroid.hasLocation()` le dice a la web que la app da la ubicación (`canUseLocation()` en `index.html`); la 1.0.5 no lo tiene y la web oculta esos botones;
  - abre la web en el idioma del móvil (es, en, fr, de, it, nl o pl) con `/?applang=xx`, que el script `lang-redirect` de `index.html` respeta salvo que el usuario ya haya elegido idioma (`si_lang`).
- En Google Play está en **prueba cerrada** (hacen falta 14 días con 12 testers). Terminaría hacia el **7–8 de octubre**; después, el usuario solicita el acceso a producción.
- Verificación de desarrollador de Android: hecha. Los dos paquetes de la cuenta están registrados.
- `mobile-app/STORE_LISTING.md` tiene los textos de la ficha de Play en los 7 idiomas (es, en, fr, de, it, nl, pl), y los pasos del formulario de seguridad de los datos.
- `marketing/REDDIT_POSTS.md` tiene los posts para Reddit y foros, cada uno con su `?ref=`.

## 4. Cómo probar

```bash
cd /home/user/SKI-APP/docs && (setsid nohup python3 -m http.server 8903 >/dev/null 2>&1 &)
cd /home/user/SKI-APP
python3 data-pipeline/scripts/build_seo_pages.py              # opcional: /en/ /fr/ /de/ /it/ y páginas estáticas (SIN --inject-home)
NODE_PATH=/opt/node22/lib/node_modules node web-tests/smoke.js # prueba de humo, debe acabar en "all checks passed"
cd data-pipeline && python3 -m pytest -q                       # si tocas el pipeline
```

**`web-tests/smoke.js` comprueba:**
- las portadas en los 7 idiomas;
- la ficha de Baqueira en el móvil (lista de pistas, tarjeta del mapa y mapa) y en el ordenador;
- una página estática;
- `stats.html?demo=1`;
- que el contador registra a una persona con su zona horaria y no cuenta a Googlebot.

**Para pruebas nuevas con Playwright:**
- `chromium.launch({ executablePath: '/opt/pw-browsers/chromium' })`.
- Bloquea todo lo que no sea localhost y simula Open-Meteo: `mockMeteo` está en `smoke.js`.
- Usa `serviceWorkers: 'block'`.
- Para probar `track.js`, sirve `docs/` bajo `https://skiinfoapp.com/` con `route.fulfill`, y fuerza `navigator.webdriver = false` (Playwright lo pone a true y el contador lo trataría como robot).
- Guarda las capturas en el scratchpad y revísalas con Read. Para enseñárselas al usuario, usa SendUserFile.

## 5. Estado a 29–30 de septiembre de 2026

**Tráfico** (panel `/stats`, del 25 al 29 de septiembre):
- **213 usuarios** y 319 sesiones.
- Día del post en r/skiing (28 de septiembre): **176 usuarios**, con más de 200 fichas vistas. Al día siguiente, 30 usuarios, de los que 12 repetían.
- Fidelización: 13 usuarios (6 %) han vuelto otro día.
- Embudo: el 64 % abre una estación, el 37 % abre el mapa y el 2,8 % pulsa Booking. Los 24 clics en Booking son de solo 6 personas, y parte son testers o el propio usuario.
- Sesión media de 1,5 minutos; mediana de 39 segundos.
- Parte de los usuarios anteriores al 29 de septiembre eran **robots**: el panel los cuenta en Fidelización, en "probables robots". Hay que pedir al usuario la cifra y que los oculte.
- La métrica "Aperturas del mapa" cambió de definición el 29 de septiembre; antes y después no son comparables.

**Hecho recientemente:**
- versión en francés, alemán e italiano;
- nombres en alfabeto latino;
- favoritos y "Mis estaciones";
- actualización semanal desde OpenSkiMap;
- selector de idioma con banderas;
- tarjeta del mapa sobre satélite en el móvil;
- procedencia, país, filtro de robots y probables robots en `/stats`;
- colores de dificultad de Norteamérica y Japón, más el filtro de doble negra;
- dos despliegues diarios.

**Hechos que conviene saber:**
- 2 de octubre: se añadieron 133 estaciones pequeñas de EE. UU. (al menos 3 km de pistas, entre ellas Liberty Mountain) con `add-stations.yml`; aún no tienen servicios. EE. UU. pasó de 216 a 349 estaciones.
- Algunas redes de empresa (incluida la del usuario) bloquean skiinfoapp.com por ser un dominio nuevo: `ERR_NAME_NOT_RESOLVED`. No es un fallo de la web.
- Decisión sobre legalidad: aviso legal y consentimiento de estadísticas **aplazados** hasta activar ingresos (afiliados o publicidad) o hacer promoción fuerte. Entonces habrá que añadir el aviso Aceptar/Rechazar y el aviso legal con los datos del titular.
- Search Console: el sitemap está enviado. El usuario pide unas 10 indexaciones manuales al día. La última lectura del sitemap que vimos era de 2.701 URLs; ahora tiene ~6.700.
- Nevasport (hilo del foro "App de perfiles con desnivel de pistas", 2–4 de octubre): muy buena acogida. Felicitaron el administrador **Pepe Peinado Palomero** (creador de Nevasport en 2001, exprofesor de esquí; la web vive de la publicidad del sector) y un moderador. El usuario solo le ha dado las gracias: **no proponer colaboración todavía**; más adelante, con algo nuevo que enseñar, presentarla como complemento para sus lectores (mapas y pendiente que Nevasport no tiene), no como competencia. Ideas del hilo: mapas en 3D (echan de menos FatMap), rutas "llévame al baño por azules" (difícil: huecos en OSM y sin estado de apertura) y "la mitad de las negras del Pirineo deberían ser rojas" (idea de guía y post).
- Competencia: Steep Seeker (EE. UU., colorea por pendiente), Carvable (iOS), skiresort.info y OnTheSnow. Lo que nos diferencia: cobertura mundial, perfil tramo a tramo y previsión de nieve.

## 6. Tareas pendientes

**Del usuario:**
1. En `/stats`, ocultar sus dispositivos (móvil con app, navegador del móvil y ordenador), decir cuántos "probables robots" salen y pulsar "Ocultar esos N".
2. Post en r/SideProject hacia el 1–2 de octubre, enlazando **directamente al mapa de una estación** con `?ref=reddit-sideproject`. Después, Nevasport, con 2–3 días entre publicaciones.
3. Search Console: seguir con las indexaciones y comprobar que el sitemap se ha leído con ~6.700 URLs.
4. Play Console, si no lo ha hecho: ficha en inglés, ficha en español actualizada (aún decía 280 estaciones) y formulario de **Seguridad de los datos** (la app recoge estadísticas anónimas).
5. Hacia el 7–8 de octubre: terminar la prueba cerrada y solicitar producción.

**De desarrollo, por prioridad:**
0. **Vista 3D** (abierta a todos el 4 de octubre; el usuario ya lo contó en Nevasport): su uso se mide con el evento `map3d` (reglas publicadas el 4 de octubre). Revisar en unos días cuántos lo abren.
0b. **Planificador de rutas** (Fase 1 hecha, escondida tras `rutas=1`): esperar las pruebas del usuario en Formigal y Baqueira y corregir. Siguientes pasos: beta abierta en el hilo de Nevasport; abrirlo a todos solo en las estaciones con calidad ≥ 80 %; botón "Está cerrado" en remontes y pistas para recalcular; Fase 2, guía en directo siguiendo "Dónde estoy" (recalcular si te sales).
1. Comprobar que se ejecutaron los despliegues programados (04:17 y 11:07 UTC) con `mcp__github__actions_list` sobre `deploy-pages.yml`, filtrando por el evento `schedule`.
2. **Portada para quien llega por primera vez:** el 36 % se va sin abrir ninguna estación. Hay que dar más visibilidad a las estaciones populares o cercanas.
3. Textos de la ficha de Play: hechos en los 7 idiomas (`STORE_LISTING.md`); falta que el usuario los pegue en Play Console.
4. **App 1.0.6:** abrir la versión del idioma del móvil entre los 5 disponibles. Cuando la app esté en producción, cambiar el botón "Muy pronto" de `/app` por el enlace de Google Play (en `build_seo_pages.py`, en `app_page`).
5. **Política de privacidad** en inglés, francés, alemán e italiano.
6. Lunes 5 de octubre: comprobar la ejecución de `refresh-stations.yml`.
7. Evaluar en unos días el uso del mapa con la tarjeta nueva y la fidelización a 7 días del post de Reddit.
8. Octubre:
   - modo de mapa que **colorea las pistas por su pendiente real**;
   - guía "Apertura de estaciones 2026/27" de España y Andorra (las fechas hay que meterlas a mano);
   - pedir que nos incluyan en la wiki de OpenStreetMap.
9. Temporada (desde finales de noviembre):
   - post semanal "Dónde va a nevar esta semana";
   - afiliado de Booking, cuando el tráfico desde Google sea estable;
   - avisos de nevada para las estaciones guardadas, empezando por la app.

**Previsión que se le dio al usuario** (usuarios al día, sin contar picos; escenario medio): octubre 15–40, noviembre 40–120 y diciembre–febrero 150–400.
