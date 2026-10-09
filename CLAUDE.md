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
- **Recordatorios (petición del usuario, 7 de octubre):** todo lo que quedemos en hacer o revisar "en unos días" (mandar estadísticas, revisar un dato, un paso en una consola…) se programa como recordatorio con `send_later` (herramienta `claude-code-remote`) y se apunta en "Recordatorios programados" (sección 6). Además, la Routine "Repaso de tareas pendientes" (lunes y jueves a las 9:47, hora de España) le recuerda las tareas sin hacer. Al cumplir una tarea, quítala de la lista.

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
| `station-names.js` | `STATION_NAMES`: id → nombre revisado a mano ("Baqueira Beret", "Candanchú", "Cerler"…, y los que si no saldrían repetidos). Ver "Nombres" abajo. |
| `sw.js` | Service worker, `VERSION = 'v8'`. Las navegaciones y los datos se piden primero a la red y, si falla, a la caché. Sube `VERSION` si cambia la lista de archivos del shell. |
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
- **Mapa del dominio entero** (5 de octubre): en "Dominio esquiable conectado", el botón "Ver el mapa del dominio entero" y, en el mapa, la pastilla "Dominio entero (N)" / "Solo X" (`showDomainMap`, `domainRaw`, `mapRaw()`): el mapa (y las rutas) usan las pistas, remontes y servicios de todas las estaciones del grupo; el resto de la ficha sigue siendo de la estación.
- `renderMapPreview`: tarjeta del mapa en el móvil, sobre satélite; solo por debajo de 1000 px.
- `trackMapUse`: cuenta el uso real del mapa una vez por estación. En el móvil, al abrirlo; en el ordenador, al arrastrar, hacer zoom o pulsar.
- **Nombres** (6 de octubre, para que la app parezca más profesional): `displayName(name, id)` (y `display_name()` en `build_seo_pages.py`, idénticos) da el nombre que se muestra: el de `station-names.js` si está; si no, la primera forma en alfabeto latino, solo lo de antes de la primera coma, sin palabras genéricas ("Estació d'Esquí", "Skigebiet", "Domaine skiable", "… Ski Resort", "… Resort"; no "Mountain Resort": "Red Mountain Resort" → "Red Mountain"). Los datos y `stations.js` guardan el nombre de OSM (la actualización semanal los reescribe); los slugs no cambian (usan `strip_generic`) y el buscador también busca por el nombre original (`localName`). Las pistas y remontes con dos nombres en la etiqueta ("Rabadá BIS;Rabadá baby") salen como "Rabadá BIS / Rabadá baby" (`featureNames`, `feature_name`).
- **Ficha sin "cocina" de datos** (6 de octubre): en la cabecera, "Remontes" en vez de las coordenadas; la etiqueta de estado solo si no está operativa; "Calidad del dato" plegada bajo "Sobre estos datos" (`details.about-data`); el pie sin el ID; la escala del mapa con coma decimal. En Europa, "expert" se muestra como "Negra" (`DIFF_SHOWN_AS.europe`, también en `build_guides.py`): antes salían "Negra" y "Negra (experta)" del mismo color.
- `DIFF`, `DIFF_ORDER`, `DIFF_SHOWN_AS` y `shownDifficulty`: colores por región.
  - **Mismos colores en modo claro y oscuro** (5 de octubre, queja de un usuario de iPhone que veía las negras blancas): el modo oscuro ya no cambia `--diff-*` ni `--map-lift-color` (`index.html` y `static-pages.css`). Los mapas (`#map-viewport`, `#map-preview`) llevan siempre el borde blanco (`--map-halo`). En modo oscuro, los puntos y barras negros de las listas llevan un anillo claro (selector `[style*="--diff-advanced"]`).
  - Norteamérica: *easy* → verde, *intermediate* → azul, *expert* → doble negra (`double`).
  - Japón: *easy* → verde.
  - Lo replican `build_guides.py`, `build_seo_pages.py` y `build_share_images.py`.
