// The site's languages, for every page (the app and the generated ones):
// remembers an explicit choice made with a language link (the Spanish home's
// "lang-redirect" script follows it), and when the browser speaks one of the
// other languages offers that version of the page in a small bar -- never an
// automatic redirect. A page's versions are its <link rel="alternate" hreflang>.
(function () {
  var LANGS = {
    es: { hint: 'Esta página también está en español.', cta: 'Ver en español', close: 'Cerrar' },
    en: { hint: 'This page is also available in English.', cta: 'View in English', close: 'Close' },
    fr: { hint: 'Cette page existe aussi en français.', cta: 'Voir en français', close: 'Fermer' },
    de: { hint: 'Diese Seite gibt es auch auf Deutsch.', cta: 'Auf Deutsch ansehen', close: 'Schließen' },
    it: { hint: 'Questa pagina è disponibile anche in italiano.', cta: 'Vedi in italiano', close: 'Chiudi' }
  };
  var HOMES = ['/', '/en/', '/fr/', '/de/', '/it/'];

  document.addEventListener('click', function (ev) {
    var a = ev.target.closest && ev.target.closest('.lang-link');
    if (!a || !a.getAttribute('data-lang')) return;
    try { localStorage.setItem('si_lang', a.getAttribute('data-lang')); } catch (e) {}
  });

  var page = (document.documentElement.getAttribute('lang') || 'es').slice(0, 2);
  // Catalan, Galician and Basque readers get Spanish; any other language, English.
  var reader = (navigator.language || '').slice(0, 2).toLowerCase();
  if (/^(ca|gl|eu)$/.test(reader)) reader = 'es';
  if (!LANGS[reader]) reader = 'en';
  if (reader === page) return;
  try { if (localStorage.getItem('si_lang_hint') || localStorage.getItem('si_lang')) return; } catch (e) { return; }

  var alt = document.querySelector('link[rel="alternate"][hreflang="' + reader + '"]');
  if (!alt) return;
  var href = alt.getAttribute('href').replace(/^https?:\/\/[^/]+/, '');  // same-site link
  // The app's homes carry the open station/view in the query string.
  if (HOMES.indexOf(href) !== -1) href += location.search;

  function show() {
    var tx = LANGS[reader];
    var bar = document.createElement('div');
    bar.className = 'lang-hint';
    bar.setAttribute('lang', reader);
    bar.innerHTML = '<span></span><a class="lang-link"></a><button type="button">×</button>';
    bar.querySelector('span').textContent = tx.hint;
    var link = bar.querySelector('a');
    link.textContent = tx.cta;
    link.href = href;
    link.setAttribute('data-lang', reader);
    link.setAttribute('hreflang', reader);
    var close = bar.querySelector('button');
    close.setAttribute('aria-label', tx.close);
    close.addEventListener('click', function () {
      bar.remove();
      try { localStorage.setItem('si_lang_hint', '1'); } catch (e) {}
    });
    document.body.appendChild(bar);
  }
  if (document.body) show(); else document.addEventListener('DOMContentLoaded', show);
})();
