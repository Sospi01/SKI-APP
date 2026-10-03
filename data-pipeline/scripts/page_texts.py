"""Text of the generated station, country and /app pages in the languages
added after Spanish and English (build_seo_pages.py keeps those two inline).
Same keys as build_seo_pages.TX / APP_TX / APP_HEAD."""

OSM = '<a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">'

TX = {
    "fr": {
        "resort": "Station de ski", "official_site": "Site officiel ↗", "altitude": "Altitude", "vertical": "Dénivelé",
        "km_pistes": "Km de pistes", "coords": "Coordonnées", "linked": "Domaine skiable relié",
        "linked_note": "Détecté par proximité géographique ; les km de chaque station peuvent se chevaucher :",
        "directions": "Itinéraire", "share": "Partager", "save": "Enregistrer", "back_country": "Stations de ski : {0}",
        "back_countries": "Pays", "open_map": "Ouvrir le plan des pistes interactif",
        "intro_1": "{0} est une station de ski{1}.", "intro_in": " ({0})",
        "intro_2": "Elle compte {0} km de pistes répartis sur {1} pistes nommées{2}.", "intro_2_lifts": " et {0} remontées",
        "intro_3": "Le domaine s'étend de {0} à {1} m d'altitude, soit {2} m de dénivelé.",
        "intro_4": "Vous trouverez ici toutes ses pistes avec leur profil de pente, ses remontées et les services sur le domaine ; "
                   "la carte interactive les montre sur image satellite.",
        "intro_h2": "{0} : plan des pistes et données", "terrain": "Terrain par difficulté", "lifts_by_type": "Remontées par type",
        "other": "Autre", "vert_m": "{0} m de dénivelé", "avg_grad": "pente moy. {0} %", "alt_range": "{0}–{1} m d'alt.",
        "max_grad": "max {0} %", "max_grad_title": "Pente maximale : le tronçon le plus raide d'au moins 50 m",
        "sections": "{0} tronçons", "floodlit": "Nocturne", "glades": "En forêt", "all_f": "Toutes", "unclassified": "Non classées",
        "pph": "{0} pers./h", "seats": "{0} places", "ride": "{0} de trajet", "unnamed": "Sans nom",
        "detachable": "Débrayable", "bubble": "Bulle", "heated": "Sièges chauffants", "private": "Privé", "all_m": "Toutes",
        "no_services": "Aucun service n'est enregistré dans OpenStreetMap pour cette station.",
        "no_services_data": "Nous n'avons pas encore de données de services pour cette station.",
        "catalog_h2": "Pistes, remontées et services", "catalog_sub": "touchez une piste pour voir son profil",
        "what_to_list": "Que lister", "runs": "Pistes", "lifts": "Remontées", "services": "Services",
        "no_runs": "Aucune piste nommée dans les données de cette station.",
        "no_lifts": "Aucune remontée dans les données de cette station.",
        "q_named": "Pistes nommées", "q_diff": "Difficulté renseignée", "q_lit": "Éclairage renseigné",
        "q_snow": "Neige de culture renseignée", "q_cap": "Débit des remontées renseigné", "q_grip": "Type d'attache renseigné",
        "quality": "Qualité des données",
        "quality_note": "La neige de culture et les pistes surveillées sont rarement renseignées dans OpenStreetMap — "
                        "cela ne veut pas dire qu'elles n'existent pas, mais que presque personne ne les cartographie encore.",
        "map_h2": "Carte interactive",
        "map_text": "Les pistes et remontées de {0} sur image satellite, le sens de chaque piste, la pente réelle de chaque tronçon, "
                    "les services et la météo en direct.",
        "map_cta": "Ouvrir la carte de {0}", "ranks": "Dans les classements", "nearby": "Stations proches",
        "nearby_meta": "à {0} km · {1} km de pistes", "snow_h2": "Neige et météo à {0}", "top_txt": " (en haut, {0} m)",
        "snow_sum": "Prévisions de neige pour les 7 prochains jours{0} : {1}{2}", "snow_cm": "{0} cm",
        "snow_none": "pas de chute de neige significative", "snow_when": " (mise à jour le {0}).",
        "snow_generic": "Prévisions de neige et météo pour les 7 prochains jours à {0}{1}.",
        "title": "{0} : plan des pistes, prévisions de neige et remontées | Ski Info",
        "d_km": "{0} km de pistes", "d_runs": "{0} pistes", "d_lifts": "{0} remontées", "d_alt": "Altitude {0}–{1} m. ",
        "d_tail": "Prévisions de neige à 7 jours, plan des pistes interactif sur satellite et pente réelle de chaque piste.",
        "c_eyebrow": "Pays", "c_h1": "Stations de ski : {0}",
        "c_sub": "{0} stations · {1} km de pistes. Choisissez une station pour voir chaque piste avec son profil de pente, "
                 "ses remontées, ses services et la carte satellite interactive.",
        "c_title": "Stations de ski : {0} – plans des pistes | Ski Info",
        "c_desc": "Les {0} stations de ski ({1}) avec plan des pistes interactif, profil de pente, remontées et services.",
        "card_pista": "de pistes", "card_total": "de pistes", "n_resorts": "{0} stations",
        "ci_h1": "Stations de ski par pays",
        "ci_sub": "{0} stations dans {1} pays, avec plan des pistes interactif, profil de pente de chaque piste, remontées et services.",
        "ci_title": "Stations de ski par pays : plans des pistes | Ski Info",
        "ci_desc": "Plans des pistes interactifs de {0} stations de ski dans {1} pays : pistes, remontées, pentes et services.",
        "f_countries": "Stations par pays", "f_guides": "Guides et classements", "f_app": "Application mobile",
        "f_privacy": "Confidentialité",
        "f_data": f"Données © {OSM}contributeurs d'OpenStreetMap</a> (ODbL), via OpenSkiMap.",
    },
    "de": {
        "resort": "Skigebiet", "official_site": "Offizielle Website ↗", "altitude": "Höhe", "vertical": "Höhenunterschied",
        "km_pistes": "Pisten-km", "coords": "Koordinaten", "linked": "Verbundenes Skigebiet",
        "linked_note": "Anhand der geografischen Nähe erkannt; die Kilometer können sich überschneiden:",
        "directions": "Anfahrt", "share": "Teilen", "save": "Merken", "back_country": "Skigebiete: {0}",
        "back_countries": "Länder", "open_map": "Interaktiven Pistenplan öffnen",
        "intro_1": "{0} ist ein Skigebiet{1}.", "intro_in": " ({0})",
        "intro_2": "Es hat {0} km Pisten auf {1} benannten Abfahrten{2}.", "intro_2_lifts": " und {0} Lifte",
        "intro_3": "Das Skigebiet reicht von {0} bis {1} m Höhe, das sind {2} Höhenmeter.",
        "intro_4": "Hier findest du alle Pisten mit ihrem Gefälleprofil, die Lifte und die Einrichtungen am Berg; "
                   "die interaktive Karte zeigt sie auf dem Satellitenbild.",
        "intro_h2": "{0}: Pistenplan und Daten", "terrain": "Pisten nach Schwierigkeit", "lifts_by_type": "Lifte nach Art",
        "other": "Sonstige", "vert_m": "{0} m Höhenunterschied", "avg_grad": "Ø-Gefälle {0} %", "alt_range": "{0}–{1} m Höhe",
        "max_grad": "max. {0} %", "max_grad_title": "Maximales Gefälle: der steilste Abschnitt von mindestens 50 m",
        "sections": "{0} Abschnitte", "floodlit": "Flutlicht", "glades": "Waldabfahrt", "all_f": "Alle", "unclassified": "Ohne Klasse",
        "pph": "{0} P./h", "seats": "{0} Plätze", "ride": "{0} Fahrzeit", "unnamed": "Ohne Namen",
        "detachable": "Kuppelbar", "bubble": "Haube", "heated": "Sitzheizung", "private": "Privat", "all_m": "Alle",
        "no_services": "Für dieses Skigebiet sind in OpenStreetMap keine Einrichtungen eingetragen.",
        "no_services_data": "Für dieses Skigebiet haben wir noch keine Daten zu Einrichtungen.",
        "catalog_h2": "Pisten, Lifte und Einrichtungen", "catalog_sub": "tippe auf eine Piste für ihr Profil",
        "what_to_list": "Was anzeigen", "runs": "Pisten", "lifts": "Lifte", "services": "Einrichtungen",
        "no_runs": "In den Daten dieses Skigebiets gibt es keine benannten Pisten.",
        "no_lifts": "In den Daten dieses Skigebiets gibt es keine Lifte.",
        "q_named": "Benannte Pisten", "q_diff": "Schwierigkeit erfasst", "q_lit": "Beleuchtung erfasst",
        "q_snow": "Beschneiung erfasst", "q_cap": "Liftkapazität erfasst", "q_grip": "Klemmenart erfasst",
        "quality": "Datenqualität",
        "quality_note": "Beschneiung und Pistenrettung sind in OpenStreetMap selten erfasst — das heißt nicht, dass es sie "
                        "nicht gibt, sondern dass sie kaum jemand kartiert.",
        "map_h2": "Interaktive Karte",
        "map_text": "Die Pisten und Lifte von {0} auf dem Satellitenbild, die Richtung jeder Piste, das echte Gefälle jedes "
                    "Abschnitts, die Einrichtungen und das aktuelle Wetter.",
        "map_cta": "Karte von {0} öffnen", "ranks": "In den Rankings", "nearby": "Skigebiete in der Nähe",
        "nearby_meta": "{0} km entfernt · {1} km Pisten", "snow_h2": "Schnee und Wetter: {0}", "top_txt": " (Bergstation, {0} m)",
        "snow_sum": "Schneeprognose für die nächsten 7 Tage{0}: {1}{2}", "snow_cm": "{0} cm",
        "snow_none": "kein nennenswerter Schneefall", "snow_when": " (aktualisiert am {0}).",
        "snow_generic": "Schnee- und Wetterprognose für die nächsten 7 Tage: {0}{1}.",
        "title": "{0}: Pistenplan, Schneeprognose und Lifte | Ski Info",
        "d_km": "{0} km Pisten", "d_runs": "{0} Pisten", "d_lifts": "{0} Lifte", "d_alt": "Höhe {0}–{1} m. ",
        "d_tail": "7-Tage-Schneeprognose, interaktiver Pistenplan auf Satellitenbild und das echte Gefälle jeder Piste.",
        "c_eyebrow": "Länder", "c_h1": "Skigebiete: {0}",
        "c_sub": "{0} Skigebiete · {1} km Pisten. Wähle ein Skigebiet, um jede Piste mit ihrem Gefälleprofil, die Lifte, "
                 "Einrichtungen und die interaktive Satellitenkarte zu sehen.",
        "c_title": "Skigebiete: {0} – Pistenpläne | Ski Info",
        "c_desc": "Die {0} Skigebiete ({1}) mit interaktivem Pistenplan, Gefälleprofil, Liften und Einrichtungen.",
        "card_pista": "Pisten", "card_total": "Pisten", "n_resorts": "{0} Skigebiete",
        "ci_h1": "Skigebiete nach Land",
        "ci_sub": "{0} Skigebiete in {1} Ländern, mit interaktivem Pistenplan, dem Gefälleprofil jeder Piste, Liften und Einrichtungen.",
        "ci_title": "Skigebiete nach Land: Pistenpläne | Ski Info",
        "ci_desc": "Interaktive Pistenpläne von {0} Skigebieten in {1} Ländern: Pisten, Lifte, Gefälle und Einrichtungen.",
        "f_countries": "Skigebiete nach Land", "f_guides": "Ratgeber & Rankings", "f_app": "Handy-App", "f_privacy": "Datenschutz",
        "f_data": f"Daten © {OSM}OpenStreetMap-Mitwirkende</a> (ODbL), über OpenSkiMap.",
    },
    "it": {
        "resort": "Stazione sciistica", "official_site": "Sito ufficiale ↗", "altitude": "Quota", "vertical": "Dislivello",
        "km_pistes": "Km di piste", "coords": "Coordinate", "linked": "Comprensorio collegato",
        "linked_note": "Rilevato per vicinanza geografica; i km di ciascuna possono sovrapporsi:",
        "directions": "Come arrivare", "share": "Condividi", "save": "Salva", "back_country": "Stazioni sciistiche: {0}",
        "back_countries": "Paesi", "open_map": "Apri la mappa interattiva delle piste",
        "intro_1": "{0} è una stazione sciistica{1}.", "intro_in": " ({0})",
        "intro_2": "Ha {0} km di piste distribuiti su {1} piste con nome{2}.", "intro_2_lifts": " e {0} impianti",
        "intro_3": "Il comprensorio va da {0} a {1} m di quota, con {2} m di dislivello.",
        "intro_4": "Qui trovi tutte le piste con il loro profilo di pendenza, gli impianti e i servizi sulle piste; "
                   "la mappa interattiva li mostra su immagine satellitare.",
        "intro_h2": "{0}: mappa delle piste e dati", "terrain": "Terreno per difficoltà", "lifts_by_type": "Impianti per tipo",
        "other": "Altro", "vert_m": "{0} m di dislivello", "avg_grad": "pend. media {0}%", "alt_range": "{0}–{1} m di quota",
        "max_grad": "max {0}%", "max_grad_title": "Pendenza massima: il tratto più ripido di almeno 50 m",
        "sections": "{0} tratti", "floodlit": "Notturna", "glades": "Nel bosco", "all_f": "Tutte", "unclassified": "Non class.",
        "pph": "{0} pers./h", "seats": "{0} posti", "ride": "{0} di viaggio", "unnamed": "Senza nome",
        "detachable": "Ad ammorsamento automatico", "bubble": "Cupola", "heated": "Sedili riscaldati", "private": "Privato",
        "all_m": "Tutti",
        "no_services": "In OpenStreetMap non sono registrati servizi per questa stazione.",
        "no_services_data": "Non abbiamo ancora dati sui servizi di questa stazione.",
        "catalog_h2": "Piste, impianti e servizi", "catalog_sub": "tocca una pista per vedere il profilo",
        "what_to_list": "Cosa elencare", "runs": "Piste", "lifts": "Impianti", "services": "Servizi",
        "no_runs": "Nei dati di questa stazione non ci sono piste con nome.",
        "no_lifts": "Nei dati di questa stazione non ci sono impianti.",
        "q_named": "Piste con nome", "q_diff": "Difficoltà indicata", "q_lit": "Illuminazione indicata",
        "q_snow": "Innevamento indicato", "q_cap": "Portata impianti indicata", "q_grip": "Tipo di ammorsamento indicato",
        "quality": "Qualità dei dati",
        "quality_note": "Innevamento e soccorso piste sono raramente indicati in OpenStreetMap: non significa che non esistano, "
                        "solo che quasi nessuno li mappa ancora.",
        "map_h2": "Mappa interattiva",
        "map_text": "Le piste e gli impianti di {0} su immagine satellitare, il senso di ogni pista, la pendenza reale di ogni tratto, "
                    "i servizi e il meteo in tempo reale.",
        "map_cta": "Apri la mappa di {0}", "ranks": "Nelle classifiche", "nearby": "Stazioni vicine",
        "nearby_meta": "a {0} km · {1} km di piste", "snow_h2": "Neve e meteo: {0}", "top_txt": " (in quota, {0} m)",
        "snow_sum": "Previsioni neve per i prossimi 7 giorni{0}: {1}{2}", "snow_cm": "{0} cm",
        "snow_none": "nessuna nevicata significativa", "snow_when": " (aggiornate il {0}).",
        "snow_generic": "Previsioni neve e meteo per i prossimi 7 giorni: {0}{1}.",
        "title": "{0}: mappa delle piste, previsioni neve e impianti | Ski Info",
        "d_km": "{0} km di piste", "d_runs": "{0} piste", "d_lifts": "{0} impianti", "d_alt": "Quota {0}–{1} m. ",
        "d_tail": "Previsioni neve a 7 giorni, mappa interattiva delle piste su satellite e pendenza reale di ogni pista.",
        "c_eyebrow": "Paesi", "c_h1": "Stazioni sciistiche: {0}",
        "c_sub": "{0} stazioni · {1} km di piste. Scegli una stazione per vedere ogni pista con il suo profilo di pendenza, "
                 "gli impianti, i servizi e la mappa satellitare interattiva.",
        "c_title": "Stazioni sciistiche: {0} – mappe delle piste | Ski Info",
        "c_desc": "Le {0} stazioni sciistiche ({1}) con mappa interattiva delle piste, profilo di pendenza, impianti e servizi.",
        "card_pista": "di piste", "card_total": "di piste", "n_resorts": "{0} stazioni",
        "ci_h1": "Stazioni sciistiche per paese",
        "ci_sub": "{0} stazioni in {1} paesi, con mappa interattiva delle piste, profilo di pendenza di ogni pista, impianti e servizi.",
        "ci_title": "Stazioni sciistiche per paese: mappe delle piste | Ski Info",
        "ci_desc": "Mappe interattive delle piste di {0} stazioni sciistiche in {1} paesi: piste, impianti, pendenze e servizi.",
        "f_countries": "Stazioni per paese", "f_guides": "Guide e classifiche", "f_app": "App per il cellulare", "f_privacy": "Privacy",
        "f_data": f"Dati © {OSM}contributori di OpenStreetMap</a> (ODbL), tramite OpenSkiMap.",
    },
}