- `renderFavs`: sección "Mis estaciones" de la portada, con la nieve a 7 días.
- **Portada nueva** (6 de octubre, aprobada por el usuario con maquetas):
  - **Web:** a la derecha del buscador (debajo en el móvil), la vista 3D de Formigal girando (`docs/img/home/hero.mp4`, solo en pantallas ≥ 1000 px, sin "ahorro de datos" ni "reducir movimiento"; si no, `hero.jpg`), con "Ver en 3D ›" → `?estacion=<id>&vista=3d` (abre el mapa y su 3D: `want3d` en `ensureMapBuilt`). Al final, "Así es cada estación en Ski Info": imagen 3D (`SHOW_3D`, Val Thorens) y capturas reales de la ficha en el idioma de la página (`profile-<lang>.jpg`, `snow-<lang>.jpg`, de `marketing/make_home_shots.js`; la nieve es de ejemplo y sin fechas).
  - **App** (`IS_APP`: WebView de Android, `; wv)` en el user agent): **nunca una estación fija arriba** (petición del usuario). Sin el 3D de cabecera ni la franja final; si hay estaciones guardadas, arriba "★ Tu estación" (`renderMine`, la última guardada) con su imagen (o, si no hay imagen, su mapa sobre satélite con `renderMapPreview(raw, {card, svg})`), su nieve en 7 días, la temperatura arriba y el espesor (Open-Meteo, como en la ficha) y "Abrir mapa" / "Ver ficha". "Mis estaciones" sale solo si hay dos o más.
  - "Estaciones populares": tarjetas con la imagen 3D de las 4 primeras de `POPULAR` (del idioma o Norteamérica) y la nieve prevista en 7 días de `snow.json` ("❄ 25 cm en 7 días").
  - "Elige un país": los 12 primeros como banderas (`#country-grid`) y "Ver los 45 países ›" despliega la lista entera.
  - **Imágenes** en `docs/img/home/` (se commitean): `<id>.jpg` de cada estación de `POPULAR` (600×500, 3D con nombres), hechas con `marketing/make_home_images.sh` (como los vídeos: lista de teselas, workflow `fetch-tiles.yml` con la lista `home`, `make_video.js --still`), y revisadas a ojo antes de publicarlas. Si se añade una estación a `POPULAR`, hay que generar su imagen (`make_home_images.sh <id>`). Si una imagen falla al cargar, la tarjeta se queda con el degradado azul y "Tu estación" pasa al mapa.
