# Posts para Reddit y foros

Cada enlace lleva `?ref=...`. En tu panel de estadísticas aparecerá como
`tag:reddit-skiing`, `tag:reddit-osm`, etc., así sabrás qué post trae
visitas.

## Antes de publicar
1. **Lee las normas de cada subreddit** (barra lateral / "About"). Algunos
   solo permiten autopromoción en un hilo semanal o con una etiqueta
   concreta. Si un post se borra por las normas, no lo vuelvas a subir igual.
2. **Usa una cuenta con algo de historial.** Las cuentas nuevas o sin
   karma suelen ir directas al filtro de spam. Si tu cuenta es nueva,
   comenta con normalidad en esos subreddits una o dos semanas antes.
3. **Di siempre que es tu proyecto.** En Reddit se castiga mucho la
   publicidad disfrazada; la sinceridad funciona mucho mejor.
4. **Uno cada día o dos, no todos a la vez.** Publicar el mismo enlace en
   varios subreddits el mismo día activa el filtro de spam.
5. **Responde a los comentarios durante las 2 primeras horas.** Es lo que
   más decide si un post sube o se hunde.
6. **Hora:** para los subreddits en inglés, entre las 15:00 y las 17:00
   (hora de España), que es la mañana en EE. UU.
7. Si alguien señala un error en una pista, agradécelo: los datos vienen
   de OpenStreetMap y se pueden corregir allí.

## Orden recomendado
1. r/OpenStreetMap (el público más amable con este tipo de proyectos, buen
   primer test)
2. r/skiing (el post principal: "he hecho esta web, ¿qué os parece?")
3. r/SideProject
4. Foros en español (Nevasport, grupos de esquí)
5. r/snowboarding **cuando lleguen las primeras nevadas fuertes**
   (noviembre), porque el post va de la previsión de nieve

---

## 1. r/skiing (post principal)

Tipo: **post de imagen** si el subreddit lo permite, con una captura de
una estación conocida con una pista seleccionada y su perfil visible.
Pon el texto de abajo como primer comentario. Si no se pueden subir
imágenes, haz un post de texto con el mismo contenido.

**Título:**
```
I built a free piste map site that lets you analyse a ski resort run by run. Looking for honest feedback
```

**Texto:**
```
Hi all! I've been working on a side project and I'd love some feedback from people who actually ski.

Most piste maps tell you a run is red or black and that's it. I wanted to know what each run is really like before getting there, so I built a site that breaks every resort down run by run:

- Tap any run to see its elevation profile section by section: length, vertical, average gradient and the steepest pitch
- Lifts with type, capacity, ride time and whether they have a bubble or heated seats
- Filter runs by difficulty, night skiing and tree runs
- 7-day snow forecast and current weather for each resort
- Rankings, e.g. the steepest runs in the Alps or the biggest resorts in North America

It covers 1,276 resorts in 45 countries, using OpenStreetMap data plus an elevation model. It's free and there's no account.

A good one to try: Mayrhofen, then tap Harakiri and look at its profile
https://skiinfoapp.com/en/resort/mayrhofen-hippach/?ref=reddit-skiing

Or look up your home mountain: https://skiinfoapp.com/en/?ref=reddit-skiing

What I'd love to know:
1. Is the run-by-run info actually useful when you're planning a trip or a day?
2. What's missing that you'd want to see for each run or resort?
3. Anything that looks wrong at your resort? The data comes from OpenStreetMap, so some resorts are mapped better than others.

Thanks for taking a look!
```

### 1b. Alternativa para r/skiing: post con datos
Si el primero no encaja con las normas del subreddit, o para publicarlo
unas semanas después:

Tipo: post de texto.

**Título:**
```
I measured the average gradient of every piste in the Alps and North America. The steepest is Whitetail at Big Sky (73%)
```

