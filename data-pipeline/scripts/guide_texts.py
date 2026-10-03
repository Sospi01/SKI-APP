"""The words of the guides (build_guides.py), one block per language.

Spanish is the site's original wording; the others say the same thing the way
a native reader would expect (their own zones, cities and search phrases, not
word-for-word translations). Placeholders: {zone} is "de los Alpes"-style,
{zone_in} "en los Alpes"-style (the same in languages that don't need both),
{n} list size, {top}/{place} the first station, {km}/{hi}/{lo}/{v}/{p}/{len}/
{vert}/{cm}/{d} numbers already formatted for the language.
"""

# Where each language's pages live (see LOC in build_seo_pages.py). Languages
# without share images of their own use the English ones.
PATHS = {
    "es": {"home": "/", "guides": "/guias/", "station": "/estacion/", "index_json": "guias.json", "og_dir": "/og/", "locale": "es-ES"},
    "en": {"home": "/en/", "guides": "/en/guides/", "station": "/en/resort/", "index_json": "en/guides.json", "og_dir": "/og/en/", "locale": "en-GB"},
    "fr": {"home": "/fr/", "guides": "/fr/guides/", "station": "/fr/station/", "index_json": "fr/guides.json", "og_dir": "/og/en/", "locale": "fr-FR"},
    "de": {"home": "/de/", "guides": "/de/ratgeber/", "station": "/de/skigebiet/", "index_json": "de/ratgeber.json", "og_dir": "/og/en/", "locale": "de-DE"},
    "it": {"home": "/it/", "guides": "/it/guide/", "station": "/it/stazione/", "index_json": "it/guide.json", "og_dir": "/og/en/", "locale": "it-IT"},
}

# zone -> lang -> (zone, zone_in)
ZONE_TXT = {
    "iberia": {"es": ("de España y Andorra",) * 2, "en": ("in Spain & Andorra",) * 2,
               "fr": ("d'Espagne et d'Andorre", "en Espagne et en Andorre"),
               "de": ("in Spanien und Andorra",) * 2, "it": ("di Spagna e Andorra", "in Spagna e Andorra")},
    "pyrenees": {"es": ("de los Pirineos",) * 2, "en": ("in the Pyrenees",) * 2,
                 "fr": ("des Pyrénées", "dans les Pyrénées"), "de": ("der Pyrenäen", "in den Pyrenäen"),
                 "it": ("dei Pirenei", "sui Pirenei")},
    "alps": {"es": ("de los Alpes",) * 2, "en": ("in the Alps",) * 2, "fr": ("des Alpes", "dans les Alpes"),
             "de": ("der Alpen", "in den Alpen"), "it": ("delle Alpi", "nelle Alpi")},
    "world": {"es": ("del mundo",) * 2, "en": ("in the world",) * 2, "fr": ("du monde", "dans le monde"),
              "de": ("der Welt", "weltweit"), "it": ("del mondo", "nel mondo")},
    "north_america": {"es": ("de Norteamérica",) * 2, "en": ("in North America",) * 2,
                      "fr": ("d'Amérique du Nord", "en Amérique du Nord"), "de": ("Nordamerikas", "in Nordamerika"),
                      "it": ("del Nord America", "in Nord America")},
    "japan": {"es": ("de Japón",) * 2, "en": ("in Japan",) * 2, "fr": ("du Japon", "au Japon"),
              "de": ("Japans", "in Japan"), "it": ("del Giappone", "in Giappone")},
}