- Portada para quien llega por primera vez: botones "Populares" (`POPULAR`, por idioma o Norteamérica) y "Cerca de ti" (por zona horaria, `TZ_COORDS`, o ubicación real guardada redondeada en `si_loc`). Botón "Instalar como app" (`beforeinstallprompt`).
- **Brújula** (5 de octubre, idea de Nevasport): botón `#map-north` arriba de los controles; solo sale cuando el mapa está girado (más de 1°), la aguja marca el norte y al pulsarlo el mapa vuelve al norte sin moverse del sitio (2D: anima `angle` alrededor del centro; 3D: `map3d.north()`, aguja con `onRotate`). `setNorth` lo pone el controlador del mapa.
- **Pendiente** (7 de octubre, revisado el 8 tras el hilo de Nevasport: un geógrafo y otros pidieron los criterios oficiales y tramos cortos): `smoothProfile` (profile.js) remuestrea cada 10 m, quita picos (mediana de 5) y promedia en `SLOPE_WINDOW_M` = 30 m; colores con los umbrales de **ATUDEM/AFNOR**: verde < 15 %, azul 15–25 %, rojo 25–40 %, negro > 40 % (`PITCH_ZONES`; la leyenda lo cita); el "máx." de cada pista es el tramo más empinado de **exactamente** `STEEPEST_M` = 50 m (el final se interpola: antes, dos nodos a 2 m daban un 67 % falso en una verde de Formigal) y se descartan los de más del 90 % (`MAX_REAL_PITCH`). Se muestran **grados junto al %** ("máx. 43 % · 23°", `pitchDeg`) y una nota: "Las alturas tienen una precisión de unos 30 m…". Lo mismo en el perfil, el mapa 2D/3D (`slopeStretches`), las insignias, las fichas y las guías: `smoothed_elevations`/`run_max_pitch`/`split_out_and_back` de `build_seo_pages.py` dan exactamente los mismos números (comprobado en 1.679 pistas). Bonaigua 43 % (23°), Cara Nord 48 %, Luis Arias 49 %; de media 4 puntos menos que antes del 7 de octubre.
- Mapa de estación: modo de color "Dificultad | Pendiente" (`setMapMode`, `si_map_mode`), botón "Dónde estoy" (`locDraw`, `watchPosition`), compartir desde el mapa (`#mapa` al final de la URL de la ficha: `static-pages.js` salta al mapa), y el perfil de cada pista se puede recorrer con el dedo (`addProfileScrubber` en `profile.js`, que marca el punto en el mapa con `window.onProfilePoint`).
- Portada: buscador `#global-search`, ranking de nieve, destacadas y guías. `#home-data` es el JSON que inyecta el despliegue.
- **Vista 3D** (`docs/map3d.js` + MapLibre GL 5 en `docs/vendor/maplibre-gl-5.24.0/`, que solo se descargan al pulsar el botón "3D" del mapa):
  - **abierta a todos desde el 4 de octubre** (antes, escondida tras `?3d=1`): el botón sale si el navegador tiene WebGL. El usuario la probó en la web y en la app y va bien;
  - carga (5 de octubre, el usuario vio que a veces cargaba mal): el satélite se declara con `tileSize: 128` (un nivel más de detalle) solo en pantallas pequeñas de alta resolución (DPR ≥ 2 y área ≤ 520.000 px, o sea móviles); en el ordenador eran 4 veces más teselas (101 → 39 al abrir el dominio de la Vía Láctea). El relieve llega solo hasta el zoom 12 (`TERRAIN_MAXZOOM`: el dato es de ~30 m y cada nivel más son 4 veces más teselas). Teselas de satélite y relieve por el protocolo `retry://` (`addRetryProtocol`): una que falla se pide hasta 2 veces más en vez de dejar un agujero negro con bordes estirados;
  - relieve de AWS Terrain Tiles (Mapzen, gratis, sin clave; sí se pueden descargar desde el sandbox) e imágenes de Esri;
  - dibuja `mapState.features` (las mismas pistas y remontes que el 2D) y devuelve los toques al 2D: panel de pista en el ordenador y ventana con el perfil en el móvil. Reutiliza los botones de zoom, el modo Dificultad/Pendiente, "Dónde estoy" y el punto del perfil;
  - cámara: mira ladera arriba (del punto más bajo al más alto) salvo que girarla hasta 90° encuadre mucho mejor la estación (`frame()`); dos botones para dar la vuelta, uno en cada sentido (`spin(dir)`: el mismo botón otra vez la para, el otro la invierte; petición de Nevasport, 5 de octubre). Para girar e inclinar a mano: Ctrl + arrastrar o botón derecho (ordenador) o dos dedos; las 3 primeras veces que se abre el 3D sale un aviso que lo explica (`map3dHint`, `si_3d_hint`);
  - arranca con `style.load`, no con `load` (que espera a todas las teselas y se queda colgado si alguna está bloqueada). Se abre directamente en la vista final (inclinada) y oculta, y aparece con un fundido al primer `idle` o a los 5 s: la animación inicial de inclinación se quitó porque pedía teselas de todos los niveles intermedios y el relieve aparecía a saltos.
