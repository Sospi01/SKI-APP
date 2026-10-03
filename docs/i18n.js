// Language helper shared by every page. Spanish is the source language: T()
// returns its (Spanish) argument unless a dictionary is loaded (docs/i18n/en.js,
// fr.js, de.js or it.js, on the pages of that language). "{0}", "{1}"... are replaced by the
// extra arguments, so translations can reorder the parts of a sentence.
var SKI_LANG = (document.documentElement.getAttribute('lang') || 'es').slice(0, 2);
var SKI_LOCALE = { en: 'en-GB', fr: 'fr-FR', de: 'de-DE', it: 'it-IT' }[SKI_LANG] || 'es-ES';
function T(s) {
  var dict = window.SKI_I18N && window.SKI_I18N.ui;
  var out = (dict && dict[s]) || s;
  for (var i = 1; i < arguments.length; i++) out = out.split('{' + (i - 1) + '}').join(String(arguments[i]));
  return out;
}
// Replace the labels of a lookup table in place from SKI_I18N.tables[name].
function localizeTable(table, name, field) {
  var tr = window.SKI_I18N && window.SKI_I18N.tables && window.SKI_I18N.tables[name];
  if (!tr) return;
  Object.keys(table).forEach(function (k) {
    if (tr[k] == null) return;
    if (field) table[k][field] = tr[k]; else table[k] = tr[k];
  });
}