# What each language publishes: (slug, zone, list size[, min km]). Published
# slugs are live URLs already known to search engines: never change them.
SPECS = {
    "es": {
        "biggest": [("estaciones-mas-grandes-espana-andorra", "iberia", 20), ("estaciones-mas-grandes-pirineos", "pyrenees", 20),
                    ("estaciones-mas-grandes-alpes", "alps", 25), ("estaciones-mas-grandes-del-mundo", "world", 25)],
        "beginners": [("estaciones-para-principiantes-espana-andorra", "iberia", 15, 10),
                      ("estaciones-para-principiantes-alpes", "alps", 20, 40)],
        "highest": [("estaciones-mas-altas-espana-andorra", "iberia", 15), ("estaciones-mas-altas-alpes", "alps", 20)],
        "vertical": [("estaciones-con-mas-desnivel-espana-andorra", "iberia", 15)],
        "steep": [("pistas-mas-empinadas-espana-andorra", "iberia", 25), ("pistas-mas-empinadas-alpes", "alps", 25)],
        "long": [("pistas-mas-largas-espana-andorra", "iberia", 25), ("pistas-mas-largas-alpes", "alps", 25)],
        "snow": "donde-nieva-esta-semana",
    },
    "en": {
        "biggest": [("biggest-ski-resorts-in-the-world", "world", 25), ("biggest-ski-resorts-in-the-alps", "alps", 25),
                    ("biggest-ski-resorts-in-north-america", "north_america", 20), ("biggest-ski-resorts-in-japan", "japan", 15),
                    ("biggest-ski-resorts-in-the-pyrenees", "pyrenees", 20),
                    ("biggest-ski-resorts-in-spain-and-andorra", "iberia", 20)],
        "beginners": [("best-ski-resorts-for-beginners-in-the-alps", "alps", 20, 40),
                      ("best-ski-resorts-for-beginners-in-north-america", "north_america", 20, 30),
                      ("best-ski-resorts-for-beginners-in-spain-and-andorra", "iberia", 15, 10)],
        "highest": [("highest-ski-resorts-in-the-alps", "alps", 20), ("highest-ski-resorts-in-north-america", "north_america", 20)],
        "vertical": [("ski-resorts-with-the-most-vertical-in-the-alps", "alps", 20),
                     ("ski-resorts-with-the-most-vertical-in-north-america", "north_america", 20)],
        "steep": [("steepest-ski-runs-in-the-alps", "alps", 25), ("steepest-ski-runs-in-north-america", "north_america", 25),
                  ("steepest-ski-runs-in-spain-and-andorra", "iberia", 25)],
        "long": [("longest-ski-runs-in-the-alps", "alps", 25), ("longest-ski-runs-in-north-america", "north_america", 25)],
        "snow": "where-it-will-snow-this-week",
    },
    "fr": {
        "biggest": [("plus-grandes-stations-de-ski-des-alpes", "alps", 25), ("plus-grandes-stations-de-ski-du-monde", "world", 25),
                    ("plus-grandes-stations-de-ski-des-pyrenees", "pyrenees", 20),
                    ("plus-grandes-stations-de-ski-d-amerique-du-nord", "north_america", 20)],
        "beginners": [("meilleures-stations-de-ski-pour-debutants-dans-les-alpes", "alps", 20, 40),
                      ("meilleures-stations-de-ski-pour-debutants-dans-les-pyrenees", "pyrenees", 15, 10)],
        "highest": [("stations-de-ski-les-plus-hautes-des-alpes", "alps", 20)],
        "vertical": [("stations-de-ski-avec-le-plus-de-denivele-dans-les-alpes", "alps", 20)],
        "steep": [("pistes-de-ski-les-plus-raides-des-alpes", "alps", 25), ("pistes-de-ski-les-plus-raides-des-pyrenees", "pyrenees", 25)],
        "long": [("pistes-de-ski-les-plus-longues-des-alpes", "alps", 25)],
        "snow": "ou-va-t-il-neiger-cette-semaine",
    },
    "de": {
        "biggest": [("groesste-skigebiete-der-alpen", "alps", 25), ("groesste-skigebiete-der-welt", "world", 25),
                    ("groesste-skigebiete-nordamerikas", "north_america", 20)],
        "beginners": [("beste-skigebiete-fuer-anfaenger-in-den-alpen", "alps", 20, 40)],
        "highest": [("hoechste-skigebiete-der-alpen", "alps", 20)],
        "vertical": [("skigebiete-mit-den-meisten-hoehenmetern-in-den-alpen", "alps", 20)],
        "steep": [("steilste-pisten-der-alpen", "alps", 25)],
        "long": [("laengste-pisten-der-alpen", "alps", 25)],
        "snow": "wo-schneit-es-diese-woche",
    },
    "it": {
        "biggest": [("stazioni-sciistiche-piu-grandi-delle-alpi", "alps", 25), ("stazioni-sciistiche-piu-grandi-del-mondo", "world", 25)],
        "beginners": [("migliori-stazioni-sciistiche-per-principianti-nelle-alpi", "alps", 20, 40)],
        "highest": [("stazioni-sciistiche-piu-alte-delle-alpi", "alps", 20)],
        "vertical": [("stazioni-sciistiche-con-piu-dislivello-nelle-alpi", "alps", 20)],
        "steep": [("piste-da-sci-piu-ripide-delle-alpi", "alps", 25)],
        "long": [("piste-da-sci-piu-lunghe-delle-alpi", "alps", 25)],
        "snow": "dove-nevichera-questa-settimana",
    },
}

# Cities for "near ..." guides: slug -> (name, lat, lon).
CITIES = {
    "es": {"madrid": ("Madrid", 40.4168, -3.7038), "barcelona": ("Barcelona", 41.3874, 2.1686),
           "valencia": ("Valencia", 39.4699, -0.3763), "bilbao": ("Bilbao", 43.2630, -2.9350),
           "zaragoza": ("Zaragoza", 41.6488, -0.8891), "sevilla": ("Sevilla", 37.3891, -5.9845),
           "malaga": ("Málaga", 36.7213, -4.4214), "pamplona": ("Pamplona", 42.8125, -1.6458)},
    "en": {"geneva": ("Geneva", 46.2044, 6.1432), "zurich": ("Zurich", 47.3769, 8.5417),
           "munich": ("Munich", 48.1351, 11.5820), "milan": ("Milan", 45.4642, 9.1900),
           "innsbruck": ("Innsbruck", 47.2692, 11.4041), "lyon": ("Lyon", 45.7640, 4.8357),
           "denver": ("Denver", 39.7392, -104.9903), "salt-lake-city": ("Salt Lake City", 40.7608, -111.8910),
           "vancouver": ("Vancouver", 49.2827, -123.1207), "tokyo": ("Tokyo", 35.6762, 139.6503)},
    "fr": {"paris": ("Paris", 48.8566, 2.3522), "lyon": ("Lyon", 45.7640, 4.8357), "grenoble": ("Grenoble", 45.1885, 5.7245),
           "geneve": ("Genève", 46.2044, 6.1432), "marseille": ("Marseille", 43.2965, 5.3698),
           "toulouse": ("Toulouse", 43.6047, 1.4442), "nice": ("Nice", 43.7102, 7.2620), "bordeaux": ("Bordeaux", 44.8378, -0.5792)},
    "de": {"muenchen": ("München", 48.1351, 11.5820), "zuerich": ("Zürich", 47.3769, 8.5417), "wien": ("Wien", 48.2082, 16.3738),
           "innsbruck": ("Innsbruck", 47.2692, 11.4041), "salzburg": ("Salzburg", 47.8095, 13.0550),
           "stuttgart": ("Stuttgart", 48.7758, 9.1829), "frankfurt": ("Frankfurt", 50.1109, 8.6821), "berlin": ("Berlin", 52.5200, 13.4050)},
    "it": {"milano": ("Milano", 45.4642, 9.1900), "torino": ("Torino", 45.0703, 7.6869), "roma": ("Roma", 41.9028, 12.4964),
           "bologna": ("Bologna", 44.4949, 11.3426), "verona": ("Verona", 45.4384, 10.9916), "genova": ("Genova", 44.4056, 8.9463),
           "firenze": ("Firenze", 43.7696, 11.2558), "bolzano": ("Bolzano", 46.4983, 11.3548)},
}