- **Planificador de rutas** (`docs/routes.js`, se descarga al primer uso). **Beta abierta** (7 de octubre) en las estaciones con la red bien conectada (calidad ≥ 80 %): lista precalculada en `docs/routes-ok.json` (`data-pipeline/scripts/build_routes_ok.js`, ~2 min; `s`: estaciones, `d`: estaciones cuyo mapa de dominio entero también llega; ids de 12 caracteres), porque calcularlo en el móvil tarda segundos en las grandes. Se regenera en `refresh-stations.yml` y `add-stations.yml`; **si cambias `routes.js`, regenéralo y commitéalo**. `routesOn()` en `index.html`; el código `rutas=1` (`localStorage.si_routes`) las abre en todas. El botón y el título del panel llevan la etiqueta "Beta". Evento `route` (una vez por estación y visita, al salir la primera ruta):
  - botón "Ruta hasta aquí" en la ventana (móvil) o el panel (ordenador) de cada pista, remonte o servicio; el panel de la ruta (`renderRoute`, reutiliza `#map-run-panel`) deja elegir el origen, solo dos opciones (el usuario quitó "La base"/"Pie de pistas"): "Mi ubicación" (si el aparato la da; se elige sola si ya está activa) o "Punto en el mapa": el panel solo pide tocar el mapa cerca de una pista o remonte y, al tocar, calcula la ruta (`routePlaceRow` muestra la salida elegida; el usuario descartó la lista de lugares por complicada). Un toque sin nada debajo se engancha al lugar de `routePlaces` más cercano a menos de 250 m, también en 3D; el panel se vuelve a abrir 350 ms después del toque para que el clic fantasma del móvil no pulse un botón del panel) y el nivel (todas, sin negras, verdes y azules; `si_route_level`), y lista los pasos con el tiempo estimado. La ruta se dibuja en 2D (`drawRoute2D`) y en 3D (`map3d.showRoute`), atenuando el resto;
  - la red (`SkiRoutes.build`): pistas solo cuesta abajo (en los dos sentidos si son casi llanas: menos de 5 m o del 3 %), remontes solo hacia arriba con 90 s de espera, y enlaces a pie entre lo que se toca (35 m; 60 m junto a remontes; hasta 150 m por llano, como el Pla de Beret), sin subir más de 8 m ni bajar por un cortado. **Bajar en remonte** (7 de octubre, el usuario vio que en la Vía Láctea casi ninguna ruta entre Sestriere/Sansicario y Claviere/Montgenèvre salía): un remonte a cuya salida no llega ninguna pista (un pueblo bajo las pistas, como Cesana) también se puede bajar (`RIDE_DOWN`: telecabinas, teleféricos, funiculares y trenes; telesillas solo si no termina ninguna pista a menos de 300 m de su salida, `CHAIR_DOWN_M`, porque más cerca suele ser un hueco del mapa; nunca arrastres); el paso dice "Baja en …". Dominio de la Vía Láctea: 49 % → 97 % de pares de remontes conectados (Sansicario → Cesana en la telecabina, Rafuyel y Sagnalonga a Claviere); 327 remontes en 209 estaciones. Dijkstra por tiempo estimado, con **como mucho 2 enlaces a pie seguidos** (`MAX_WALKS`; 5 de octubre: encadenando enlaces cortos entre pistas paralelas mandaba a andar medio kilómetro ladera arriba junto a una pista, p. ej. de Cesana a la 27 bis en la Vía Láctea);
  - calidad de la red (`SkiRoutes.quality`, % de pares de remontes conectados; `node web-tests/route-quality.js`): a 7 de octubre, 1.042 de 1.382 con dos o más remontes superan el 80 % (Formigal 100 %, Baqueira 94 %). Por debajo del 80 % el panel avisa de que puede haber huecos;
  - pasos legibles: se omiten enlaces (caminatas < 80 m, trocitos de otra pista), un remonte dibujado en varios tramos es un paso (su duración se reparte por longitud y la espera se cuenta una vez), una pista usada en parte dice "200 m de 2,6 km", y si ya estás en el destino dice "Ya estás en…";
  - las pistas dibujadas como un bucle (bajan por un carril y suben por otro, o al revés) se parten en dos carriles hacia abajo: en el perfil (`splitOutAndBack` de `profile.js`), en las flechas del mapa y en las rutas (`splitLoop`);
  - no sabe qué está abierto: el panel lo advierte siempre.
  - al calcular, la ruta se encuadra sola (`fitRoute` → `fitMapTo` en 2D, `map3d.fitRoute` en 3D) junto al panel (ordenador) o encima (móvil). En la ruta, remontes en discontinua y tramos a pie en puntos;
  - la salida (`routeStartsAt`, 7 de octubre): si tocas una pista, la ruta sale **de esa pista**; si no, de lo que haya a menos de 25 m (40 m con "Mi ubicación"), y solo si no hay nada, andando hasta lo que haya en 300 m. "Ya estás en…" solo si la pista tocada es el destino. Antes valía cualquier pista a 300 m y, si la de destino pasaba a menos de 60 m, decía "Ya estás" aunque hubiera que bajar y subir un remonte (47 casos así en Baqueira);
  - elegir la salida tocando: con "Punto en el mapa" elegido, cualquier toque en el mapa es la salida (`routePickArmed`; un remonte → su salida o llegada más cercana, un servicio → él mismo, una pista → el punto tocado; los servicios tienen prioridad sobre la pista de debajo). Con otro origen, tocar algo con la ruta abierta abre una ventanita con "Salir desde aquí" y "Ruta hasta aquí" (en el ordenador no se cierra al mover el ratón: `dataset.sticky`).
