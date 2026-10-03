// The language picker the app puts in its headers: a flag button that opens
// the five languages. hrefFor(lang) gives where each one leads (worked out
// when the menu opens, so it follows the station on screen); picking one is
// remembered like any other language link (below).
var SKI_LANG_CHOICES = [['es', 'es', 'Español'], ['en', 'gb', 'English'], ['fr', 'fr', 'Français'],
  ['de', 'de', 'Deutsch'], ['it', 'it', 'Italiano']];
function mountLangPicker(container, hrefFor, className) {
  var page = (document.documentElement.getAttribute('lang') || 'es').slice(0, 2);
  var cur = SKI_LANG_CHOICES.filter(function (c) { return c[0] === page; })[0] || SKI_LANG_CHOICES[0];
  var flag = function (cc) { return '<img src="/flags/' + cc + '.svg" alt="" width="20" height="15">'; };
  var wrap = document.createElement('div');
  wrap.className = 'lang-picker' + (className ? ' ' + className : '');
  var btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'lang-picker-btn';
  btn.setAttribute('aria-haspopup', 'true');
  btn.setAttribute('aria-expanded', 'false');
  btn.setAttribute('aria-label', cur[2]);
  btn.innerHTML = flag(cur[1]) + '<span>' + cur[0].toUpperCase() + '</span>'
    + '<svg viewBox="0 0 10 10" aria-hidden="true"><path d="M2 3.5l3 3 3-3" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  var menu = document.createElement('div');
  menu.className = 'lang-picker-menu';
  menu.hidden = true;
  SKI_LANG_CHOICES.forEach(function (c) {
    var a = document.createElement('a');
    a.className = 'lang-picker-item lang-link';
    a.setAttribute('data-lang', c[0]);
    a.setAttribute('hreflang', c[0]);
    a.setAttribute('lang', c[0]);
    if (c[0] === page) a.setAttribute('aria-current', 'true');
    a.innerHTML = flag(c[1]) + '<span></span>';
    a.querySelector('span').textContent = c[2];
    a.href = hrefFor(c[0]);
    a.addEventListener('click', function (ev) { if (c[0] === page) { ev.preventDefault(); close(); } });
    menu.appendChild(a);
  });
  function open() {
    Array.prototype.forEach.call(menu.children, function (a) { a.href = hrefFor(a.getAttribute('data-lang')); });
    menu.hidden = false;
    btn.setAttribute('aria-expanded', 'true');
  }
  function close() {
    menu.hidden = true;
    btn.setAttribute('aria-expanded', 'false');
  }
  btn.addEventListener('click', function () { if (menu.hidden) open(); else close(); });
  document.addEventListener('click', function (ev) { if (!wrap.contains(ev.target)) close(); });
  document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape') close(); });
  wrap.appendChild(btn);
  wrap.appendChild(menu);
  container.appendChild(wrap);
  return wrap;
}

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
