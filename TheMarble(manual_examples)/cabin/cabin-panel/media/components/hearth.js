// hearth.js — gauge bar, trend, model info, hound pulse, last seam.
(function () {
  function gaugeColor(pct) {
    if (pct >= 80) return 'red';
    if (pct >= 55) return 'yellow';
    return 'green';
  }

  function fmtTs(ts) {
    if (!ts) return '';
    try {
      const s = ts.replace(/^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2}).*/, '$1-$2-$3T$4:$5:$6Z');
      const d = new Date(s);
      if (isNaN(d)) return ts.slice(0, 16);
      return d.toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' });
    } catch { return ts.slice(0, 16); }
  }

  function esc(s) {
    return (s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  function addRootSwitcher(container, server) {
    const wrap = document.createElement('div');
    wrap.style.cssText = 'display:flex;gap:6px;margin-bottom:10px;';
    wrap.innerHTML =
      '<input class="cabin-input" id="root-input" style="font-family:monospace;font-size:11px" ' +
      '       placeholder="path to project root (e.g. C:\\Users\\...\\Mycroft)">' +
      '<button class="btn secondary" id="root-switch" style="white-space:nowrap;font-size:11px">Switch root</button>';
    container.appendChild(wrap);

    const input = wrap.querySelector('#root-input');
    const btn   = wrap.querySelector('#root-switch');
    btn.addEventListener('click', function () {
      const root = input.value.trim();
      if (!root) return;
      fetch(server + '/root', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ root }),
      })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (d.ok) { btn.textContent = '✓'; setTimeout(function () { btn.textContent = 'Switch root'; }, 1500); }
          else { btn.textContent = d.error || 'error'; }
        })
        .catch(function (e) { btn.textContent = e.message; });
    });
  }

  function renderSection(label, items) {
    if (!items || !items.length) return '';
    return '<div class="card-section">' +
      '<div class="card-label">' + label + '</div>' +
      '<ul class="card-list">' +
      items.map(function (t) { return '<li>' + esc(t) + '</li>'; }).join('') +
      '</ul></div>';
  }

  function renderPulse(pulse) {
    const ts = pulse.ts || pulse.path || '';
    const header = '<hr class="divider"><div class="pulse-ts">hound pulse &nbsp;·&nbsp; ' + esc(fmtTs(ts)) + '</div>';

    // Structured card (decisions / open / friction / next)
    if (pulse.decisions || pulse.open || pulse.friction || pulse.next) {
      const noteHtml = pulse.note
        ? '<div class="hound-note">' + esc(pulse.note) + '</div>'
        : '';
      return header +
        '<div class="card-body">' +
        renderSection('DECISIONS', pulse.decisions) +
        renderSection('OPEN', pulse.open) +
        renderSection('FRICTION', pulse.friction) +
        renderSection('NEXT', pulse.next) +
        noteHtml +
        '</div>';
    }

    // Raw text fallback (older pulses)
    const text = pulse.raw || pulse.text || '';
    return header + '<div class="pulse-body">' + esc(text) + '</div>';
  }

  function render(container, data) {
    const gauge  = data.gauge  || {};
    const pulse  = data.pulse;
    const seam   = data.seam;
    const pct    = gauge.pct   || 0;
    const trend  = gauge.trend || 'steady';
    const color  = gaugeColor(pct);
    const turns  = gauge.turns  != null ? gauge.turns  : '—';
    const cache  = gauge.cache_pct != null ? gauge.cache_pct : '—';
    const sid    = gauge.session_id ? gauge.session_id.slice(0, 8) : '—';
    const model  = gauge.model || '—';

    container.innerHTML = [
      '<div class="gauge-wrap">',
      '  <div class="gauge-bar-track">',
      '    <div class="gauge-bar-fill ' + color + '" style="width:' + Math.min(pct, 100) + '%"></div>',
      '  </div>',
      '  <div class="gauge-meta">',
      '    <span>' + pct + '% &nbsp;·&nbsp; ' +
               (gauge.total_in || 0).toLocaleString() + ' / ' +
               (gauge.window   || 0).toLocaleString() + ' tokens</span>',
      '    <span class="gauge-trend ' + trend + '">' + trend + '</span>',
      '  </div>',
      '  <div class="gauge-meta">',
      '    <span>turns: ' + turns + ' &nbsp;·&nbsp; cache: ' + cache + '% &nbsp;·&nbsp; session: ' + sid + '</span>',
      '    <span style="font-size:10px;color:var(--cabin-dim)">' + esc(model) + '</span>',
      '  </div>',
      '</div>',
      gauge.error ? '<div class="error-msg" style="margin-top:6px">' + esc(gauge.error) + '</div>' : '',
      seam ? [
        '<hr class="divider">',
        '<div style="font-size:11px;color:var(--cabin-dim)">last seam &nbsp;·&nbsp; ' + esc(fmtTs(seam.ts)) + '</div>',
        '<div style="font-size:10px;font-family:monospace;margin-top:3px;color:var(--cabin-dim)">',
        (seam.files || []).slice(0, 6).map(f => '· ' + esc(f.split(/[\\/]/).pop())).join('<br>'),
        '</div>',
      ].join('') : '',
      pulse ? renderPulse(pulse) : '',
    ].join('');
  }

  window.CabinComponents = window.CabinComponents || {};
  window.CabinComponents['hearth'] = {
    id: 'hearth',
    title: 'Hearth Card',
    pollMs: 4000,
    mount(container, server) {
      container.innerHTML = '';
      addRootSwitcher(container, server);

      // Hound dispatch button
      const houndRow = document.createElement('div');
      houndRow.style.cssText = 'display:flex;align-items:center;gap:8px;margin-bottom:10px;';
      houndRow.innerHTML =
        '<button class="btn secondary" id="hound-btn" style="font-size:11px">Send Hound</button>' +
        '<span id="hound-status" style="font-size:10px;color:var(--cabin-dim)"></span>';
      container.appendChild(houndRow);

      const houndBtn    = houndRow.querySelector('#hound-btn');
      const houndStatus = houndRow.querySelector('#hound-status');
      houndBtn.addEventListener('click', function () {
        houndBtn.disabled = true;
        houndBtn.textContent = 'running…';
        houndStatus.textContent = 'hound is in the forest (~60s)';
        fetch(server + '/hound', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ reason: 'panel dispatch' }),
        })
          .then(function (r) { return r.json(); })
          .then(function (d) {
            houndBtn.disabled = false;
            houndBtn.textContent = 'Send Hound';
            houndStatus.textContent = d.ok ? 'done — card updated' : (d.error || 'error');
            if (d.ok) { load(); }
          })
          .catch(function (e) {
            houndBtn.disabled = false;
            houndBtn.textContent = 'Send Hound';
            houndStatus.textContent = e.message;
          });
      });

      const dataDiv = document.createElement('div');
      dataDiv.innerHTML = '<span class="loading">loading…</span>';
      container.appendChild(dataDiv);

      const load = () =>
        fetch(server + '/state')
          .then(r => r.json())
          .then(d => render(dataDiv, d))
          .catch(e => { dataDiv.innerHTML = '<span class="error-msg">server unreachable: ' + e.message + '</span>'; });
      load();
      const timer = setInterval(load, 4000);
      return () => clearInterval(timer);
    },
  };
})();