- **Formulario de sugerencias** (`docs/feedback.js`, 7 de octubre): ventana con mensaje y correo opcional que llega por correo al usuario vía **Web3Forms** (clave pública en el archivo; desde el 8 de octubre los mensajes van a `skiinfoapp@gmail.com`, la cuenta del proyecto; la dirección la guarda Web3Forms). Lo abre cualquier elemento con `data-feedback` (`general`, `data`, `route`; el texto del enlace lo pone el propio script, con sus textos en los 7 idiomas): pie de la portada y de todas las páginas generadas, "Avisar de un error en los datos" en "Sobre estos datos" (app y fichas estáticas) y "¿Algo raro en esta ruta? Cuéntanoslo" en el panel de la ruta (`routeFeedbackLink`, manda la ruta y los pasos). El correo lleva estación, página, idioma y web/app. Mencionado en la política de privacidad (7 idiomas). Cuenta de Gmail propia del proyecto: Google bloqueó `skiinfoapp@gmail.com` al crearla; el recurso se aprobó el 8 de octubre y ya recibe las sugerencias de Web3Forms. Se usará para las redes sociales.
- **Modo de prueba de "Dónde estoy"** (escondido): tras abrir la web con `?simular=1` (se recuerda en `localStorage.si_fake_loc`; `?simular=0` lo quita), el botón no pide la ubicación real: mueve el punto por la pista más larga de la estación a unos 8 m/s (`locFakeWalk`). Sirve para probar desde casa y para grabar vídeos. En modo prueba el botón sale aunque el aparato no dé ubicación (app 1.0.5).
- **Códigos en el buscador de la portada** (la app Android no tiene barra de direcciones): `simular=1`/`simular=0` y `rutas=1`/`rutas=0` activan o quitan esos modos y recargan la página.

### 3.2 Pipeline (`data-pipeline/`)

- `ski_pipeline/`: CLI que descarga el GeoJSON de OpenSkiMap y crea un SQLite: `python -m ski_pipeline.cli --db data/ski_info.db -v`. Tests: `cd data-pipeline && python3 -m pytest -q` (39 pasan).
- `scripts/`:
  - `build_seo_pages.py`: fichas, países, página `/app`, sitemap, copias por idioma de la app y datos de la portada. Opciones: `--inject-home` (solo en el despliegue), `--write-slugs` para estaciones nuevas y `--base-url`.
  - `build_guides.py`: guías generadas con los datos; los textos están en `guide_texts.py`. Arriba llevan la misma barra que las fichas (6 de octubre, la app no tiene barra del navegador): "‹ Guías" (en el índice, "‹ Ski Info"), que vuelve a la página anterior si era de la web (`BACK_JS`) y si no va al enlace, y "Ski Info" a la portada.
  - Guías "cerca de [ciudad]" (`CITIES` de `guide_texts.py`): el 8 de octubre se añadieron 40 ciudades (es: Valladolid, Logroño, Oviedo, Huesca, Lleida, Granada, León, Burgos, San Sebastián; en: Boston, Nueva York, Seattle, Calgary, Toronto, Portland, Reno, Montreal, Sapporo; fr: Annecy, Chambéry, Clermont-Ferrand, Strasbourg, Perpignan, Pau, Montpellier; de: Graz, Linz, Bern, Luzern, Basel, Nürnberg, Köln, Dresden, Hamburg; it: Trento, Bergamo, Brescia, Cuneo, Padova, Udine), porque son las guías que más clics traen. En francés, "de" se elide ante vocal ("près d'Annecy", slug `pres-d-annecy`). Las guías usan `display_name()` como el resto de la web (antes salían tres "San Isidro" iguales).
  - `page_texts.py`: textos de las páginas en fr, de, it, nl y pl.
  - `fetch_snow_forecast.py`: previsión de todas las estaciones, que se guarda en `docs/snow.json`.
  - `build_share_images.py`: imágenes OG. Necesita Pillow y tarda unos 3 minutos.
  - `refresh_stations.py`: actualización semanal de `docs/data` desde OpenSkiMap. Nunca añade ni quita estaciones. Añade a cada estación las pistas y remontes **de ninguna estación** del catálogo (de una zona pequeña que se dejó fuera por ser parte de otra, como el lado de Cesana de Sansicario, o sin zona) que la tocan: a menos de 300 m, directamente o a través de otros sueltos (60 m) (`absorb_orphans`, con sus km en `run_stats`). `--dry-run` (y la opción del workflow manual, activada por defecto) solo hace el informe. Si una estación pierde más de la mitad de pistas o km, la deja como estaba. Si más del 20 % parecen rotas, no escribe nada. Detecta estaciones cuyo id ha cambiado. Tiene sus tests.
  - `detect_domain_groups.py`: agrupa las estaciones que forman un mismo dominio esquiable.
  - `add_stations.py`: añade estaciones que faltan de un país (mismo criterio que el catálogo original, con un mínimo de km), salta las que ya están, las que quedan a menos de 1,5 km de una existente y las mucho más pequeñas a menos de 3,5 km o dentro del terreno de otra (partes de otra estación), y las que no tienen remontes en funcionamiento; crea su ficha sin servicios. Se lanza con el workflow manual `add-stations.yml` (primero en modo prueba, que solo lista; luego de verdad, que commitea y despliega). Tiene sus tests.
