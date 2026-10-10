"""The "FatMap alternative" page, one per language, under the guides path.

FatMap (3D mountain maps many skiers used) was bought by Strava in January
2023 and shut down on 1 October 2024; people still search for a replacement.
This page says plainly what Ski Info offers instead -- and what it doesn't --
with links straight into the 3D view of well-known resorts, and an FAQ
(FAQPage JSON-LD) that search engines and AI answers can quote.

Called by build_seo_pages.py: render(...) -> (html, url) per language.
"""
from __future__ import annotations

SLUG = {"es": "alternativa-a-fatmap", "en": "fatmap-alternative", "fr": "alternative-a-fatmap",
        "de": "fatmap-alternative", "it": "alternativa-a-fatmap", "nl": "fatmap-alternatief",
        "pl": "alternatywa-dla-fatmap"}

# Well-known resorts for each language's readers (station_slugs.json slugs).
FEATURED = {
    "es": ["baqueira-beret", "formigal", "grandvalira", "sierra-nevada", "val-thorens", "zermatt-breuil-cervinia"],
    "en": ["tignes-val-d-isere", "val-thorens", "zermatt-breuil-cervinia", "st-anton-st-christoph-stuben",
           "whistler-blackcomb", "les-trois-vallees"],
    "fr": ["val-thorens", "tignes-val-d-isere", "les-trois-vallees", "la-plagne", "les-arcs", "brevent-flegere-chamonix"],
    "de": ["st-anton-st-christoph-stuben", "solden", "kitzski", "skicircus-saalbach-hinterglemm-leogang-fieberbrunn",
           "zermatt-breuil-cervinia", "4-vallees-verbier-la-tzoumaz-nendaz-veysonnaz-thyon"],
    "it": ["livigno", "cortina-d-ampezzo", "val-di-fassa", "zermatt-breuil-cervinia", "courchevel", "val-thorens"],
    "nl": ["val-thorens", "solden", "skicircus-saalbach-hinterglemm-leogang-fieberbrunn", "les-trois-vallees",
           "st-anton-st-christoph-stuben", "kaprun-kitzsteinhorn-maiskogel"],
    "pl": ["kasprowy-wierch", "szczyrk", "val-thorens", "livigno", "solden", "kaprun-kitzsteinhorn-maiskogel"],
}