**Texto:**
```
I've been building a free site with piste maps for about 1,300 resorts, and one thing I always wanted was the real steepness of runs, not just their colour. So I took the run geometry from OpenStreetMap / OpenSkiMap, laid it over an elevation model and computed the gradient of every run, section by section.

Steepest runs by average gradient (top to bottom, runs of 300 m or more):

**Alps**
1. Lieuson, Auron (FR): 56% over 338 m
2. 114a Black Wall, Glacier 3000 (CH): 55% over 797 m
3. Black Pipe, SkiWelt Wilder Kaiser (AT): 55% over 303 m
4. Les Chalets Verts, Bernex (FR): 53% over 443 m
5. Lazid x-dream, Serfaus-Fiss-Ladis (AT): 52% over 583 m

**North America**
1. Whitetail, Big Sky: 73% over 583 m
2. Hells Half Face, Big Sky: 71% over 375 m
3. Breakover, Crystal Mountain: 68% over 328 m
4. Regal Chute, Alta: 67% over 363 m
5. Santa Clause, Alta: 66% over 347 m

A few caveats:
- This is the average over the whole run. Famous runs like Harakiri in Mayrhofen have a much steeper pitch (the famous 78%) but a gentler average over their full length, so they don't top this list.
- It's only as good as the OpenStreetMap data. If a run looks off, it's usually because of how it's mapped, and I'd love to hear about it.

Full top 25 lists:
Alps: https://skiinfoapp.com/en/guides/steepest-ski-runs-in-the-alps/?ref=reddit-skiing
North America: https://skiinfoapp.com/en/guides/steepest-ski-runs-in-north-america/?ref=reddit-skiing

On each resort's page you can tap any run and see its profile, e.g. Big Sky: https://skiinfoapp.com/en/resort/big-sky/?ref=reddit-skiing

It's my own side project: free, no account. Which runs do you think are missing?
```

---

## 2. r/OpenStreetMap

Tipo: post de texto.

**Título:**
```
I built a ski resort site on top of OpenSkiMap data: piste maps and gradient profiles for 1,276 resorts
```

**Texto:**
```
I wanted to share a project that exists thanks to everyone who maps ski areas.

Ski Info (https://skiinfoapp.com/en/?ref=reddit-osm) takes the pistes, lifts and amenities from OpenStreetMap via OpenSkiMap and turns them into a piste map and stats for each resort. Runs are laid over an elevation model, so you can tap any run and see its gradient profile section by section.

Some things that might interest mappers:
- Every resort page has a "data quality" block showing what share of runs and lifts have each tag (names, piste:difficulty, lit, snowmaking, aerialway:capacity, aerialway:detachable). It makes the gaps pretty visible: snowmaking, for example, is almost never tagged.
- The gradient rankings surface mapping errors quickly: a "green" run with a 60% average usually means a wrong difficulty tag or a way drawn in the wrong place.
- piste:difficulty is shown in each region's own colours (OpenSkiMap's run convention): "easy" is a blue run in the Alps but a green circle in North America, where "expert" becomes a double black diamond.

Example, the steepest runs in the Alps: https://skiinfoapp.com/en/guides/steepest-ski-runs-in-the-alps/?ref=reddit-osm

Every page and map credits © OpenStreetMap contributors (ODbL). Feedback very welcome, especially on tags I should be using and am not.
```

---

## 3. r/SideProject

Tipo: post de texto.

**Título:**
```
I built a free piste map + snow forecast site for 1,276 ski resorts, running on a static site with no backend
```

**Texto:**
```
Ski Info: https://skiinfoapp.com/en/?ref=reddit-sideproject

What it does:
- A piste map for 1,276 ski resorts in 45 countries, with the gradient profile of every run
- A 7-day snow forecast for every resort, plus a daily "where will it snow most" ranking
- Rankings: biggest resorts, steepest runs, resorts near Geneva / Munich / Denver / Tokyo...
- English and Spanish

How it's built:
- The data comes from OpenStreetMap / OpenSkiMap, processed with a Python pipeline
- Everything is a static site on GitHub Pages. A GitHub Action rebuilds it every morning with the new snow forecast from Open-Meteo and regenerates ~2,700 pages (one per resort and language) for SEO
- The Android app is a thin WebView over the same site
- Lighthouse scores 98-100 on mobile. Self-hosting the fonts and inlining the home page data made the biggest difference

Happy to answer questions about any of it, and I'd love feedback on what would make you actually use it.
```

---

## 4. r/snowboarding (esperar a las primeras nevadas fuertes)

Tipo: post de texto. Antes de publicar, abre la guía y cambia los datos
del texto por los de ese día (las estaciones y los cm cambian a diario).