- **Para buscadores e IAs** (8 de octubre; dos usuarios llegaron recomendados por ChatGPT, que busca sobre todo en Bing; el usuario dio de alta la web en Bing Webmaster Tools importándola de Search Console):
  - `scripts/indexnow.py`: tras cada despliegue avisa por **IndexNow** (Bing, Yandex…) de las páginas del sitemap que han cambiado (hash del HTML sin la previsión de nieve ni `home-data`; los hashes viajan en la caché `indexnow-*` del workflow; la primera vez manda las ~10.400). La clave es pública: `docs/08aa4441f443c25748c0b352af960923.txt`. Nunca hace fallar el despliegue.
  - `docs/llms.txt`: presentación de Ski Info para IAs (qué es, qué datos, URLs de ejemplo). Fijo; si cambian cifras o rutas, actualízalo.
  - En la introducción de cada ficha (7 idiomas): "Sus pistas más empinadas (tramo de 50 m con más pendiente) son A (59 %, 31°), B y C. La pista más larga es X (4,1 km)." Solo pistas balizadas (no freeride) y de como mucho 60 %: más suele ser el relieve de 30 m pillando un cortado al lado, y una frase se cita como un hecho (las insignias siguen mostrando todo).
  - **Página "Alternativa a FatMap"** (`scripts/fatmap_page.py`, 7 idiomas, bajo la ruta de guías: `/guias/alternativa-a-fatmap/`, `/en/guides/fatmap-alternative/`…; enlazada en el índice de guías y en `llms.txt`): FatMap cerró el 1 de octubre de 2024 tras comprarla Strava (enero de 2023). Qué tiene Ski Info, qué no tiene (travesía, sin conexión, app de iPhone), estaciones para abrir en 3D (`FEATURED`) y preguntas frecuentes con `FAQPage`.
  - **Guías de pendiente** (`softblack` y `hardred` en `build_guides.py`/`guide_texts.py`): "Las pistas negras más suaves" y "Las rojas más difíciles" (Pirineos y Alpes en es/en/fr; Alpes en de/it/nl/pl), según el tramo de 50 m más empinado de cada pista (`station_stats` recibe `run_max_pitch`). Solo pistas oficiales de 300 m o más, sin tramos de más del 60 %; en las negras, nada por debajo del 20 % ni con nombre de camino o enlace (`TRACK`: "Route de…", "Chemin", "Raccordo"…), que suelen estar mal clasificados en OSM. Sin pendiente media: a veces salía mayor que la máxima (se calculan distinto).
  - **Títulos de las fichas** (9 de octubre, viendo Search Console: "courchevel lift map" en posición 9,6 sin clics): con las palabras que se buscan y la pendiente. "Courchevel piste & lift map, slopes and snow forecast"; en EE. UU. y Canadá, "trail & lift map" (`title_na`, según `run_convention`); de "Pistenplan & Liftplan, Gefälle…"; es "mapa de pistas y remontes, pendientes y nieve"; fr/it/nl/pl igual (`title` de `TX`/`page_texts.py`).
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
  - Tipos de evento: `open`, `station`, `map`, `booking`, `time`, `page`, `fav`, `map3d` (abre la vista 3D) y `locate` (activa "Dónde estoy"); estos dos, una vez por estación y visita, desde el 4 de octubre. `route` (calcula una ruta, una vez por estación y visita; 7 de octubre: **hay que publicar las reglas**; en `/stats`, "Usuarios que calculan una ruta", "Calculan una ruta" y la insignia 🧭).
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
- **Vídeos para TikTok "¿Qué estación de esquí es?"** (`marketing/make_video.js` + `marketing/make_video.sh`; el bueno es `marketing/videos/formigal-3d.mp4`, 5 de octubre): el 3D con relieve y los nombres de pistas y remontes (como en la web; `--names 0` los quita) dando una vuelta despacio (20 s, 18°/s; el usuario pidió más lento que los 12 s del primero, `formigal-adivina.mp4`, que salió plano), la pregunta, una pista y "Respuesta en los comentarios" (los 2,5 s finales: "Mapa 3D de 1.400 estaciones · skiinfoapp.com"), 1080×1920, sin música. El usuario quiere **siempre el mismo estilo**: los textos son una plantilla fija (`overlay.png`/`outro.png`) que ffmpeg pone encima.
  - **Una sola orden** (en el sandbox, ~22 min): `marketing/make_video.sh <nombre> <id> "<pista>"`. Hace: lista de teselas de satélite (vuelta rápida de 16 pasos, ~3 min) → workflow `fetch-tiles.yml` (las descarga y commitea; espera su resultado y lo reintenta: el 5 de octubre GitHub no le asignó máquina una vez) → fotogramas (~13 min) → mp4 → commit del mp4 y la vista previa y borra las teselas. Teselas que ya estén en `marketing/tiles/<nombre>/` no se vuelven a pedir.
  - Rapidez: el WebGL va por software (~1 s por dibujo), así que cada fotograma se dibuja **una vez** y se lee del canvas (la captura de pantalla volvía a dibujar: 6 s/fotograma → ~3,5), se dibujan 12 por segundo y ffmpeg interpola a 30 (`minterpolate`; por eso los textos van aparte: interpolados se emborronaban).
  - El relieve (teselas de AWS) lo descarga el script con `curl` (`DEM_DIR`): el Chromium del sandbox no se fía del certificado del proxy. En GitHub Actions el WebGL va a ~68 s por fotograma: `make-video.yml` no sirve.
  - Ojo con los nombres que delatan la estación (p. ej. el remonte "Sallent" en Formigal).
