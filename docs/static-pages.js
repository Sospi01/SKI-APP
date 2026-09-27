// Interactivity for the generated station pages: the Pistas/Remontes/Servicios
// switcher, their filter chips, and each run's elevation profile (drawn with
// profile.js from the station's data file, fetched on first expand). The page
// is fully readable without this script -- it only adds the app's behaviour.
(function () {
  var stationId = document.body.getAttribute('data-station');

  document.querySelectorAll('.seg-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var which = btn.getAttribute('data-catalog');
      document.querySelectorAll('.seg-btn').forEach(function (b) {
        b.setAttribute('aria-selected', b === btn ? 'true' : 'false');
      });
      document.querySelectorAll('.catalog-panel').forEach(function (p) {
        p.hidden = p.id !== 'catalog-' + which;
      });
    });
  });

  // Chips carry data-keys (space-separated) matched against each item's
  // data-key; "all" shows everything. A run's profile panel follows its run.
  document.querySelectorAll('.chips[data-list]').forEach(function (chips) {
    var list = document.getElementById(chips.getAttribute('data-list'));
    chips.querySelectorAll('.chip').forEach(function (chip) {
      chip.addEventListener('click', function () {
        chips.querySelectorAll('.chip').forEach(function (c) { c.setAttribute('aria-pressed', c === chip ? 'true' : 'false'); });
        var keys = chip.getAttribute('data-keys');
        list.querySelectorAll('.item').forEach(function (item) {
          var show = keys === 'all' || keys.split(' ').indexOf(item.getAttribute('data-key')) !== -1;
          item.style.display = show ? '' : 'none';
          var next = item.nextElementSibling;
          if (next && next.classList.contains('run-profile')) next.style.display = show ? '' : 'none';
        });
      });
    });
  });

  var dataPromise = null;
  function stationData() {
    if (!dataPromise) {
      dataPromise = fetch('/data/' + stationId + '.json').then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      });
    }
    return dataPromise;
  }
  function isDownhill(r) { return !r.uses || r.uses.split(',').indexOf('downhill') !== -1; }

  document.querySelectorAll('.run-item').forEach(function (item) {
    var panel = item.nextElementSibling;
    var rendered = false;
    function toggle() {
      var open = item.getAttribute('aria-expanded') === 'true';
      item.setAttribute('aria-expanded', open ? 'false' : 'true');
      panel.hidden = open;
      if (open || rendered) return;
      rendered = true;
      panel.className = 'run-profile empty';
      panel.textContent = 'Cargando perfil…';
      var name = item.getAttribute('data-run');
      stationData().then(function (raw) {
        var parts = [];
        raw.runs.forEach(function (r) {
          if (isDownhill(r) && r.name === name && r.geom) parts = parts.concat(r.geom);
        });
        panel.className = 'run-profile';
        panel.textContent = '';
        renderRunProfile(panel, { geomParts: parts });
      }).catch(function () {
        rendered = false;
        panel.textContent = 'No se pudo cargar el perfil. Inténtalo de nuevo.';
      });
    }
    item.addEventListener('click', toggle);
    item.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); }
    });
  });
})();