GROUPS = {
    "es": {"snow": "Nieve", "resorts": "Estaciones", "runs": "Pistas", "near": "Cerca de tu ciudad"},
    "en": {"snow": "Snow", "resorts": "Resorts", "runs": "Runs", "near": "Near your city"},
    "fr": {"snow": "Neige", "resorts": "Stations", "runs": "Pistes", "near": "Près de chez vous"},
    "de": {"snow": "Schnee", "resorts": "Skigebiete", "runs": "Pisten", "near": "In deiner Nähe"},
    "it": {"snow": "Neve", "resorts": "Stazioni", "runs": "Piste", "near": "Vicino a te"},
}

# The guides themselves. "rank" is the phrase for the station pages' "In the
# rankings" chips, used by RANK_ITEM below.
GT = {
    "es": {
        "runs_w": "{0} pistas", "lifts_w": "{0} remontes", "km_pistes": "km de pistas", "pct": "{0} %",
        "biggest": {
            "title": "Las estaciones de esquí más grandes {zone}",
            "intro": "Las {n} estaciones de esquí con más kilómetros de pistas {zone}. La más grande es {top} ({place}), con {km} km de pistas",
            "follow": ", seguida de {name} ({km} km)", "and": " y {name} ({km} km).",
            "tail": " Pulsa cualquiera para ver su mapa de pistas, el perfil de cada pista y la previsión de nieve.",
            "method": "Ordenadas por la suma de la longitud de todas sus pistas de esquí alpino según OpenStreetMap "
                      "(no se cuentan los circuitos de fondo). Las cifras oficiales de cada estación pueden variar algo "
                      "porque cada una mide sus pistas a su manera.",
            "rank": "Estaciones más grandes {zone}", "label": "de pistas"},
        "beginners": {
            "title": "Mejores estaciones de esquí para principiantes {zone}", "h1": "Las mejores estaciones para principiantes {zone}",
            "intro": "Las estaciones {zone} donde más proporción de pistas son verdes y azules: ideales para aprender "
                     "o para esquiar tranquilo. Encabeza la lista {top}, con un {pct} % de sus {km} km en pistas fáciles. "
                     "Solo entran estaciones de al menos {min_km} km, para que haya terreno suficiente para progresar.",
            "method": "Porcentaje de kilómetros de pistas verdes y azules sobre el total de pistas de esquí alpino, "
                      "entre las estaciones con al menos {min_km} km. Datos de dificultad de OpenStreetMap.",
            "rank": "Mejores para principiantes {zone}", "label": "pistas fáciles",
            "meta": "{easy} de {km} km verdes o azules · {meta}"},
        "highest": {
            "title": "Las estaciones de esquí más altas {zone}",
            "intro": "Las estaciones {zone} que llegan más alto. Más altitud suele significar nieve de más calidad "
                     "y temporadas más largas. La más alta es {top}, que alcanza los {hi} m.",
            "method": "Cota más alta a la que llega una pista o un remonte de la estación, según OpenStreetMap y el modelo de elevación.",
            "rank": "Estaciones más altas {zone}", "label": "cota máxima", "meta": "desde {lo} m · {km} {km_pistes}"},
        "vertical": {
            "title": "Las estaciones de esquí con más desnivel {zone}",
            "intro": "Las estaciones {zone} con más metros de desnivel entre su punto más bajo y el más alto: "
                     "las bajadas más largas del día. Lidera {top}, con {v} m de desnivel.",
            "method": "Diferencia entre la cota más alta y la más baja de las pistas y remontes de la estación.",
            "rank": "Estaciones con más desnivel {zone}", "label": "de desnivel", "meta": "{lo}–{hi} m · {km} {km_pistes}"},
        "steep": {
            "title": "Las pistas de esquí más empinadas {zone}",
            "intro": "Las {n} pistas con más pendiente media {zone}, medida de arriba abajo con el modelo de elevación. "
                     "La más empinada es {run}, en {station}, con un {p} % de pendiente media "
                     "en {len} m. En la ficha de cada estación puedes ver el perfil de la pista tramo a tramo.",
            "method": "Pendiente media = desnivel total ÷ longitud de la pista (en %), para pistas oficiales (verde a negra) "
                      "de al menos 300 m. En los tramos más duros la inclinación puntual es mayor que la media.",
            "rank": "Pistas más empinadas {zone}", "label": "pend. media", "meta": "{len} m · desnivel {vert} m · {diff}"},
        "long": {
            "title": "Las pistas de esquí más largas {zone}",
            "intro": "Las {n} pistas más largas {zone}. La primera es {run}, en {station}, "
                     "con {km} km de bajada y {vert} m de desnivel.",
            "method": "Longitud total de cada pista con nombre (sumando sus tramos) según OpenStreetMap, para pistas oficiales "
                      "de verde a negra.",
            "rank": "Pistas más largas {zone}", "label": "de bajada", "meta": "desnivel {vert} m · pend. media {p} % · {diff}"},
        "near": {
            "slug": "estaciones-de-esqui-cerca-de-{city}", "title": "Estaciones de esquí cerca de {city}",
            "intro": "Las estaciones de esquí más cercanas a {city}, de la más próxima a la más lejana. "
                     "La más cercana es {top}, a unos {d} km en línea recta"
                     "; a menos de 250 km tienes {within} estaciones."
                     " Pulsa «Cómo llegar» en la ficha de cada una para ver la ruta en coche.",
            "method": "Distancia en línea recta desde el centro de la ciudad hasta la estación; por carretera siempre es más. "
                      "Incluye estaciones de España, Andorra y Francia con al menos 3 km de pistas.",
            "rank": "Estaciones cerca de {city}", "label": "en línea recta", "meta": "{km} km de pistas · {meta}"},
        "snow": {
            "when": " (previsión del {date})",
            "intro": "Las estaciones de esquí donde más nieve se espera en los próximos 7 días{when}, en su cota más alta. "
                     "Encabeza la lista {top} ({place}), con unos {cm} cm previstos. "
                     "Se actualiza cada día; en la ficha de cada estación tienes la previsión día a día.",
            "none": "Ahora mismo no se esperan nevadas significativas en ninguna estación en los próximos 7 días{when}. "
                    "Esta página se actualiza cada día con la previsión de nieve de más de 1.200 estaciones.",
            "title": "Dónde va a nevar esta semana: previsión de nieve en las estaciones", "h1": "Dónde va a nevar esta semana",
            "method": "Suma de la nieve prevista para los próximos 7 días por los modelos meteorológicos (Open-Meteo) en la cota "
                      "más alta de cada estación. Es una previsión, no el parte oficial de nieve de la estación.",
            "label": "en 7 días"},
    },
    "en": {
        "runs_w": "{0} runs", "lifts_w": "{0} lifts", "km_pistes": "km of pistes", "pct": "{0}%",
        "biggest": {
            "title": "The biggest ski resorts {zone}",
            "intro": "The {n} ski resorts {zone} with the most kilometres of pistes. The biggest is {top} ({place}), with {km} km of pistes",
            "follow": ", followed by {name} ({km} km)", "and": " and {name} ({km} km).",
            "tail": " Tap any of them for its piste map, the gradient profile of every run and the snow forecast.",
            "method": "Ranked by the total length of their alpine runs in OpenStreetMap (cross-country trails don't count). "
                      "Official figures may differ a little, as every resort measures its runs its own way.",
            "rank": "the biggest ski resorts {zone}", "label": "of pistes"},
        "beginners": {
            "title": "Best ski resorts for beginners {zone}", "h1": "The best ski resorts for beginners {zone}",
            "intro": "The resorts {zone} where the largest share of the pistes are green and blue: ideal for learning "
                     "or for relaxed skiing. Top of the list is {top}, with {pct}% of its "
                     "{km} km on easy runs. Only resorts with at least {min_km} km are included, "
                     "so there's enough terrain to progress.",
            "method": "Share of green and blue kilometres over all alpine pistes, among resorts with at least "
                      "{min_km} km. Difficulty data from OpenStreetMap.",
            "rank": "the best resorts for beginners {zone}", "label": "easy runs",
            "meta": "{easy} of {km} km green or blue · {meta}"},
        "highest": {
            "title": "The highest ski resorts {zone}",
            "intro": "The resorts {zone} that reach highest. More altitude usually means better snow and longer "
                     "seasons. The highest is {top}, topping out at {hi} m.",
            "method": "Highest point reached by a run or lift of the resort, from OpenStreetMap and the elevation model.",
            "rank": "the highest ski resorts {zone}", "label": "top elevation", "meta": "from {lo} m · {km} {km_pistes}"},
        "vertical": {
            "title": "Ski resorts with the most vertical {zone}",
            "intro": "The resorts {zone} with the biggest vertical drop between their lowest and highest points: "
                     "the longest descents of the day. {top} leads with {v} m of vertical.",
            "method": "Difference between the highest and lowest points of the resort's runs and lifts.",
            "rank": "the resorts with the most vertical {zone}", "label": "vertical", "meta": "{lo}–{hi} m · {km} {km_pistes}"},
        "steep": {
            "title": "The steepest ski runs {zone}",
            "intro": "The {n} runs {zone} with the highest average gradient, measured top to bottom with the elevation model. "
                     "The steepest is {run} at {station}, averaging {p}% over "
                     "{len} m. Each resort's page shows the profile of every run, section by section.",
            "method": "Average gradient = total vertical ÷ run length (as %), for graded runs (green to black) of at least "
                      "300 m. On the hardest pitches the local gradient is steeper than the average.",
            "rank": "the steepest runs {zone}", "label": "avg. gradient", "meta": "{len} m · {vert} m vertical · {diff}"},
        "long": {
            "title": "The longest ski runs {zone}",
            "intro": "The {n} longest runs {zone}. First is {run} at {station}, "
                     "a {km} km descent with {vert} m of vertical.",
            "method": "Total length of each named run (adding up its sections) in OpenStreetMap, for graded runs from green to black.",
            "rank": "the longest runs {zone}", "label": "long", "meta": "{vert} m vertical · avg. gradient {p}% · {diff}"},
        "near": {
            "slug": "ski-resorts-near-{city}", "title": "Ski resorts near {city}",
            "intro": "The ski resorts closest to {city}, from nearest to farthest. The nearest is {top}, "
                     "about {d} km away as the crow flies; {within} resorts are within 250 km."
                     " Tap “Directions” on any resort's page for the driving route.",
            "method": "Straight-line distance from the city centre to the resort; by road it is always further. "
                      "Resorts with at least 3 km of pistes.",
            "rank": "the ski resorts near {city}", "label": "as the crow flies", "meta": "{km} km of pistes · {meta}"},
        "snow": {
            "when": " (forecast of {date})",
            "intro": "The ski resorts expecting the most snow over the next 7 days{when}, at their highest point. "
                     "Top of the list is {top} ({place}), with around {cm} cm forecast. "
                     "Updated every day; each resort's page has the day-by-day forecast.",
            "none": "No resort is expecting significant snowfall over the next 7 days{when}. "
                    "This page is updated every day with the snow forecast for over 1,200 resorts.",
            "title": "Where it will snow this week: ski resort snow forecast", "h1": "Where it will snow this week",
            "method": "Total snowfall forecast for the next 7 days by weather models (Open-Meteo) at each resort's highest "
                      "point. It's a forecast, not the resort's official snow report.",
            "label": "in 7 days"},
    },
    "fr": {
        "runs_w": "{0} pistes", "lifts_w": "{0} remontées", "km_pistes": "km de pistes", "pct": "{0} %",
        "biggest": {
            "title": "Les plus grandes stations de ski {zone}",
            "intro": "Les {n} stations de ski {zone} qui comptent le plus de kilomètres de pistes. La plus grande est {top} ({place}), avec {km} km de pistes",
            "follow": ", suivie de {name} ({km} km)", "and": " et {name} ({km} km).",
            "tail": " Touchez-en une pour voir son plan des pistes, le profil de chaque piste et les prévisions de neige.",
            "method": "Classées selon la longueur totale de leurs pistes de ski alpin dans OpenStreetMap (les pistes de fond ne "
                      "comptent pas). Les chiffres officiels peuvent varier un peu, chaque station mesurant ses pistes à sa manière.",
            "rank": "plus grandes stations de ski {zone}", "label": "de pistes"},
        "beginners": {
            "title": "Meilleures stations de ski pour débutants {zone_in}", "h1": "Les meilleures stations de ski pour débutants {zone_in}",
            "intro": "Les stations {zone_in} où la part de pistes vertes et bleues est la plus élevée : idéales pour apprendre "
                     "ou skier tranquillement. {top} arrive en tête, avec {pct} % de ses {km} km en pistes faciles. "
                     "Seules les stations d'au moins {min_km} km sont retenues, pour avoir assez de terrain pour progresser.",
            "method": "Part des kilomètres de pistes vertes et bleues sur l'ensemble des pistes de ski alpin, parmi les stations "
                      "d'au moins {min_km} km. Difficultés issues d'OpenStreetMap.",
            "rank": "meilleures stations pour débutants {zone_in}", "label": "pistes faciles",
            "meta": "{easy} sur {km} km en vert ou bleu · {meta}"},
        "highest": {
            "title": "Les stations de ski les plus hautes {zone}",
            "intro": "Les stations {zone} qui montent le plus haut. Plus d'altitude signifie souvent une neige de meilleure qualité "
                     "et des saisons plus longues. La plus haute est {top}, qui culmine à {hi} m.",
            "method": "Point le plus haut atteint par une piste ou une remontée de la station, d'après OpenStreetMap et le modèle d'élévation.",
            "rank": "stations de ski les plus hautes {zone}", "label": "altitude max.", "meta": "depuis {lo} m · {km} {km_pistes}"},
        "vertical": {
            "title": "Les stations de ski avec le plus de dénivelé {zone_in}",
            "intro": "Les stations {zone_in} qui offrent le plus de dénivelé entre leur point le plus bas et le plus haut : "
                     "les plus longues descentes de la journée. {top} est en tête avec {v} m de dénivelé.",
            "method": "Différence entre le point le plus haut et le plus bas des pistes et remontées de la station.",
            "rank": "stations avec le plus de dénivelé {zone_in}", "label": "de dénivelé", "meta": "{lo}–{hi} m · {km} {km_pistes}"},
        "steep": {
            "title": "Les pistes de ski les plus raides {zone}",
            "intro": "Les {n} pistes {zone} avec la plus forte pente moyenne, mesurée de haut en bas avec le modèle d'élévation. "
                     "La plus raide est {run}, à {station}, avec {p} % de pente moyenne sur {len} m. "
                     "La fiche de chaque station montre le profil de chaque piste, tronçon par tronçon.",
            "method": "Pente moyenne = dénivelé total ÷ longueur de la piste (en %), pour les pistes balisées (de verte à noire) "
                      "d'au moins 300 m. Dans les passages les plus durs, la pente locale est plus forte que la moyenne.",
            "rank": "pistes les plus raides {zone}", "label": "pente moy.", "meta": "{len} m · {vert} m de dénivelé · {diff}"},
        "long": {
            "title": "Les pistes de ski les plus longues {zone}",
            "intro": "Les {n} pistes les plus longues {zone}. En tête, {run}, à {station} : {km} km de descente et {vert} m de dénivelé.",
            "method": "Longueur totale de chaque piste nommée (en additionnant ses tronçons) dans OpenStreetMap, pour les pistes "
                      "balisées de verte à noire.",
            "rank": "pistes les plus longues {zone}", "label": "de descente", "meta": "{vert} m de dénivelé · pente moy. {p} % · {diff}"},
        "near": {
            "slug": "stations-de-ski-pres-de-{city}", "title": "Stations de ski près de {city}",
            "intro": "Les stations de ski les plus proches de {city}, de la plus proche à la plus éloignée. La plus proche est {top}, "
                     "à environ {d} km à vol d'oiseau ; {within} stations sont à moins de 250 km. "
                     "Touchez « Itinéraire » sur la fiche d'une station pour voir le trajet en voiture.",
            "method": "Distance à vol d'oiseau entre le centre-ville et la station ; par la route, c'est toujours plus. "
                      "Stations d'au moins 3 km de pistes.",
            "rank": "stations de ski près de {city}", "label": "à vol d'oiseau", "meta": "{km} km de pistes · {meta}"},
        "snow": {
            "when": " (prévision du {date})",
            "intro": "Les stations de ski où il devrait tomber le plus de neige dans les 7 prochains jours{when}, à leur point le plus haut. "
                     "{top} ({place}) arrive en tête, avec environ {cm} cm prévus. "
                     "Mis à jour chaque jour ; la fiche de chaque station donne la prévision jour par jour.",
            "none": "Aucune station n'attend de chute de neige significative dans les 7 prochains jours{when}. "
                    "Cette page est mise à jour chaque jour avec les prévisions de neige de plus de 1 200 stations.",
            "title": "Où va-t-il neiger cette semaine : prévisions de neige dans les stations", "h1": "Où va-t-il neiger cette semaine",
            "method": "Cumul de neige prévu pour les 7 prochains jours par les modèles météo (Open-Meteo) au point le plus haut "
                      "de chaque station. C'est une prévision, pas le bulletin d'enneigement officiel de la station.",
            "label": "en 7 jours"},
    },
    "de": {
        "runs_w": "{0} Pisten", "lifts_w": "{0} Lifte", "km_pistes": "km Pisten", "pct": "{0} %",
        "biggest": {
            "title": "Die größten Skigebiete {zone}",
            "intro": "Die {n} Skigebiete {zone_in} mit den meisten Pistenkilometern. Das größte ist {top} ({place}) mit {km} km Pisten",
            "follow": ", gefolgt von {name} ({km} km)", "and": " und {name} ({km} km).",
            "tail": " Tippe auf eines, um den Pistenplan, das Profil jeder Piste und die Schneeprognose zu sehen.",
            "method": "Sortiert nach der Gesamtlänge der alpinen Pisten in OpenStreetMap (Langlaufloipen zählen nicht). "
                      "Offizielle Angaben können etwas abweichen, da jedes Skigebiet seine Pisten anders misst.",
            "rank": "Größte Skigebiete {zone}", "label": "Pisten"},
        "beginners": {
            "title": "Die besten Skigebiete für Anfänger {zone_in}", "h1": "Die besten Skigebiete für Anfänger {zone_in}",
            "intro": "Die Skigebiete {zone_in} mit dem höchsten Anteil an grünen und blauen Pisten: ideal zum Lernen oder für "
                     "entspanntes Skifahren. An der Spitze steht {top} mit {pct} % seiner {km} km auf leichten Pisten. "
                     "Berücksichtigt werden nur Skigebiete mit mindestens {min_km} km, damit genug Gelände zum Üben bleibt.",
            "method": "Anteil der Kilometer grüner und blauer Pisten an allen alpinen Pisten, unter den Skigebieten mit mindestens "
                      "{min_km} km. Schwierigkeitsangaben aus OpenStreetMap.",
            "rank": "Beste Skigebiete für Anfänger {zone_in}", "label": "leichte Pisten",
            "meta": "{easy} von {km} km grün oder blau · {meta}"},
        "highest": {
            "title": "Die höchsten Skigebiete {zone}",
            "intro": "Die Skigebiete {zone_in}, die am höchsten hinaufreichen. Mehr Höhe bedeutet meist besseren Schnee und längere "
                     "Saisons. Das höchste ist {top} mit bis zu {hi} m.",
            "method": "Höchster Punkt, den eine Piste oder ein Lift des Skigebiets erreicht, laut OpenStreetMap und Höhenmodell.",
            "rank": "Höchste Skigebiete {zone}", "label": "höchster Punkt", "meta": "ab {lo} m · {km} {km_pistes}"},
        "vertical": {
            "title": "Die Skigebiete mit den meisten Höhenmetern {zone_in}",
            "intro": "Die Skigebiete {zone_in} mit dem größten Höhenunterschied zwischen tiefstem und höchstem Punkt: "
                     "die längsten Abfahrten des Tages. {top} führt mit {v} Höhenmetern.",
            "method": "Differenz zwischen dem höchsten und dem tiefsten Punkt der Pisten und Lifte des Skigebiets.",
            "rank": "Meiste Höhenmeter {zone_in}", "label": "Höhenmeter", "meta": "{lo}–{hi} m · {km} {km_pistes}"},
        "steep": {
            "title": "Die steilsten Skipisten {zone}",
            "intro": "Die {n} Pisten {zone_in} mit dem höchsten durchschnittlichen Gefälle, von oben bis unten mit dem Höhenmodell "
                     "gemessen. Die steilste ist {run} in {station} mit durchschnittlich {p} % auf {len} m. "
                     "Auf der Seite jedes Skigebiets siehst du das Profil jeder Piste, Abschnitt für Abschnitt.",
            "method": "Durchschnittliches Gefälle = Höhenunterschied ÷ Pistenlänge (in %), für markierte Pisten (grün bis schwarz) "
                      "ab 300 m Länge. An den steilsten Stellen ist das Gefälle höher als der Durchschnitt.",
            "rank": "Steilste Pisten {zone}", "label": "Ø-Gefälle", "meta": "{len} m · {vert} m Höhenunterschied · {diff}"},
        "long": {
            "title": "Die längsten Skipisten {zone}",
            "intro": "Die {n} längsten Pisten {zone_in}. Ganz vorne liegt {run} in {station}: {km} km Abfahrt mit {vert} m Höhenunterschied.",
            "method": "Gesamtlänge jeder benannten Piste (Summe ihrer Abschnitte) in OpenStreetMap, für markierte Pisten von grün bis schwarz.",
            "rank": "Längste Pisten {zone}", "label": "Abfahrt", "meta": "{vert} m Höhenunterschied · Ø-Gefälle {p} % · {diff}"},
        "near": {
            "slug": "skigebiete-in-der-naehe-von-{city}", "title": "Skigebiete in der Nähe von {city}",
            "intro": "Die Skigebiete, die {city} am nächsten liegen, vom nächsten zum entferntesten. Am nächsten liegt {top}, "
                     "rund {d} km Luftlinie entfernt; {within} Skigebiete liegen im Umkreis von 250 km. "
                     "Tippe auf der Seite eines Skigebiets auf „Anfahrt“, um die Route mit dem Auto zu sehen.",
            "method": "Luftlinie vom Stadtzentrum zum Skigebiet; auf der Straße ist es immer weiter. "
                      "Skigebiete mit mindestens 3 km Pisten.",
            "rank": "Skigebiete in der Nähe von {city}", "label": "Luftlinie", "meta": "{km} km Pisten · {meta}"},
        "snow": {
            "when": " (Prognose vom {date})",
            "intro": "Die Skigebiete, in denen in den nächsten 7 Tagen{when} am meisten Schnee erwartet wird, an ihrem höchsten Punkt. "
                     "An der Spitze steht {top} ({place}) mit rund {cm} cm Neuschnee. "
                     "Wird täglich aktualisiert; auf der Seite jedes Skigebiets gibt es die Prognose Tag für Tag.",
            "none": "Derzeit erwartet kein Skigebiet in den nächsten 7 Tagen{when} nennenswerten Schneefall. "
                    "Diese Seite wird täglich mit der Schneeprognose für über 1.200 Skigebiete aktualisiert.",
            "title": "Wo es diese Woche schneit: Schneeprognose für die Skigebiete", "h1": "Wo es diese Woche schneit",
            "method": "Summe des von Wettermodellen (Open-Meteo) für die nächsten 7 Tage vorhergesagten Neuschnees am höchsten "
                      "Punkt jedes Skigebiets. Es ist eine Prognose, nicht der offizielle Schneebericht des Skigebiets.",
            "label": "in 7 Tagen"},
    },
    "it": {
        "runs_w": "{0} piste", "lifts_w": "{0} impianti", "km_pistes": "km di piste", "pct": "{0}%",
        "biggest": {
            "title": "Le stazioni sciistiche più grandi {zone}",
            "intro": "Le {n} stazioni sciistiche {zone} con più chilometri di piste. La più grande è {top} ({place}), con {km} km di piste",
            "follow": ", seguita da {name} ({km} km)", "and": " e {name} ({km} km).",
            "tail": " Tocca una stazione per vedere la mappa delle piste, il profilo di ogni pista e le previsioni neve.",
            "method": "Ordinate per lunghezza totale delle piste di sci alpino in OpenStreetMap (le piste di fondo non contano). "
                      "I dati ufficiali possono variare un po', perché ogni stazione misura le piste a modo suo.",
            "rank": "stazioni sciistiche più grandi {zone}", "label": "di piste"},
        "beginners": {
            "title": "Le migliori stazioni sciistiche per principianti {zone_in}",
            "h1": "Le migliori stazioni sciistiche per principianti {zone_in}",
            "intro": "Le stazioni {zone_in} con la quota più alta di piste verdi e blu: ideali per imparare o per sciare in "
                     "tranquillità. In testa c'è {top}, con il {pct}% dei suoi {km} km su piste facili. Sono incluse solo le "
                     "stazioni con almeno {min_km} km, perché ci sia abbastanza terreno per progredire.",
            "method": "Percentuale di chilometri di piste verdi e blu sul totale delle piste di sci alpino, tra le stazioni con "
                      "almeno {min_km} km. Difficoltà da OpenStreetMap.",
            "rank": "migliori stazioni per principianti {zone_in}", "label": "piste facili",
            "meta": "{easy} su {km} km verdi o blu · {meta}"},
        "highest": {
            "title": "Le stazioni sciistiche più alte {zone}",
            "intro": "Le stazioni {zone} che arrivano più in alto. Più quota di solito significa neve migliore e stagioni più lunghe. "
                     "La più alta è {top}, che arriva a {hi} m.",
            "method": "Punto più alto raggiunto da una pista o da un impianto della stazione, secondo OpenStreetMap e il modello di elevazione.",
            "rank": "stazioni sciistiche più alte {zone}", "label": "quota massima", "meta": "da {lo} m · {km} {km_pistes}"},
        "vertical": {
            "title": "Le stazioni sciistiche con più dislivello {zone_in}",
            "intro": "Le stazioni {zone_in} con più metri di dislivello tra il punto più basso e il più alto: le discese più lunghe "
                     "della giornata. In testa c'è {top}, con {v} m di dislivello.",
            "method": "Differenza tra il punto più alto e il più basso delle piste e degli impianti della stazione.",
            "rank": "stazioni con più dislivello {zone_in}", "label": "di dislivello", "meta": "{lo}–{hi} m · {km} {km_pistes}"},
        "steep": {
            "title": "Le piste da sci più ripide {zone}",
            "intro": "Le {n} piste {zone} con la pendenza media più alta, misurata dall'alto in basso con il modello di elevazione. "
                     "La più ripida è {run}, a {station}, con una pendenza media del {p}% su {len} m. "
                     "Nella scheda di ogni stazione trovi il profilo di ogni pista, tratto per tratto.",
            "method": "Pendenza media = dislivello totale ÷ lunghezza della pista (in %), per le piste segnalate (da verde a nera) "
                      "di almeno 300 m. Nei tratti più duri la pendenza puntuale è maggiore della media.",
            "rank": "piste più ripide {zone}", "label": "pend. media", "meta": "{len} m · {vert} m di dislivello · {diff}"},
        "long": {
            "title": "Le piste da sci più lunghe {zone}",
            "intro": "Le {n} piste più lunghe {zone}. In testa c'è {run}, a {station}: {km} km di discesa e {vert} m di dislivello.",
            "method": "Lunghezza totale di ogni pista con nome (sommando i suoi tratti) in OpenStreetMap, per le piste segnalate "
                      "da verde a nera.",
            "rank": "piste più lunghe {zone}", "label": "di discesa", "meta": "{vert} m di dislivello · pend. media {p}% · {diff}"},
        "near": {
            "slug": "stazioni-sciistiche-vicino-a-{city}", "title": "Stazioni sciistiche vicino a {city}",
            "intro": "Le stazioni sciistiche più vicine a {city}, dalla più vicina alla più lontana. La più vicina è {top}, "
                     "a circa {d} km in linea d'aria; entro 250 km ci sono {within} stazioni. "
                     "Tocca «Come arrivare» nella scheda di una stazione per vedere il percorso in auto.",
            "method": "Distanza in linea d'aria dal centro città alla stazione; su strada è sempre di più. "
                      "Stazioni con almeno 3 km di piste.",
            "rank": "stazioni sciistiche vicino a {city}", "label": "in linea d'aria", "meta": "{km} km di piste · {meta}"},
        "snow": {
            "when": " (previsione del {date})",
            "intro": "Le stazioni sciistiche dove è attesa più neve nei prossimi 7 giorni{when}, alla loro quota più alta. "
                     "In testa c'è {top} ({place}), con circa {cm} cm previsti. "
                     "Si aggiorna ogni giorno; nella scheda di ogni stazione trovi la previsione giorno per giorno.",
            "none": "Al momento nessuna stazione prevede nevicate significative nei prossimi 7 giorni{when}. "
                    "Questa pagina si aggiorna ogni giorno con le previsioni neve di oltre 1.200 stazioni.",
            "title": "Dove nevicherà questa settimana: previsioni neve nelle stazioni", "h1": "Dove nevicherà questa settimana",
            "method": "Somma della neve prevista nei prossimi 7 giorni dai modelli meteo (Open-Meteo) alla quota più alta di ogni "
                      "stazione. È una previsione, non il bollettino neve ufficiale della stazione.",
            "label": "in 7 giorni"},
    },
}