APP_TX = {
    "fr": {"add_home": "Écran d'accueil", "available": "Disponible sur", "soon": "Bientôt sur",
           "soon_note": "L'application est en phase de test. En attendant, vous pouvez utiliser Ski Info dans Chrome et l'installer : "
                        "menu <b>⋮</b> → <b>Ajouter à l'écran d'accueil</b> (ou <b>Installer l'application</b>).",
           "h1": "Ski Info sur votre téléphone",
           "lead": "Les plans des pistes, la pente de chaque piste et les prévisions de neige de {0}+ stations, toujours à portée de main. "
                   "Gratuit et sans inscription.",
           "b1": "S'ouvre comme une application", "b1t": "Avec son icône sur l'écran d'accueil, en plein écran.",
           "b2": "Fonctionne avec peu de réseau", "b2t": "Les stations déjà consultées s'ouvrent même sans réseau sur les pistes.",
           "b3": "Toujours à jour", "b3t": "Aucune mise à jour à télécharger : toujours la dernière version.",
           "inapp": "Vous utilisez déjà l'application Ski Info. Merci !", "ios_h2": "iPhone et iPad",
           "ios_lead": "Pas besoin de l'App Store : elle s'installe depuis <b>Safari</b> en trois étapes.",
           "s1": "Ouvrez <b>skiinfoapp.com/fr/</b> dans Safari et touchez le bouton <b>Partager</b> <i class=\"ico\">{0}</i> dans la barre du bas.",
           "s2": "Faites défiler et touchez <b>Sur l'écran d'accueil</b> <i class=\"ico\">{0}</i>.",
           "s3": "Touchez <b>Ajouter</b>. Ski Info apparaîtra sur votre écran d'accueil comme n'importe quelle application.",
           "chrome_ios": "Si vous utilisez Chrome sur iPhone, le bouton Partager se trouve en haut, à côté de la barre d'adresse.",
           "pc_h2": "Sur ordinateur",
           "pc": "Rien à installer : rendez-vous sur <a href=\"/fr/\">skiinfoapp.com/fr/</a>. Dans Chrome ou Edge, vous pouvez aussi "
                 "l'installer avec l'icône <b>Installer</b> à droite de la barre d'adresse.",
           "title": "Téléchargez Ski Info : application de plans des pistes et de neige pour Android et iPhone",
           "desc": "Installez Ski Info sur votre téléphone : plans des pistes, pente de chaque piste et prévisions de neige de "
                   "{0}+ stations de ski. Android et iPhone, gratuit et sans inscription."},
    "de": {"add_home": "Home-Bildschirm", "available": "Jetzt bei", "soon": "Bald bei",
           "soon_note": "Die App ist in der Testphase. Bis dahin kannst du Ski Info in Chrome nutzen und installieren: "
                        "Menü <b>⋮</b> → <b>Zum Startbildschirm hinzufügen</b> (oder <b>App installieren</b>).",
           "h1": "Ski Info auf dem Handy",
           "lead": "Pistenpläne, das Gefälle jeder Piste und die Schneeprognose für {0}+ Skigebiete, immer griffbereit. "
                   "Kostenlos und ohne Anmeldung.",
           "b1": "Öffnet sich wie eine App", "b1t": "Mit eigenem Symbol auf dem Home-Bildschirm, im Vollbild.",
           "b2": "Funktioniert bei schlechtem Empfang", "b2t": "Skigebiete, die du schon geöffnet hast, laden auch ohne Netz auf der Piste.",
           "b3": "Immer aktuell", "b3t": "Keine Updates zum Herunterladen: immer die neueste Version.",
           "inapp": "Du nutzt bereits die Ski Info App. Danke!", "ios_h2": "iPhone und iPad",
           "ios_lead": "Kein App Store nötig: Installiere sie in drei Schritten über <b>Safari</b>.",
           "s1": "Öffne <b>skiinfoapp.com/de/</b> in Safari und tippe unten auf <b>Teilen</b> <i class=\"ico\">{0}</i>.",
           "s2": "Scrolle nach unten und tippe auf <b>Zum Home-Bildschirm</b> <i class=\"ico\">{0}</i>.",
           "s3": "Tippe auf <b>Hinzufügen</b>. Ski Info erscheint auf deinem Home-Bildschirm wie jede andere App.",
           "chrome_ios": "Wenn du Chrome auf dem iPhone nutzt, ist der Teilen-Knopf oben neben der Adressleiste.",
           "pc_h2": "Am Computer",
           "pc": "Nichts zu installieren: Geh auf <a href=\"/de/\">skiinfoapp.com/de/</a>. In Chrome oder Edge kannst du sie auch über "
                 "das Symbol <b>Installieren</b> rechts in der Adressleiste installieren.",
           "title": "Ski Info herunterladen: Pistenplan- und Schnee-App für Android und iPhone",
           "desc": "Installiere Ski Info auf deinem Handy: Pistenpläne, das Gefälle jeder Piste und Schneeprognosen für "
                   "{0}+ Skigebiete. Android und iPhone, kostenlos und ohne Anmeldung."},
    "it": {"add_home": "Schermata Home", "available": "Disponibile su", "soon": "Presto su",
           "soon_note": "L'app è in fase di test. Nel frattempo puoi usare Ski Info da Chrome e installarla: "
                        "menu <b>⋮</b> → <b>Aggiungi a schermata Home</b> (o <b>Installa app</b>).",
           "h1": "Ski Info sul tuo telefono",
           "lead": "Le mappe delle piste, la pendenza di ogni pista e le previsioni neve di {0}+ stazioni, sempre a portata di mano. "
                   "Gratis e senza registrazione.",
           "b1": "Si apre come un'app", "b1t": "Con la sua icona nella schermata Home, a schermo intero.",
           "b2": "Funziona con poco segnale", "b2t": "Le stazioni che hai già consultato si aprono anche senza segnale sulle piste.",
           "b3": "Sempre aggiornata", "b3t": "Nessun aggiornamento da scaricare: sempre l'ultima versione.",
           "inapp": "Stai già usando l'app Ski Info. Grazie!", "ios_h2": "iPhone e iPad",
           "ios_lead": "Non serve l'App Store: si installa da <b>Safari</b> in tre passaggi.",
           "s1": "Apri <b>skiinfoapp.com/it/</b> in Safari e tocca il pulsante <b>Condividi</b> <i class=\"ico\">{0}</i> nella barra in basso.",
           "s2": "Scorri verso il basso e tocca <b>Aggiungi alla schermata Home</b> <i class=\"ico\">{0}</i>.",
           "s3": "Tocca <b>Aggiungi</b>. Ski Info comparirà nella schermata Home come qualsiasi altra app.",
           "chrome_ios": "Se usi Chrome su iPhone, il pulsante Condividi è in alto, accanto alla barra degli indirizzi.",
           "pc_h2": "Sul computer",
           "pc": "Non c'è niente da installare: vai su <a href=\"/it/\">skiinfoapp.com/it/</a>. In Chrome o Edge puoi anche installarla "
                 "con l'icona <b>Installa</b> a destra della barra degli indirizzi.",
           "title": "Scarica Ski Info: app di mappe delle piste e neve per Android e iPhone",
           "desc": "Installa Ski Info sul tuo telefono: mappe delle piste, pendenza di ogni pista e previsioni neve di "
                   "{0}+ stazioni sciistiche. Android e iPhone, gratis e senza registrazione."},
}

