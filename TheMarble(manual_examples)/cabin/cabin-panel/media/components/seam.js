// seam.js — seam snapshot list + diff button. The invisible made visible.
(function () {
  function esc(s) {
    return (s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  function fmtTs(ts) {
    if (!ts) return '—';
    try {
      const s = ts.replace(/^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2}).*/, '$1-$2-$3T$4:$5:$6Z');
      const d = new Date(s);
      if (isNaN(d)) return ts.slice(0, 16);
      return d.toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' });
    } catch { return ts.slice(0, 16); }
  }

  function showDiff(container, server, beforePath, afterPath, btn) {
    btn.disabled = true;
    btn.textContent = 'loading…';
    const url = server + '/seam/diff?before=' + encodeURIComponent(beforePath) + '&after=' + encodeURIComponent(afterPath);
    fetch(url)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.error) {
          btn.textContent = 'error';
          btn.disabled = false;
          return;
        }
        const diff = data.diff;

        function section(label, ids, color) {
          if (!ids || !ids.length) return '';
          return '<div style="color:' + color + ';margin-bottom:4px;font-weight:600">' + label + ' (' + ids.length + ')</div>' +
            ids.map(function (id) { return '<div style="padding-left:10px">' + esc(id) + '</div>'; }).join('');
        }

        const diffEl = document.createElement('div');
        diffEl.style.cssText = 'margin-top:8px;padding:8px;background:var(--vscode-editor-background);border-radius:4px;font-family:monospace;font-size:10px;';
        diffEl.innerHTML =
          section('removed — check these', diff.removed.ids, 'var(--cabin-red)') +
          section('added', diff.added.ids, 'var(--cabin-green)') +
          section('unchanged', diff.unchanged.ids, 'var(--cabin-dim)') +
          (diff.removed.count === 0 && diff.added.count === 0
            ? '<span style="color:var(--cabin-dim)">no changes between these two snapshots</span>' : '');

        btn.closest('.seam-row').insertAdjacentElement('afterend', diffEl);
        btn.textContent = 'hide';
        btn.disabled = false;

        btn.addEventListener('click', function onHide() {
          diffEl.remove();
          btn.textContent = 'diff';
          btn.removeEventListener('click', onHide);
          btn.addEventListener('click', function () {
            showDiff(container, server, beforePath, afterPath, btn);
          }, { once: true });
        }, { once: true });
      })
      .catch(function () {
        btn.textContent = 'diff';
        btn.disabled = false;
      });
  }

  function render(container, snapshots, server) {
    if (!snapshots || snapshots.length === 0) {
      container.innerHTML = '<span class="empty">no seam snapshots yet</span>';
      return;
    }

    container.innerHTML = '';

    snapshots.forEach(function (snap, i) {
      const hasPrev  = i < snapshots.length - 1;
      const prevPath = hasPrev ? snapshots[i + 1].path : null;

      const names = (snap.files || []).slice(0, 3).map(function (f) {
        return '<span style="font-family:monospace"> · ' + esc(f.split(/[\\/]/).pop()) + '</span>';
      }).join('');
      const more = snap.file_count > 3 ? ' + ' + (snap.file_count - 3) + ' more' : '';

      const row = document.createElement('div');
      row.className = 'seam-row';
      row.innerHTML =
        '<div style="flex:1;min-width:0">' +
        '  <div class="seam-ts">' + esc(fmtTs(snap.ts)) + '</div>' +
        '  <div style="font-size:10px;color:var(--cabin-dim);margin-top:2px">' +
        snap.file_count + ' file(s)' + names + more +
        '  </div>' +
        '</div>' +
        (hasPrev
          ? '<button class="btn secondary" style="font-size:10px" ' +
            'data-snap="' + esc(snap.path) + '" data-prev="' + esc(prevPath) + '">diff</button>'
          : '');

      const dBtn = row.querySelector('[data-snap]');
      if (dBtn) {
        dBtn.addEventListener('click', function () {
          showDiff(container, server, dBtn.getAttribute('data-prev'), dBtn.getAttribute('data-snap'), dBtn);
        }, { once: true });
      }

      container.appendChild(row);
    });
  }

  window.CabinComponents = window.CabinComponents || {};
  window.CabinComponents['seam'] = {
    id: 'seam',
    title: 'Seam History',
    pollMs: 30000,
    mount(container, server) {
      container.innerHTML = '<span class="loading">loading…</span>';
      const load = () =>
        fetch(server + '/seam')
          .then(function (r) { return r.json(); })
          .then(function (d) { render(container, d.snapshots, server); })
          .catch(function (e) { container.innerHTML = '<span class="error-msg">' + e.message + '</span>'; });
      load();
      const timer = setInterval(load, 30000);
      return () => clearInterval(timer);
    },
  };
})();