# The station pages' "In the rankings" chips: {i} position, {what} the guide's
# rank phrase; a run's chip is RUN_PREFIX + chip.
RANK_ITEM = {"es": "{i}.ª en {what}", "en": "#{i} of {what}", "fr": "N° {i} des {what}",
             "de": "Platz {i}: {what}", "it": "{i}ª tra le {what}"}
RUN_PREFIX = {"es": "{title}: ", "en": "{title}: ", "fr": "{title} : ", "de": "{title} · ", "it": "{title}: "}

# Page furniture of the guide pages and their index.
PAGE = {
    "es": {"guides": "Guías", "method": "Cómo se ha hecho esta lista", "more": "Más guías", "no1": "N.º 1: {0}",
           "empty": "Ahora mismo no hay estaciones en esta lista.",
           "stale": "Atención: esta previsión es del {0} y puede estar desactualizada. En la ficha de cada estación tienes la previsión en directo.",
           "index_h1": "Guías y rankings de esquí",
           "index_sub": "Las estaciones más grandes, las más altas y las mejores para principiantes, las pistas más empinadas y más largas, "
                        "las estaciones más cerca de tu ciudad y dónde va a nevar esta semana. Todo calculado con los datos de más de 1.200 estaciones.",
           "index_title": "Guías y rankings de estaciones de esquí | Ski Info",
           "index_desc": "Rankings de estaciones de esquí: las más grandes, las más altas, las mejores para principiantes, "
                         "las pistas más empinadas y largas, estaciones cerca de tu ciudad y dónde nieva esta semana."},
    "en": {"guides": "Guides", "method": "How this list was made", "more": "More guides", "no1": "No. 1: {0}",
           "empty": "There are no resorts in this list right now.",
           "stale": "Note: this forecast is from {0} and may be out of date. Each resort's page has the live forecast.",
           "index_h1": "Ski guides & rankings",
           "index_sub": "The biggest and highest resorts, the best for beginners, the steepest and longest runs, the resorts near your "
                        "city and where it will snow this week. All worked out from the data of over 1,200 ski resorts.",
           "index_title": "Ski resort guides & rankings | Ski Info",
           "index_desc": "Ski resort rankings: the biggest, the highest, the best for beginners, the steepest and longest runs, "
                         "resorts near your city and where it will snow this week."},
    "fr": {"guides": "Guides", "method": "Comment cette liste a été établie", "more": "Plus de guides", "no1": "N° 1 : {0}",
           "empty": "Aucune station dans cette liste pour le moment.",
           "stale": "Attention : cette prévision date du {0} et n'est peut-être plus à jour. La fiche de chaque station donne la prévision en direct.",
           "index_h1": "Guides et classements du ski",
           "index_sub": "Les stations les plus grandes et les plus hautes, les meilleures pour débutants, les pistes les plus raides et les "
                        "plus longues, les stations près de chez vous et où il va neiger cette semaine. Le tout calculé à partir des données "
                        "de plus de 1 200 stations.",
           "index_title": "Guides et classements des stations de ski | Ski Info",
           "index_desc": "Classements des stations de ski : les plus grandes, les plus hautes, les meilleures pour débutants, les pistes "
                         "les plus raides et les plus longues, les stations près de votre ville et où il neige cette semaine."},
    "de": {"guides": "Ratgeber", "method": "So ist diese Liste entstanden", "more": "Weitere Ratgeber", "no1": "Nr. 1: {0}",
           "empty": "In dieser Liste gibt es gerade keine Skigebiete.",
           "stale": "Hinweis: Diese Prognose ist vom {0} und möglicherweise nicht mehr aktuell. Auf der Seite jedes Skigebiets gibt es die aktuelle Prognose.",
           "index_h1": "Ski-Ratgeber & Rankings",
           "index_sub": "Die größten und höchsten Skigebiete, die besten für Anfänger, die steilsten und längsten Pisten, die Skigebiete "
                        "in der Nähe deiner Stadt und wo es diese Woche schneit. Alles berechnet aus den Daten von über 1.200 Skigebieten.",
           "index_title": "Ratgeber & Rankings für Skigebiete | Ski Info",
           "index_desc": "Rankings der Skigebiete: die größten, die höchsten, die besten für Anfänger, die steilsten und längsten Pisten, "
                         "Skigebiete in der Nähe deiner Stadt und wo es diese Woche schneit."},
    "it": {"guides": "Guide", "method": "Come è stata fatta questa lista", "more": "Altre guide", "no1": "N. 1: {0}",
           "empty": "Al momento non ci sono stazioni in questa lista.",
           "stale": "Attenzione: questa previsione è del {0} e potrebbe non essere aggiornata. Nella scheda di ogni stazione trovi la previsione in tempo reale.",
           "index_h1": "Guide e classifiche dello sci",
           "index_sub": "Le stazioni più grandi e più alte, le migliori per principianti, le piste più ripide e più lunghe, le stazioni "
                        "vicino alla tua città e dove nevicherà questa settimana. Tutto calcolato con i dati di oltre 1.200 stazioni.",
           "index_title": "Guide e classifiche delle stazioni sciistiche | Ski Info",
           "index_desc": "Classifiche delle stazioni sciistiche: le più grandi, le più alte, le migliori per principianti, le piste più "
                         "ripide e lunghe, le stazioni vicino alla tua città e dove nevica questa settimana."},
}