# <head> of the app's own copy in each language (/fr/, /de/, /it/).
APP_HEAD = {
    "fr": {"title": "Ski Info · Plans des pistes et prévisions de neige des stations de ski",
           "description": "Plans des pistes interactifs sur image satellite, profil de pente de chaque piste, remontées, services et "
                          "prévisions de neige à 7 jours pour plus de 1 200 stations de ski dans 45 pays.",
           "og_title": "Ski Info · Plans des pistes et prévisions de neige",
           "og_description": "Plans des pistes sur satellite, la pente réelle de chaque piste et les prévisions de neige de plus de "
                             "1 200 stations de ski. Gratuit et sans inscription."},
    "de": {"title": "Ski Info · Pistenpläne und Schneeprognosen für Skigebiete",
           "description": "Interaktive Pistenpläne auf Satellitenbild, das Gefälleprofil jeder Piste, Lifte, Einrichtungen und "
                          "7-Tage-Schneeprognosen für über 1.200 Skigebiete in 45 Ländern.",
           "og_title": "Ski Info · Pistenpläne und Schneeprognosen",
           "og_description": "Pistenpläne auf Satellitenbild, das echte Gefälle jeder Piste und die Schneeprognose für über 1.200 "
                             "Skigebiete. Kostenlos und ohne Anmeldung."},
    "it": {"title": "Ski Info · Mappe delle piste e previsioni neve delle stazioni sciistiche",
           "description": "Mappe interattive delle piste su immagine satellitare, profilo di pendenza di ogni pista, impianti, servizi "
                          "e previsioni neve a 7 giorni per oltre 1.200 stazioni sciistiche in 45 paesi.",
           "og_title": "Ski Info · Mappe delle piste e previsioni neve",
           "og_description": "Mappe delle piste su satellite, la pendenza reale di ogni pista e le previsioni neve di oltre 1.200 "
                             "stazioni sciistiche. Gratis e senza registrazione."},
}

MONTHS = {
    "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"],
    "de": ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"],
    "it": ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"],
}
DATE_FMT = {"fr": "{d} {m}", "de": "{d}. {m}", "it": "{d} {m}"}