- **TikTok** (8 de octubre): cuenta **@skiinfoapp** ("Ski Info App"), creada con `skiinfoapp@gmail.com`, **personal** (para usar los sonidos de tendencia; el enlace pulsable en la biografía llega a los 1.000 seguidores: entonces `skiinfoapp.com/?ref=tiktok`). Foto de perfil 1080×1080 generada del logo. Plan: 2-3 vídeos por semana, subidos a mano desde el móvil con sonido de tendencia al 20-30 %; texto "¿Qué estación de esquí es? … Respuesta mañana en los comentarios" + hashtags; al día siguiente, comentario fijado con la respuesta y la web. Publicados: jueves 8 Formigal, viernes 9 Baqueira; luego Sierra Nevada (martes 13), Cerler, Val Thorens, Zermatt. **Plantilla desde el 9 de octubre** (petición del usuario): la pista es solo el país ("España", "Francia", "Suiza") y "Respuesta en los comentarios" va a un tercio de la altura (`.bottom` con 300 px abajo en `make_video.js`), porque abajo lo tapaban el título y la barra de comentarios de TikTok. Baqueira, Sierra Nevada, Cerler, Val Thorens y Zermatt se rehicieron así. **Retención** (9 de octubre): Baqueira tuvo 604 visitas pero 4,8 s de media y un 3,8 % lo vio entero. Pruebas con `marketing/make_variant.js` (reaprovecha los fotogramas de `/tmp/video-<nombre>/frames`, ~4 min; si el contenedor se reinicia hay que volver a dibujarlos con `make_video.sh`): la vuelta entera en 10–12 s y sin cierre, para que haga bucle; gancho grande el primer 1,6 s (`--hook`); cuenta atrás (`--countdown`); empezar acercado y abrirse (`--reveal 1`); "skiinfoapp.com" fijo bajo la llamada a comentar. Plan: martes 13 Sierra Nevada v1 (12 s, "¿La adivinas en 10 segundos?", cuenta de 10); jueves 15 Cerler v2 (10 s, acercado, "Solo los que más esquían la aciertan 👀", cuenta de 8); domingo 18 Val Thorens v3 (como la v1 + "Texto a voz" de TikTok). Comparar tiempo medio y % que lo ve entero. **Quiz** (idea del usuario, 9 de octubre; `marketing/make_quiz.js`): varias estaciones en un vídeo, cada una con cuenta atrás de 5 s y luego su nombre en grande ("✅ GRANDVALIRA"), "¿Cuántas aciertas? Comenta 👇"; `quiz-1.mp4` = Grandvalira, St. Anton, Courchevel (sábado 17). No usar estaciones ya publicadas sueltas (Formigal, Baqueira). Hay vídeos sueltos de Grandvalira, St. Anton y Courchevel. Después, los mismos vídeos (el mp4 original, sin marca de TikTok) en Instagram Reels y YouTube Shorts. Hay conector de Metricool para programar publicaciones si algún día se quiere automatizar.

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
5. Acceso a producción en Google Play: solicitado el 7 de octubre; esperar la aprobación (el usuario avisa).