**Título:**
```
I made a free daily ranking of where it's going to snow most this week, for 1,200+ resorts
```

**Texto:**
```
Every morning it pulls the 7-day snowfall forecast for every resort (at summit altitude) and ranks them by region: Alps, North America, Japan, Pyrenees...

This week's top spots: [RELLENA: 3 estaciones con sus cm, sacadas de la guía el día que publiques]

https://skiinfoapp.com/en/guides/where-it-will-snow-this-week/?ref=reddit-snowboarding

Each resort page also has the piste map and the gradient of every run. It's my own side project, free, no account. Let me know if your local hill is missing.
```

---

## 5. Foros en español (Nevasport, grupos de Telegram / WhatsApp de esquí)

**Título:**
```
He hecho una web gratuita para analizar las estaciones de esquí pista a pista, ¿qué os parece?
```

**Texto:**
```
Hola a todos. Llevo un tiempo con un proyecto personal y me gustaría saber qué opináis los que esquiáis de verdad.

Casi todos los mapas de pistas te dicen si una pista es roja o negra y poco más. Yo quería saber cómo es cada pista antes de llegar, así que he hecho una web que analiza cada estación pista a pista:

- Tocas cualquier pista y ves su perfil tramo a tramo: longitud, desnivel, pendiente media y el tramo más empinado
- Remontes con tipo, capacidad, duración del trayecto y si tienen burbuja o asientos calefactados
- Filtros de pistas por dificultad, nocturnas y de bosque
- Previsión de nieve a 7 días y tiempo actual de cada estación
- Rankings, como las pistas más empinadas de España o las estaciones más grandes de los Pirineos

Tiene 1.276 estaciones de 45 países, con datos de OpenStreetMap y un modelo de elevación. Es gratis y sin registro.

Para probarla, por ejemplo Baqueira: tocad Pasarells, que sale como la pista más empinada de España (51 % de media)
https://skiinfoapp.com/estacion/baqueira-beret/?ref=nevasport

O buscad vuestra estación: https://skiinfoapp.com/?ref=nevasport

Me encantaría saber:
1. ¿Os resulta útil ver la información pista a pista para preparar un viaje o un día de esquí?
2. ¿Qué echáis en falta de cada pista o estación?
3. ¿Veis algo mal en vuestra estación? Los datos vienen de OpenStreetMap y algunas están mejor mapeadas que otras.

¡Gracias por echarle un ojo!
```

### 5b. Alternativa en español: post con datos

**Título:**
```
He calculado la pendiente real de todas las pistas de España y Andorra: la más empinada es Pasarells (Baqueira), 51 %
```

**Texto:**
```
Llevo un tiempo haciendo una web gratuita con el mapa de pistas de unas 1.300 estaciones, y quería saber la pendiente real de cada pista, no solo su color. He cogido las pistas de OpenStreetMap, las he cruzado con un modelo de elevación y he calculado la pendiente tramo a tramo.

Las más empinadas de España y Andorra (pendiente media de arriba abajo, pistas de 300 m o más):
1. Pasarells, Baqueira-Beret: 51 % en 425 m
2. Pala Boja, Vall de Núria: 50 % en 302 m
3. La Canal, Masella: 48 % en 458 m
4. Pala Fuerte, Valdezcaray: 47 % en 404 m
5. Vista Cerví, Boí Taüll: 47 % en 991 m

Ojo: es la pendiente media de toda la pista; muchas tienen un tramo bastante más empinado que la media. Y depende de cómo esté mapeada cada pista en OpenStreetMap, así que si veis alguna rara, decídmelo.

Las 25 primeras: https://skiinfoapp.com/guias/pistas-mas-empinadas-espana-andorra/?ref=nevasport

En la ficha de cada estación podéis tocar cualquier pista y ver su perfil, por ejemplo Baqueira: https://skiinfoapp.com/estacion/baqueira-beret/?ref=nevasport

También tiene la previsión de nieve a 7 días de cada estación. Es un proyecto personal, gratis y sin registro. ¿Qué pista echáis en falta?
```

Para grupos de WhatsApp o Telegram, cambia `?ref=nevasport` por
`?ref=whatsapp` o `?ref=telegram`.