# {n}: number of resorts, {c}: countries.
TX = {
    "es": {
        "title": "Alternativa a FatMap: mapas 3D de pistas de esquí, gratis",
        "h1": "Una alternativa a FatMap para ver las pistas de esquí en 3D",
        "lead": "FatMap, el mapa 3D de montaña que usaban muchos esquiadores, cerró el 1 de octubre de 2024, después de que lo comprara Strava. "
                "Ski Info es una alternativa gratuita para las estaciones de esquí: el relieve en 3D con todas las pistas y remontes "
                "de {n} estaciones en {c} países y, además, la pendiente real de cada pista, tramo a tramo.",
        "has_h2": "Qué tiene Ski Info",
        "has": [
            "<b>Mapa 3D con relieve</b> de cada estación: pistas y remontes con su nombre, para girarlo, inclinarlo y dar la vuelta a la montaña.",
            "<b>Pendiente real de cada pista</b>: su perfil tramo a tramo en % y en grados, con los colores de los criterios de ATUDEM y AFNOR, y su tramo más empinado.",
            "<b>Mapa coloreado por pendiente</b>, no solo por dificultad oficial: para ver qué negras son suaves y qué rojas son duras.",
            "<b>{n} estaciones en {c} países</b>: Alpes, Pirineos, Norteamérica, Escandinavia, Japón, Andes…",
            "<b>Previsión de nieve a 7 días</b> en cada estación.",
            "<b>Rutas por la estación</b> (beta): cómo llegar de una pista a otra, por ejemplo sin pasar por negras.",
            "<b>Gratis y sin registrarse</b>, en la web y en Android, en 7 idiomas.",
        ],
        "hasnt_h2": "Lo que (todavía) no tiene",
        "hasnt": "Ski Info se centra en las estaciones de esquí: no tiene rutas de travesía ni de fuera pista, ni mapas para usar sin conexión, "
                 "y no hay app para iPhone (la web se puede añadir a la pantalla de inicio y funciona como una app).",
        "try_h2": "Pruébalo en 3D",
        "try_note": "Toca una estación para abrir su mapa en 3D. Las demás, en el buscador de la portada.",
        "open3d": "Ver en 3D", "page": "Ficha",
        "faq_h2": "Preguntas frecuentes",
        "faq": [
            ("¿FatMap ha cerrado?",
             "Sí. Strava compró FatMap en enero de 2023 y la cerró el 1 de octubre de 2024; parte de sus funciones pasaron a Strava."),
            ("¿Hay una alternativa gratuita a FatMap para esquiar?",
             "Ski Info (skiinfoapp.com) es gratuita y no pide registro: mapa 3D con relieve, pistas y remontes de {n} estaciones de esquí, "
             "y la pendiente de cada pista."),
            ("¿Dónde puedo ver la pendiente de una pista de esquí?",
             "En la ficha de cada estación de Ski Info: cada pista tiene su perfil de pendiente tramo a tramo, en % y en grados, y su tramo más empinado de 50 m."),
        ],
        "cta": "Abrir Ski Info",
    },
    "en": {
        "title": "FatMap alternative: free 3D ski piste maps",
        "h1": "A FatMap alternative for 3D ski maps",
        "lead": "FatMap, the 3D mountain map many skiers relied on, shut down on 1 October 2024, after Strava bought it. "
                "Ski Info is a free alternative for ski resorts: 3D terrain with every run and lift of {n} resorts in {c} countries, "
                "plus the real slope of every run, stretch by stretch.",
        "has_h2": "What Ski Info has",
        "has": [
            "<b>3D terrain map</b> of every resort: named runs and lifts, to rotate, tilt and fly around the mountain.",
            "<b>Real slope of every run</b>: its gradient profile stretch by stretch, in % and degrees, coloured with the ATUDEM/AFNOR thresholds, and its steepest stretch.",
            "<b>Map coloured by slope</b>, not just by official difficulty: see which blacks are mellow and which reds are tough.",
            "<b>{n} resorts in {c} countries</b>: the Alps, the Pyrenees, North America, Scandinavia, Japan, the Andes…",
            "<b>7-day snow forecast</b> for every resort.",
            "<b>Routes around the resort</b> (beta): how to get from one run to another, for example avoiding black runs.",
            "<b>Free, no sign-up</b>, on the web and Android, in 7 languages.",
        ],
        "hasnt_h2": "What it doesn't have (yet)",
        "hasnt": "Ski Info is about ski resorts: no ski touring or backcountry routes, no offline maps, and no iPhone app "
                 "(the website can be added to the home screen and works like an app).",
        "try_h2": "Try it in 3D",
        "try_note": "Tap a resort to open its 3D map. Every other one is in the search on the home page.",
        "open3d": "View in 3D", "page": "Resort page",
        "faq_h2": "FAQ",
        "faq": [
            ("Has FatMap shut down?",
             "Yes. Strava bought FatMap in January 2023 and shut it down on 1 October 2024; some of its features moved to Strava."),
            ("Is there a free FatMap alternative for skiing?",
             "Ski Info (skiinfoapp.com) is free with no sign-up: a 3D terrain map with the runs and lifts of {n} ski resorts, "
             "and the slope of every run."),
            ("Where can I see how steep a ski run is?",
             "On each resort's page on Ski Info: every run has its gradient profile stretch by stretch, in % and degrees, and its steepest 50 m stretch."),
        ],
        "cta": "Open Ski Info",
    },
    "fr": {
        "title": "Alternative à FatMap : cartes des pistes de ski en 3D, gratuites",
        "h1": "Une alternative à FatMap pour voir les pistes de ski en 3D",
        "lead": "FatMap, la carte 3D de montagne qu'utilisaient beaucoup de skieurs, a fermé le 1er octobre 2024, après son rachat par Strava. "
                "Ski Info est une alternative gratuite pour les stations de ski : le relief en 3D avec toutes les pistes et remontées "
                "de {n} stations dans {c} pays et, en plus, la pente réelle de chaque piste, tronçon par tronçon.",
        "has_h2": "Ce que propose Ski Info",
        "has": [
            "<b>Carte 3D avec relief</b> de chaque station : pistes et remontées avec leur nom, à faire pivoter, incliner et survoler.",
            "<b>Pente réelle de chaque piste</b> : son profil tronçon par tronçon, en % et en degrés, avec les seuils AFNOR/ATUDEM, et son tronçon le plus raide.",
            "<b>Carte colorée selon la pente</b>, pas seulement selon la difficulté officielle : quelles noires sont douces et quelles rouges sont dures.",
            "<b>{n} stations dans {c} pays</b> : Alpes, Pyrénées, Amérique du Nord, Scandinavie, Japon, Andes…",
            "<b>Prévisions de neige à 7 jours</b> pour chaque station.",
            "<b>Itinéraires dans la station</b> (bêta) : comment aller d'une piste à une autre, par exemple sans passer par les noires.",
            "<b>Gratuit et sans inscription</b>, sur le web et Android, en 7 langues.",
        ],
        "hasnt_h2": "Ce qu'il n'a pas (encore)",
        "hasnt": "Ski Info se concentre sur les stations de ski : pas d'itinéraires de ski de randonnée ni de hors-piste, pas de cartes hors connexion, "
                 "et pas d'app iPhone (le site peut être ajouté à l'écran d'accueil et fonctionne comme une app).",
        "try_h2": "Essayez en 3D",
        "try_note": "Touchez une station pour ouvrir sa carte en 3D. Toutes les autres sont dans la recherche de la page d'accueil.",
        "open3d": "Voir en 3D", "page": "Fiche",
        "faq_h2": "Questions fréquentes",
        "faq": [
            ("FatMap a-t-il fermé ?",
             "Oui. Strava a racheté FatMap en janvier 2023 et l'a fermé le 1er octobre 2024 ; une partie de ses fonctions est passée sur Strava."),
            ("Existe-t-il une alternative gratuite à FatMap pour le ski ?",
             "Ski Info (skiinfoapp.com) est gratuit et sans inscription : carte 3D avec relief, pistes et remontées de {n} stations de ski, "
             "et la pente de chaque piste."),
            ("Où voir la pente d'une piste de ski ?",
             "Sur la fiche de chaque station dans Ski Info : chaque piste a son profil de pente tronçon par tronçon, en % et en degrés, et son tronçon de 50 m le plus raide."),
        ],
        "cta": "Ouvrir Ski Info",
    },
    "de": {
        "title": "FatMap-Alternative: kostenlose 3D-Pistenpläne",
        "h1": "Eine FatMap-Alternative für Pisten in 3D",
        "lead": "FatMap, die 3D-Bergkarte vieler Skifahrer, wurde am 1. Oktober 2024 eingestellt, nachdem Strava sie gekauft hatte. "
                "Ski Info ist eine kostenlose Alternative für Skigebiete: das Gelände in 3D mit allen Pisten und Liften "
                "von {n} Skigebieten in {c} Ländern – und dazu das echte Gefälle jeder Piste, Abschnitt für Abschnitt.",
        "has_h2": "Was Ski Info bietet",
        "has": [
            "<b>3D-Karte mit Relief</b> für jedes Skigebiet: Pisten und Lifte mit Namen, zum Drehen, Neigen und Umrunden.",
            "<b>Echtes Gefälle jeder Piste</b>: ihr Profil Abschnitt für Abschnitt in % und Grad, eingefärbt nach den ATUDEM/AFNOR-Schwellen, und ihr steilster Abschnitt.",
            "<b>Karte nach Gefälle eingefärbt</b>, nicht nur nach offizieller Schwierigkeit: Welche Schwarzen sind sanft, welche Roten hart?",
            "<b>{n} Skigebiete in {c} Ländern</b>: Alpen, Pyrenäen, Nordamerika, Skandinavien, Japan, Anden…",
            "<b>7-Tage-Schneeprognose</b> für jedes Skigebiet.",
            "<b>Routen im Skigebiet</b> (Beta): wie man von einer Piste zur anderen kommt, zum Beispiel ohne schwarze Pisten.",
            "<b>Kostenlos und ohne Anmeldung</b>, im Web und auf Android, in 7 Sprachen.",
        ],
        "hasnt_h2": "Was es (noch) nicht gibt",
        "hasnt": "Ski Info konzentriert sich auf Skigebiete: keine Skitouren- oder Freeride-Routen, keine Offline-Karten "
                 "und keine iPhone-App (die Website lässt sich zum Home-Bildschirm hinzufügen und funktioniert wie eine App).",
        "try_h2": "In 3D ausprobieren",
        "try_note": "Tippe auf ein Skigebiet, um seine 3D-Karte zu öffnen. Alle anderen findest du über die Suche auf der Startseite.",
        "open3d": "In 3D ansehen", "page": "Skigebiet",
        "faq_h2": "Häufige Fragen",
        "faq": [
            ("Wurde FatMap eingestellt?",
             "Ja. Strava hat FatMap im Januar 2023 gekauft und am 1. Oktober 2024 eingestellt; einige Funktionen gingen in Strava über."),
            ("Gibt es eine kostenlose FatMap-Alternative zum Skifahren?",
             "Ski Info (skiinfoapp.com) ist kostenlos und ohne Anmeldung: eine 3D-Karte mit Relief, den Pisten und Liften von {n} Skigebieten "
             "und dem Gefälle jeder Piste."),
            ("Wo sehe ich, wie steil eine Piste ist?",
             "Auf der Seite jedes Skigebiets bei Ski Info: Jede Piste hat ihr Gefälleprofil Abschnitt für Abschnitt, in % und Grad, und ihren steilsten 50-m-Abschnitt."),
        ],
        "cta": "Ski Info öffnen",
    },
    "it": {
        "title": "Alternativa a FatMap: mappe 3D delle piste da sci, gratis",
        "h1": "Un'alternativa a FatMap per vedere le piste da sci in 3D",
        "lead": "FatMap, la mappa 3D di montagna usata da molti sciatori, ha chiuso il 1° ottobre 2024, dopo l'acquisto da parte di Strava. "
                "Ski Info è un'alternativa gratuita per le stazioni sciistiche: il rilievo in 3D con tutte le piste e gli impianti "
                "di {n} stazioni in {c} paesi e, in più, la pendenza reale di ogni pista, tratto per tratto.",
        "has_h2": "Cosa offre Ski Info",
        "has": [
            "<b>Mappa 3D con rilievo</b> di ogni stazione: piste e impianti con il loro nome, da ruotare, inclinare e sorvolare.",
            "<b>Pendenza reale di ogni pista</b>: il suo profilo tratto per tratto, in % e in gradi, con le soglie ATUDEM/AFNOR, e il suo tratto più ripido.",
            "<b>Mappa colorata per pendenza</b>, non solo per difficoltà ufficiale: quali nere sono facili e quali rosse sono dure.",
            "<b>{n} stazioni in {c} paesi</b>: Alpi, Pirenei, Nord America, Scandinavia, Giappone, Ande…",
            "<b>Previsioni di neve a 7 giorni</b> per ogni stazione.",
            "<b>Percorsi nella stazione</b> (beta): come andare da una pista all'altra, per esempio evitando le nere.",
            "<b>Gratis e senza registrazione</b>, sul web e su Android, in 7 lingue.",
        ],
        "hasnt_h2": "Cosa non ha (ancora)",
        "hasnt": "Ski Info si concentra sulle stazioni sciistiche: niente itinerari di scialpinismo o fuoripista, niente mappe offline "
                 "e nessuna app per iPhone (il sito si può aggiungere alla schermata Home e funziona come un'app).",
        "try_h2": "Provalo in 3D",
        "try_note": "Tocca una stazione per aprire la sua mappa in 3D. Tutte le altre sono nella ricerca della home page.",
        "open3d": "Vedi in 3D", "page": "Scheda",
        "faq_h2": "Domande frequenti",
        "faq": [
            ("FatMap ha chiuso?",
             "Sì. Strava ha acquistato FatMap a gennaio 2023 e l'ha chiusa il 1° ottobre 2024; parte delle sue funzioni è passata a Strava."),
            ("Esiste un'alternativa gratuita a FatMap per sciare?",
             "Ski Info (skiinfoapp.com) è gratuita e senza registrazione: mappa 3D con rilievo, piste e impianti di {n} stazioni sciistiche "
             "e la pendenza di ogni pista."),
            ("Dove posso vedere la pendenza di una pista da sci?",
             "Nella scheda di ogni stazione su Ski Info: ogni pista ha il suo profilo di pendenza tratto per tratto, in % e in gradi, e il suo tratto di 50 m più ripido."),
        ],
        "cta": "Apri Ski Info",
    },
    "nl": {
        "title": "FatMap-alternatief: gratis 3D-pistekaarten",
        "h1": "Een FatMap-alternatief om skipistes in 3D te bekijken",
        "lead": "FatMap, de 3D-bergkaart die veel skiërs gebruikten, is op 1 oktober 2024 gestopt, nadat Strava het had gekocht. "
                "Ski Info is een gratis alternatief voor skigebieden: het terrein in 3D met alle pistes en liften "
                "van {n} skigebieden in {c} landen, plus de echte helling van elke piste, stuk voor stuk.",
        "has_h2": "Wat Ski Info heeft",
        "has": [
            "<b>3D-kaart met reliëf</b> van elk skigebied: pistes en liften met hun naam, om te draaien, te kantelen en rond de berg te vliegen.",
            "<b>Echte helling van elke piste</b>: het profiel stuk voor stuk, in % en graden, gekleurd volgens de ATUDEM/AFNOR-grenzen, en het steilste stuk.",
            "<b>Kaart gekleurd op helling</b>, niet alleen op officiële moeilijkheid: welke zwarte pistes meevallen en welke rode zwaar zijn.",
            "<b>{n} skigebieden in {c} landen</b>: de Alpen, de Pyreneeën, Noord-Amerika, Scandinavië, Japan, de Andes…",
            "<b>Sneeuwverwachting voor 7 dagen</b> voor elk skigebied.",
            "<b>Routes door het skigebied</b> (bèta): hoe je van de ene piste naar de andere komt, bijvoorbeeld zonder zwarte pistes.",
            "<b>Gratis en zonder account</b>, op het web en Android, in 7 talen.",
        ],
        "hasnt_h2": "Wat het (nog) niet heeft",
        "hasnt": "Ski Info draait om skigebieden: geen toer- of offpisteroutes, geen offline kaarten "
                 "en geen iPhone-app (de website kun je aan je beginscherm toevoegen en werkt dan als een app).",
        "try_h2": "Probeer het in 3D",
        "try_note": "Tik op een skigebied om de 3D-kaart te openen. Alle andere vind je via de zoekfunctie op de startpagina.",
        "open3d": "Bekijk in 3D", "page": "Skigebied",
        "faq_h2": "Veelgestelde vragen",
        "faq": [
            ("Is FatMap gestopt?",
             "Ja. Strava kocht FatMap in januari 2023 en stopte ermee op 1 oktober 2024; een deel van de functies ging naar Strava."),
            ("Is er een gratis FatMap-alternatief om te skiën?",
             "Ski Info (skiinfoapp.com) is gratis en zonder account: een 3D-kaart met reliëf, de pistes en liften van {n} skigebieden "
             "en de helling van elke piste."),
            ("Waar zie ik hoe steil een skipiste is?",
             "Op de pagina van elk skigebied in Ski Info: elke piste heeft een hellingsprofiel stuk voor stuk, in % en graden, en het steilste stuk van 50 m."),
        ],
        "cta": "Ski Info openen",
    },
    "pl": {
        "title": "Alternatywa dla FatMap: darmowe mapy tras narciarskich 3D",
        "h1": "Alternatywa dla FatMap: trasy narciarskie w 3D",
        "lead": "FatMap, trójwymiarowa mapa gór, z której korzystało wielu narciarzy, została zamknięta 1 października 2024 r., po przejęciu przez Stravę. "
                "Ski Info to darmowa alternatywa dla ośrodków narciarskich: teren w 3D ze wszystkimi trasami i wyciągami "
                "(ośrodki: {n}, kraje: {c}), a do tego rzeczywiste nachylenie każdej trasy, odcinek po odcinku.",
        "has_h2": "Co oferuje Ski Info",
        "has": [
            "<b>Mapa 3D z rzeźbą terenu</b> każdego ośrodka: trasy i wyciągi z nazwami, do obracania, pochylania i oblatywania góry.",
            "<b>Rzeczywiste nachylenie każdej trasy</b>: profil odcinek po odcinku, w % i stopniach, w kolorach według progów ATUDEM/AFNOR, oraz najbardziej stromy odcinek.",
            "<b>Mapa kolorowana według nachylenia</b>, nie tylko według oficjalnej trudności: które czarne są łagodne, a które czerwone trudne.",
            "<b>Ośrodki w {c} krajach ({n})</b>: Alpy, Pireneje, Ameryka Północna, Skandynawia, Japonia, Andy…",
            "<b>Prognoza śniegu na 7 dni</b> dla każdego ośrodka.",
            "<b>Trasy po ośrodku</b> (beta): jak dostać się z jednej trasy na inną, np. omijając czarne.",
            "<b>Za darmo i bez rejestracji</b>, w przeglądarce i na Androidzie, w 7 językach.",
        ],
        "hasnt_h2": "Czego (jeszcze) nie ma",
        "hasnt": "Ski Info skupia się na ośrodkach narciarskich: nie ma tras skiturowych ani pozatrasowych, map offline "
                 "ani aplikacji na iPhone'a (stronę można dodać do ekranu głównego i działa jak aplikacja).",
        "try_h2": "Wypróbuj w 3D",
        "try_note": "Dotknij ośrodka, aby otworzyć jego mapę 3D. Wszystkie pozostałe znajdziesz w wyszukiwarce na stronie głównej.",
        "open3d": "Zobacz w 3D", "page": "Ośrodek",
        "faq_h2": "Najczęstsze pytania",
        "faq": [
            ("Czy FatMap został zamknięty?",
             "Tak. Strava kupiła FatMap w styczniu 2023 r. i zamknęła go 1 października 2024 r.; część funkcji przeniesiono do Stravy."),
            ("Czy jest darmowa alternatywa dla FatMap do narciarstwa?",
             "Ski Info (skiinfoapp.com) jest darmowe i nie wymaga rejestracji: mapa 3D z rzeźbą terenu, trasami i wyciągami ośrodków narciarskich ({n}) "
             "oraz nachyleniem każdej trasy."),
            ("Gdzie sprawdzić nachylenie trasy narciarskiej?",
             "Na stronie każdego ośrodka w Ski Info: każda trasa ma profil nachylenia odcinek po odcinku, w % i stopniach, oraz najbardziej stromy odcinek 50 m."),
        ],
        "cta": "Otwórz Ski Info",
    },
}


