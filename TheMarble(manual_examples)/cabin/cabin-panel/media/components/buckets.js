// buckets.js — bucket list, entry counts, high-pressure entries, quarantine button.
(function () {
  function esc(s) {
    return (s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  function render(container, buckets, server) {
    if (!buckets || buckets.length === 0) {
      container.innerHTML = '<span class="empty">no buckets found</span>';
      return;
    }

    container.innerHTML = '';

    buckets.forEach(function (b) {
      const disabled = !b.enabled;
      const voice    = b.voiced ? 'voiced' : 'voiceless';
      const hp       = b.high_pressure || [];

      const row = document.createElement('div');
      row.className = 'bucket-row' + (disabled ? ' bucket-disabled' : '');

      const hpHtml = hp.length === 0 ? '' :
        '<div style="margin-top:6px">' +
        '  <div style="font-size:10px;text-transform:uppercase;letter-spacing:.04em;color:var(--cabin-red);margin-bottom:3px">high pressure (' + hp.length + ')</div>' +
        hp.map(function (e) {
          const p = (e.neighbor_pressure || 0) + 2 * (e.surface_pressure || 0);
          return '<div style="font-size:10px;font-family:monospace;padding:3px 6px;' +
                 'background:rgba(224,80,80,.06);border-radius:3px;margin-bottom:3px;' +
                 'border-left:2px solid var(--cabin-red)">' +
                 esc((e.body || '').slice(0, 120)) +
                 ' <span style="color:var(--cabin-dim)">— p' + p + '</span></div>';
        }).join('') +
        '</div>';

      row.innerHTML =
        '<div style="flex:1;min-width:0">' +
        '  <div style="display:flex;align-items:center;gap:6px;margin-bottom:3px">' +
        '    <span class="bucket-name">' + esc(b.bucket) + '</span>' +
        '    <span class="tag ' + esc(b.forest) + '">' + esc(b.forest) + '</span>' +
        '    <span class="tag ' + voice + '">' + voice + '</span>' +
        (disabled ? '    <span class="tag" style="color:var(--cabin-red)">quarantined</span>' : '') +
        '  </div>' +
        '  <div class="bucket-meta">' + b.entry_count + ' entries' + (b.note ? ' · ' + esc(b.note) : '') + '</div>' +
        hpHtml +
        '</div>' +
        (!disabled
          ? '<button class="btn danger" style="flex-shrink:0;font-size:10px" data-quarantine="' + esc(b.bucket) + '">Quarantine</button>'
          : '');

      const qBtn = row.querySelector('[data-quarantine]');
      if (qBtn) {
        qBtn.addEventListener('click', function () {
          const bucket = qBtn.getAttribute('data-quarantine');
          if (!confirm('Quarantine "' + bucket + '"? It stops surfacing until re-enabled.')) return;
          fetch(server + '/quarantine/' + encodeURIComponent(bucket), { method: 'POST' })
            .then(function (r) { return r.json(); })
            .then(function (d) {
              if (d.ok) {
                row.classList.add('bucket-disabled');
                qBtn.remove();
                row.querySelector('.bucket-meta').insertAdjacentHTML('afterend',
                  '<span class="tag" style="color:var(--cabin-red);margin-top:4px;display:inline-block">quarantined</span>');
              }
            })
            .catch(function () {});
        });
      }

      container.appendChild(row);
    });
  }

  window.CabinComponents = window.CabinComponents || {};
  window.CabinComponents['buckets'] = {
    id: 'buckets',
    title: 'Memory State',
    pollMs: 15000,
    mount(container, server) {
      container.innerHTML = '<span class="loading">loading…</span>';
      const load = () =>
        fetch(server + '/buckets')
          .then(function (r) { return r.json(); })
          .then(function (d) { render(container, d.buckets, server); })
          .catch(function (e) { container.innerHTML = '<span class="error-msg">' + e.message + '</span>'; });
      load();
      const timer = setInterval(load, 15000);
      return () => clearInterval(timer);
    },
  };
})();
