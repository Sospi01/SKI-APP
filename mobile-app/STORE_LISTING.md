# Ficha de Google Play — Ski Info

Textos listos para copiar y pegar en Play Console. Cambiarlos no requiere
publicar una versión nueva de la app.

Dónde se pega:
- **Español (ficha principal):** Crecimiento → Presencia en Store →
  Fichas de Store → Ficha de Store principal.
- **Inglés:** en esa misma ficha, "Gestionar traducciones" → "Añadir
  traducciones" → **Inglés (Estados Unidos) – en-US**. Opcional: añade
  también **Inglés (Reino Unido) – en-GB** con el mismo texto.

Las capturas de pantalla se heredan de la ficha principal si no subes
otras para el inglés. Lo ideal es subir 4 capturas hechas con la app en
inglés (ábrela, pulsa "View in English" y haz las capturas de la portada,
la ficha de una estación, el mapa con una pista seleccionada y la
previsión de nieve).

Límites de Google Play: título 30 caracteres, descripción breve 80 y
descripción completa 4000. Todos los textos de aquí están dentro.

---

## Inglés (en-US)

### Título (27/30)
```
Ski Info: Piste Maps & Snow
```

### Descripción breve (73/80)
```
Piste maps, 7-day snow forecasts and run gradients for 1,200+ ski resorts
```

### Descripción completa
```
Ski Info puts the piste map of 1,276 ski resorts in 45 countries in your pocket: the Alps, the Pyrenees, North America, Japan, Scandinavia and more. Every resort comes with a 7-day snow forecast and the real gradient of every run.

EVERY RUN, MEASURED
• Interactive piste map over satellite imagery
• Tap any run to see its elevation profile section by section, its average gradient and its steepest pitch
• Runs by difficulty, with night skiing and tree runs marked
• Lifts by type, with capacity, ride time and whether they have a bubble or heated seats
• Restaurants, bars, first aid and rental shops on the map

SNOW FORECAST
• 7-day snowfall forecast at summit altitude for every resort
• Where it will snow most this week: a ranking by region, updated every day
• Current weather at the resort

RANKINGS AND GUIDES
• The biggest ski resorts in the world, the Alps and North America
• The highest resorts and the ones with the most vertical
• The best resorts for beginners
• The steepest and longest runs
• Ski resorts near Geneva, Zurich, Munich, Milan, Innsbruck, Lyon, Denver, Salt Lake City, Vancouver and Tokyo

PLAN YOUR DAY
• Directions to the resort's base area in Google Maps
• Share a resort with your friends in one tap
• Search for accommodation nearby

Free, and no account needed. Available in English and Spanish.

WHERE THE DATA COMES FROM
Runs and lifts come from OpenStreetMap and OpenSkiMap (ODbL licence), mapped by a worldwide community of volunteers. Gradients are computed from an elevation model. Weather and snow forecasts come from Open-Meteo, and satellite imagery from Esri, Maxar and Earthstar Geographics. Some resorts are mapped in more detail than others, and each resort page shows how complete its data is.

Also on the web: skiinfoapp.com
```

---

## Español (ficha principal, actualizada)

La ficha actual dice "más de 280 estaciones" y 6 países. Ya son 1.276 en
45 países, con previsión de nieve y pendientes. Conviene sustituirla.

### Título (24/30)
```
Ski Info: pistas y nieve
```
(Si prefieres mantener solo la marca, deja `Ski Info`. Añadir palabras
clave al título suele mejorar la búsqueda dentro de Google Play.)

### Descripción breve (74/80)
```
Mapa de pistas, nieve a 7 días y pendiente real de más de 1.200 estaciones
```

### Descripción completa
```
Ski Info reúne el mapa de pistas de 1.276 estaciones de esquí de 45 países: España y Andorra, los Pirineos, los Alpes, Norteamérica, Japón, Escandinavia y más. Cada estación incluye la previsión de nieve a 7 días y la pendiente real de cada pista.

CADA PISTA, MEDIDA
• Mapa de pistas interactivo sobre imagen de satélite
• Toca una pista y verás su perfil de altitud tramo a tramo, su pendiente media y su tramo más empinado
• Pistas por dificultad, con las nocturnas y las de bosque señaladas
• Remontes por tipo, con capacidad, duración del trayecto y si tienen burbuja o asientos calefactados
• Restaurantes, bares, primeros auxilios y tiendas de alquiler en el mapa

PREVISIÓN DE NIEVE
• Nieve prevista a 7 días en cota alta para cada estación
• Dónde va a nevar más esta semana: ranking por zonas, actualizado cada día
• Tiempo actual en la estación

RANKINGS Y GUÍAS
• Las estaciones más grandes de España y Andorra, de los Pirineos y del mundo
• Las más altas y las de más desnivel
• Las mejores estaciones para principiantes
• Las pistas más empinadas y más largas
• Estaciones cerca de Madrid, Barcelona, Zaragoza, Valencia, Bilbao y otras ciudades

ORGANIZA EL DÍA
• Cómo llegar a la base de la estación con Google Maps
• Comparte una estación con tus amigos en un toque
• Busca alojamiento cerca

Gratis y sin registro. Disponible en español e inglés.

DE DÓNDE SALEN LOS DATOS
Las pistas y remontes vienen de OpenStreetMap y OpenSkiMap (licencia ODbL), mantenidos por una comunidad de voluntarios de todo el mundo. Las pendientes se calculan con un modelo de elevación. El tiempo y la previsión de nieve vienen de Open-Meteo, y las imágenes de satélite de Esri, Maxar y Earthstar Geographics. Algunas estaciones están cartografiadas con más detalle que otras, y cada ficha indica lo completos que son sus datos.

También en la web: skiinfoapp.com
```

---

## Categoría
Deportes (o Viajes y guías locales).

## Clasificación de contenido
Sin violencia, sin lenguaje adulto, sin compras dentro de la app. Debería
quedar como "Para todos los públicos" / PEGI 3.

## Anuncios
La app no muestra anuncios. El enlace de alojamiento a Booking.com es un
enlace de afiliado, no un anuncio, así que la respuesta a "¿Contiene
anuncios?" es **No**.

## Formulario de seguridad de datos (Data safety)
**Importante:** la versión anterior de este documento decía que la app no
recoge datos. Desde que añadimos las estadísticas (Firestore) y Firebase
Analytics en Android, eso ya no es cierto. Google puede retirar una app si
el formulario no coincide con lo que hace, así que revisa que esté así:

- ¿La app recopila o comparte datos de usuario? **Sí, recopila.**
  **No comparte** (Firebase actúa como proveedor de servicio, lo que para
  Google no cuenta como "compartir").
- ¿Los datos se cifran en tránsito? **Sí** (HTTPS).
- ¿Los usuarios pueden pedir que se borren? **No.** Los datos no están
  ligados a ninguna identidad y se borran solos a los 13 meses.
- Tipos de datos que hay que marcar:
  - **Actividad en la app → Interacciones con la app:** recogida, no
    compartida, no efímera, obligatoria, finalidad **Analíticas**.
  - **Identificadores del dispositivo u otros identificadores:** recogido,
    no compartido, obligatorio, finalidad **Analíticas** (es el
    identificador aleatorio de las estadísticas y el ID de instancia de
    Firebase; el identificador publicitario está desactivado).
  - Nada más: ni ubicación, ni datos personales, ni contactos.

## Público objetivo
General, no dirigida específicamente a niños.

## Política de privacidad (URL)
```
https://skiinfoapp.com/privacy.html
```

## Correo de contacto del desarrollador
```
fsospedra2@gmail.com
```