def url_for(base_url: str, guides_path: str, lang: str) -> str:
    return f"{base_url}{guides_path}{SLUG[lang]}/"


def render(lang: str, *, page, e, base_url: str, loc: dict, guides_path: str, n: str, c: str,
           featured: list[tuple[str, str, str]], alternates: dict) -> str:
    """featured: [(station id, display name, slug)]."""
    t = TX[lang]
    fill = lambda s: s.format(n=n, c=c)
    url = url_for(base_url, guides_path, lang)
    has = "".join(f"<li>{fill(x)}</li>" for x in t["has"])
    cards = "".join(
        f'<div class="item"><span class="dot" style="background:var(--accent)"></span><div class="item-main">'
        f'<div class="item-name">{e(name)}</div><div class="item-meta">'
        f'<a href="{loc["home"]}?estacion={sid}&amp;vista=3d">{e(t["open3d"])} ›</a> · '
        f'<a href="{loc["station"]}{slug}/">{e(t["page"])}</a></div></div></div>'
        for sid, name, slug in featured)
    faq = "".join(f"<h3>{e(q)}</h3><p class=\"intro\">{e(fill(a))}</p>" for q, a in t["faq"])
    body = f"""<div class="topbar"><a class="back-btn" href="{guides_path}"><span class="chev">‹</span> {e(PAGE_GUIDES[lang])}</a><a class="back-btn" href="{loc['home']}">Ski Info</a></div>
<div class="guide-head">
<div class="eyebrow"><a href="{loc['home']}">Ski Info</a> · <a href="{guides_path}">{e(PAGE_GUIDES[lang])}</a></div>
<h1>{e(t['h1'])}</h1>
<p class="list-sub">{e(fill(t['lead']))}</p>
</div>
<div class="guide-wrap">
<section><div class="section-head"><h2>{e(t['has_h2'])}</h2></div><ul class="intro fatmap-list">{has}</ul></section>
<section><div class="section-head"><h2>{e(t['try_h2'])}</h2></div><p class="intro">{e(t['try_note'])}</p><div class="list-scroll">{cards}</div>
<a class="cta-block" href="{loc['home']}">{e(t['cta'])}</a></section>
<section><div class="section-head"><h2>{e(t['hasnt_h2'])}</h2></div><p class="intro">{e(t['hasnt'])}</p></section>
<section class="guide-method"><h2>{e(t['faq_h2'])}</h2>{faq}</section>
</div>"""
    jsonld = {"@context": "https://schema.org", "@type": "FAQPage", "inLanguage": lang, "url": url,
              "mainEntity": [{"@type": "Question", "name": q,
                              "acceptedAnswer": {"@type": "Answer", "text": fill(a)}} for q, a in t["faq"]]}
    return page(title=f"{t['title']} | Ski Info", description=fill(t["lead"])[:300], url=url, body=body,
                jsonld=jsonld, base_url=base_url, lang=lang, alternates=alternates)


PAGE_GUIDES = {"es": "Guías", "en": "Guides", "fr": "Guides", "de": "Ratgeber", "it": "Guide", "nl": "Gidsen", "pl": "Poradniki"}
