// "Send us your comments": a small form that reaches the owner by email, via
// Web3Forms (the site has no server of its own). Used by the app (index.html:
// the route panel, "About this data", the footer) and the generated pages
// (station pages, footers): any element with data-feedback opens it, and gets
// its link text from here if it has none. Texts in the 7 languages live here
// too, so the generated pages need nothing else.
//   SkiFeedback.open({ kind: 'route' | 'data' | 'general', context: 'free text' })
// The access key isn't secret: Web3Forms keys are made to sit in web pages,
// and the address the messages go to stays on their side.
(function () {
  var KEY = 'd3b9863e-4a47-4477-8ea9-c32902231d0d';
  var ENDPOINT = 'https://api.web3forms.com/submit';
  var MAX = 2000;
  var TX = {
    es: { link: 'Enviar sugerencias', data: 'Avisar de un error en los datos', route: '¿Algo raro en esta ruta? Cuéntanoslo',
      title: 'Cuéntanos', intro: 'Ideas, errores en el mapa, una ruta rara… Lo leemos todo.',
      introRoute: '¿Qué ha fallado en esta ruta? Dinos qué esperabas y qué te ha salido.',
      introData: '¿Qué está mal? Una pista mal dibujada, un remonte que ya no existe, un nombre…',
      msg: 'Tu mensaje', email: 'Tu correo (opcional, por si quieres respuesta)',
      note: 'Solo usaremos tu correo para contestarte.', send: 'Enviar', cancel: 'Cancelar', close: 'Cerrar',
      sending: 'Enviando…', ok: '¡Gracias! Lo hemos recibido.', err: 'No se pudo enviar. Inténtalo de nuevo en un rato.',
      empty: 'Escribe algo antes de enviar.', badEmail: 'Ese correo no parece válido.' },
    en: { link: 'Send feedback', data: 'Report a data error', route: 'Something odd about this route? Tell us',
      title: 'Tell us', intro: 'Ideas, mistakes on the map, an odd route… We read everything.',
      introRoute: 'What went wrong with this route? Tell us what you expected and what you got.',
      introData: 'What is wrong? A run drawn badly, a lift that no longer exists, a name…',
      msg: 'Your message', email: 'Your email (optional, if you want a reply)',
      note: 'We will only use your email to reply to you.', send: 'Send', cancel: 'Cancel', close: 'Close',
      sending: 'Sending…', ok: 'Thank you! We got it.', err: 'It could not be sent. Please try again in a while.',
      empty: 'Write something before sending.', badEmail: 'That email does not look right.' },
    fr: { link: 'Envoyer une suggestion', data: 'Signaler une erreur dans les données', route: 'Un souci avec cet itinéraire ? Dites-le-nous',
      title: 'Dites-nous', intro: 'Idées, erreurs sur la carte, un itinéraire bizarre… Nous lisons tout.',
      introRoute: "Qu'est-ce qui n'allait pas dans cet itinéraire ? Dites-nous ce que vous attendiez et ce que vous avez obtenu.",
      introData: "Qu'est-ce qui ne va pas ? Une piste mal tracée, une remontée qui n'existe plus, un nom…",
      msg: 'Votre message', email: 'Votre e-mail (facultatif, si vous voulez une réponse)',
      note: 'Nous utiliserons votre e-mail uniquement pour vous répondre.', send: 'Envoyer', cancel: 'Annuler', close: 'Fermer',
      sending: 'Envoi…', ok: "Merci ! C'est bien reçu.", err: "L'envoi a échoué. Réessayez dans un moment.",
      empty: "Écrivez quelque chose avant d'envoyer.", badEmail: 'Cet e-mail ne semble pas valide.' },
    de: { link: 'Feedback senden', data: 'Fehler in den Daten melden', route: 'Stimmt etwas mit dieser Route nicht? Sag es uns',
      title: 'Schreib uns', intro: 'Ideen, Fehler auf der Karte, eine seltsame Route… Wir lesen alles.',
      introRoute: 'Was war an dieser Route falsch? Schreib uns, was du erwartet hast und was herauskam.',
      introData: 'Was stimmt nicht? Eine falsch eingezeichnete Piste, ein Lift, den es nicht mehr gibt, ein Name…',
      msg: 'Deine Nachricht', email: 'Deine E-Mail (optional, falls du eine Antwort möchtest)',
      note: 'Wir nutzen deine E-Mail nur, um dir zu antworten.', send: 'Senden', cancel: 'Abbrechen', close: 'Schließen',
      sending: 'Wird gesendet…', ok: 'Danke! Ist angekommen.', err: 'Senden fehlgeschlagen. Bitte versuch es später noch einmal.',
      empty: 'Schreib etwas, bevor du sendest.', badEmail: 'Diese E-Mail sieht nicht richtig aus.' },
    it: { link: 'Invia un suggerimento', data: 'Segnala un errore nei dati', route: 'Qualcosa non va in questo percorso? Diccelo',
      title: 'Scrivici', intro: 'Idee, errori sulla mappa, un percorso strano… Leggiamo tutto.',
      introRoute: "Cosa non andava in questo percorso? Dicci cosa ti aspettavi e cosa è uscito.",
      introData: 'Cosa non va? Una pista disegnata male, un impianto che non esiste più, un nome…',
      msg: 'Il tuo messaggio', email: 'La tua email (facoltativa, se vuoi una risposta)',
      note: 'Useremo la tua email solo per risponderti.', send: 'Invia', cancel: 'Annulla', close: 'Chiudi',
      sending: 'Invio…', ok: "Grazie! L'abbiamo ricevuto.", err: 'Invio non riuscito. Riprova tra un po’.',
      empty: "Scrivi qualcosa prima dell'invio.", badEmail: 'Questa email non sembra valida.' },
    nl: { link: 'Feedback sturen', data: 'Fout in de gegevens melden', route: 'Klopt er iets niet aan deze route? Laat het weten',
      title: 'Laat het ons weten', intro: 'Ideeën, fouten op de kaart, een vreemde route… We lezen alles.',
      introRoute: 'Wat ging er mis met deze route? Vertel wat je verwachtte en wat je kreeg.',
      introData: 'Wat klopt er niet? Een verkeerd getekende piste, een lift die niet meer bestaat, een naam…',
      msg: 'Je bericht', email: 'Je e-mail (optioneel, als je antwoord wilt)',
      note: 'We gebruiken je e-mail alleen om je te antwoorden.', send: 'Versturen', cancel: 'Annuleren', close: 'Sluiten',
      sending: 'Versturen…', ok: 'Bedankt! We hebben het ontvangen.', err: 'Versturen is mislukt. Probeer het straks opnieuw.',
      empty: 'Schrijf iets voordat je verstuurt.', badEmail: 'Dat e-mailadres lijkt niet te kloppen.' },
    pl: { link: 'Wyślij opinię', data: 'Zgłoś błąd w danych', route: 'Coś nie tak z tą trasą? Napisz nam',
      title: 'Napisz do nas', intro: 'Pomysły, błędy na mapie, dziwna trasa… Czytamy wszystko.',
      introRoute: 'Co było nie tak z tą trasą? Napisz, czego się spodziewałeś, a co wyszło.',
      introData: 'Co jest nie tak? Źle narysowana trasa, wyciąg, którego już nie ma, nazwa…',
      msg: 'Twoja wiadomość', email: 'Twój e-mail (opcjonalnie, jeśli chcesz odpowiedzi)',
      note: 'Użyjemy Twojego e-maila tylko po to, by Ci odpowiedzieć.', send: 'Wyślij', cancel: 'Anuluj', close: 'Zamknij',
      sending: 'Wysyłanie…', ok: 'Dziękujemy! Otrzymaliśmy wiadomość.', err: 'Nie udało się wysłać. Spróbuj ponownie za chwilę.',
      empty: 'Napisz coś przed wysłaniem.', badEmail: 'Ten e-mail nie wygląda na poprawny.' }
  };
  function lang() {
    var l = (window.SKI_LANG || document.documentElement.lang || 'es').slice(0, 2).toLowerCase();
    return TX[l] ? l : 'en';
  }
  function t(k) { return TX[lang()][k]; }
  function platform() { return /; wv\)/.test(navigator.userAgent) ? 'app Android' : 'web'; }

  var CSS = '.fb-back{position:fixed;inset:0;z-index:10000;background:rgba(10,20,35,.55);display:flex;align-items:center;justify-content:center;padding:16px}' +
    '.fb-box{background:var(--surface,var(--bg,#fff));color:var(--text-primary,#16202b);border-radius:14px;max-width:440px;width:100%;padding:20px 20px 16px;box-shadow:0 12px 40px rgba(0,0,0,.3);font:15px/1.45 "IBM Plex Sans",system-ui,sans-serif;max-height:calc(100vh - 32px);overflow:auto}' +
    '.fb-box h2{font:700 22px/1.2 "Barlow Condensed",sans-serif;margin:0 0 6px}' +
    '.fb-box p{margin:0 0 12px;color:var(--text-secondary,#4a5866);font-size:14px}' +
    '.fb-box label{display:block;font-size:13px;font-weight:600;margin:10px 0 4px;color:var(--text-secondary,#4a5866)}' +
    '.fb-box textarea,.fb-box input[type=email]{width:100%;box-sizing:border-box;border:1px solid var(--border,#d5dbe1);border-radius:8px;padding:9px 10px;font:inherit;color:inherit;background:var(--page,var(--bg,#fff))}' +
    '.fb-box textarea{min-height:110px;resize:vertical}' +
    '.fb-box .fb-note{font-size:12px;margin:4px 0 0;color:var(--text-muted,#6b7785)}' +
    '.fb-box .fb-trap{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden}' +
    '.fb-row{display:flex;gap:8px;justify-content:flex-end;margin-top:14px}' +
    '.fb-row button{border:0;border-radius:999px;padding:9px 18px;font:600 14px/1 "IBM Plex Sans",system-ui,sans-serif;cursor:pointer}' +
    '.fb-send{background:var(--accent,#1f6feb);color:#fff}.fb-send[disabled]{opacity:.6;cursor:default}' +
    '.fb-cancel{background:transparent;color:var(--text-secondary,#4a5866)}' +
    '.fb-status{min-height:1.2em;font-size:13px;margin-top:10px}.fb-status.err{color:#c62828}' +
    '.fb-done{text-align:center;padding:18px 0 6px;font-size:16px}' +
    'a.fb-link,button.fb-link{cursor:pointer}' +
    'button.fb-link{background:none;border:0;padding:0;font:inherit;color:var(--accent,#1f6feb);text-decoration:underline}';
  var styled = false;
  function style() {
    if (styled) return;
    styled = true;
    var s = document.createElement('style'); s.textContent = CSS; document.head.appendChild(s);
  }

  function open(opts) {
    opts = opts || {};
    style();
    var kind = opts.kind || 'general';
    var back = document.createElement('div'); back.className = 'fb-back';
    var box = document.createElement('div'); box.className = 'fb-box';
    box.setAttribute('role', 'dialog'); box.setAttribute('aria-modal', 'true'); box.setAttribute('aria-labelledby', 'fb-title');
    var h = document.createElement('h2'); h.id = 'fb-title'; h.textContent = t('title');
    var p = document.createElement('p'); p.textContent = t(kind === 'route' ? 'introRoute' : kind === 'data' ? 'introData' : 'intro');
    var form = document.createElement('form'); form.noValidate = true;
    var l1 = document.createElement('label'); l1.textContent = t('msg'); l1.htmlFor = 'fb-msg';
    var ta = document.createElement('textarea'); ta.id = 'fb-msg'; ta.maxLength = MAX; ta.required = true;
    var l2 = document.createElement('label'); l2.textContent = t('email'); l2.htmlFor = 'fb-email';
    var em = document.createElement('input'); em.type = 'email'; em.id = 'fb-email'; em.autocomplete = 'email'; em.maxLength = 120;
    var note = document.createElement('p'); note.className = 'fb-note'; note.textContent = t('note');
    // Robots fill in every box; people never see this one.
    var trap = document.createElement('input'); trap.type = 'checkbox'; trap.name = 'botcheck'; trap.className = 'fb-trap'; trap.tabIndex = -1; trap.setAttribute('aria-hidden', 'true');
    var status = document.createElement('div'); status.className = 'fb-status'; status.setAttribute('aria-live', 'polite');
    var row = document.createElement('div'); row.className = 'fb-row';
    var cancel = document.createElement('button'); cancel.type = 'button'; cancel.className = 'fb-cancel'; cancel.textContent = t('cancel');
    var send = document.createElement('button'); send.type = 'submit'; send.className = 'fb-send'; send.textContent = t('send');
    row.appendChild(cancel); row.appendChild(send);
    [l1, ta, l2, em, note, trap, status, row].forEach(function (x) { form.appendChild(x); });
    box.appendChild(h); box.appendChild(p); box.appendChild(form);
    back.appendChild(box);
    document.body.appendChild(back);
    var before = document.activeElement;
    setTimeout(function () { ta.focus(); }, 30);

    function close() {
      document.removeEventListener('keydown', onKey);
      if (back.parentNode) back.parentNode.removeChild(back);
      if (before && before.focus) try { before.focus(); } catch (e) {}
    }
    function onKey(e) { if (e.key === 'Escape') close(); }
    document.addEventListener('keydown', onKey);
    cancel.addEventListener('click', close);
    back.addEventListener('click', function (e) { if (e.target === back) close(); });

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var text = ta.value.trim(), mail = em.value.trim();
      status.className = 'fb-status err';
      if (!text) { status.textContent = t('empty'); ta.focus(); return; }
      if (mail && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(mail)) { status.textContent = t('badEmail'); em.focus(); return; }
      status.className = 'fb-status'; status.textContent = t('sending');
      send.disabled = true;
      var what = { general: 'Sugerencia', route: 'Ruta', data: 'Error en los datos' }[kind] || kind;
      var where = [
        'Tipo: ' + what,
        opts.context ? 'Contexto: ' + opts.context : '',
        'Página: ' + location.href,
        'Idioma: ' + lang() + ' · ' + platform(),
        mail ? 'Correo: ' + mail : 'Sin correo'
      ].filter(Boolean).join('\n');
      var body = { access_key: KEY, subject: 'Ski Info · ' + what + (opts.station ? ' · ' + opts.station : ''),
        from_name: 'Ski Info', message: text + '\n\n---\n' + where, botcheck: trap.checked };
      if (mail) body.email = mail;
      fetch(ENDPOINT, { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' }, body: JSON.stringify(body) })
        .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { if (!r.ok || !j.success) throw new Error(j.message || r.status); }); })
        .then(function () {
          form.innerHTML = '';
          p.remove();
          var done = document.createElement('div'); done.className = 'fb-done'; done.textContent = t('ok');
          var r2 = document.createElement('div'); r2.className = 'fb-row';
          var c2 = document.createElement('button'); c2.type = 'button'; c2.className = 'fb-send'; c2.textContent = t('close');
          c2.addEventListener('click', close);
          r2.appendChild(c2); form.appendChild(done); form.appendChild(r2);
          c2.focus();
        })
        .catch(function () { send.disabled = false; status.className = 'fb-status err'; status.textContent = t('err'); });
    });
  }

  // Links on the page: <a data-feedback="data">…</a> (text filled in if empty).
  function bind(root) {
    Array.prototype.forEach.call((root || document).querySelectorAll('[data-feedback]'), function (a) {
      if (a.dataset.fbBound) return;
      a.dataset.fbBound = '1';
      var kind = a.getAttribute('data-feedback') || 'general';
      if (!a.textContent.trim()) a.textContent = t(kind === 'data' ? 'data' : kind === 'route' ? 'route' : 'link');
      a.classList.add('fb-link');
      a.addEventListener('click', function (e) {
        e.preventDefault();
        open({ kind: kind, context: a.getAttribute('data-feedback-context') || document.title, station: a.getAttribute('data-feedback-station') || '' });
      });
    });
  }
  window.SkiFeedback = { open: open, bind: bind, label: t };
  style();
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { bind(); });
  else bind();
})();