**De desarrollo, por prioridad:**
(Comprobado el 8 de octubre: los despliegues programados y la actualización semanal del lunes 5 se ejecutan bien; GitHub los lanza con retraso, de 1 a 7 horas.)
0. **Vista 3D** (abierta a todos el 4 de octubre; el usuario ya lo contó en Nevasport): su uso se mide con el evento `map3d` (reglas publicadas el 4 de octubre). Revisar en unos días cuántos lo abren.
0b. **Planificador de rutas** (beta abierta a todos el 7 de octubre en las 1.042 estaciones con calidad ≥ 80 %; reglas con `route` pendientes de publicar por el usuario): anunciarlo en el hilo de Nevasport, leer lo que llegue por el formulario y corregir. Siguientes pasos: botón "Está cerrado" en remontes y pistas para recalcular; Fase 2, guía en directo siguiendo "Dónde estoy" (recalcular si te sales).
3. Textos de la ficha de Play: hechos en los 7 idiomas (`STORE_LISTING.md`); falta que el usuario los pegue en Play Console.
4. **App en producción:** cuando Google apruebe el acceso, versión de producción con el AAB 1.0.6 y cambiar el botón "Muy pronto" de `/app` por el enlace de Google Play (en `build_seo_pages.py`, en `app_page`).
7. Evaluar en unos días el uso del mapa con la tarjeta nueva y la fidelización a 7 días del post de Reddit.
8. Octubre:
   - modo de mapa que **colorea las pistas por su pendiente real**;
   - guía "Apertura de estaciones 2026/27" de España y Andorra (las fechas hay que meterlas a mano);
   - pedir que nos incluyan en la wiki de OpenStreetMap.
   - **Descenso virtual en el 3D** (8 de octubre, aprobado por el usuario): botón en la pista elegida que baja la cámara por ella, con el punto del perfil avanzando a la vez. Es lo que ChatGPT más destaca de Bonvo, que nos pone por delante (nos cita 3.º por la pendiente tramo a tramo). Se aprovecha `map3d.js`, el perfil y `onProfilePoint`.
   - Idea de Nevasport (Jairo): el color "real" de una pista depende también de anchura, exposición y nieve; a largo plazo, relieve de 2–5 m (IGN, Austria, Suiza) en las estaciones principales.
9. Temporada (desde finales de noviembre):
   - post semanal "Dónde va a nevar esta semana";
   - afiliado de Booking, cuando el tráfico desde Google sea estable;
   - avisos de nevada para las estaciones guardadas, empezando por la app.

**Recordatorios programados** (quitar cuando se cumplan):
- 14 oct, 9:30: ¿aprobado el acceso a producción? (lo solicitó el 7 de octubre). Si sí: versión de producción con el AAB 1.0.6 y enlace de Play en `/app`.
- 11 oct, 9:00: que el usuario mande Search Console (Rendimiento 28 días con Consultas y Páginas; Indexación → Páginas) y `/stats`. Referencia del 4 oct: 15 clics, 3.130 impresiones, CTR 0,5 %, posición 41,3; 2.320 indexadas, 4.323 descubiertas sin indexar, 289 rastreadas sin indexar (sobre todo estaciones pequeñas de EE. UU. en fr/it/de/pl). Si las rastreadas sin indexar pasan de ~1.000, valorar `noindex` en fichas pequeñas en idiomas que no les tocan.
- 11 oct, 10:30: cómo van los vídeos de TikTok (Formigal, jueves 8: el viernes seguía con 4 visitas sin entrar en "Para ti"; Baqueira, viernes 9, ya con la plantilla nueva). Si no arrancan: promoción de 5 € (el mínimo) en el que mejor vaya o cambiar el gancho. Siguiente: Sierra Nevada el martes 13.
- Lunes y jueves, 9:47: repaso de tareas pendientes (Routine).

**Previsión que se le dio al usuario** (usuarios al día, sin contar picos; escenario medio): octubre 15–40, noviembre 40–120 y diciembre–febrero 150–400.
