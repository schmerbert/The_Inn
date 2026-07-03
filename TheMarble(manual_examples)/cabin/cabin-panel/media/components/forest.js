// forest.js — "Ask the forest": zero-token forest browse with full provenance.
(function () {
  function esc(s) {
    return (s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  function provTags(hit) {
    return [
      '<span class="tag ' + (hit.forest || 'home') + '">' + esc(hit.forest || 'home') + '</span>',
      '<span class="tag">' + esc(hit.bucket) + '</span>',
      hit.voiced ? '<span class="tag voiced">voiced</span>' : '<span class="tag voiceless">voiceless</span>',
      hit.writer      ? '<span class="tag">'         + esc(hit.writer)      + '</span>' : '',
      hit.source_kind ? '<span class="tag">'         + esc(hit.source_kind) + '</span>' : '',
      hit.author      ? '<span class="tag">'         + esc(hit.author)      + '</span>' : '',
      hit.model       ? '<span class="tag">'         + esc(hit.model)       + '</span>' : '',
      hit.lesson      ? '<span class="tag">'         + esc(hit.lesson)      + '</span>' : '',
      hit.effective_pressure > 0
        ? '<span class="tag pressure">pressure ' + hit.effective_pressure + '</span>' : '',
      hit.traversal_count > 0
        ? '<span class="tag">recalled ' + hit.traversal_count + '×</span>' : '',
      hit.dismissed ? '<span class="tag" style="opacity:.5">dismissed</span>' : '',
      '<span class="tag" style="opacity:.6">d=' + hit.distance + '</span>',
    ].filter(Boolean).join('');
  }

  function provDates(hit) {
    const parts = [];
    if (hit.created_at)  parts.push('born '      + hit.created_at.slice(0,10));
    if (hit.traversed_at) parts.push('last seen ' + hit.traversed_at.slice(0,10));
    return parts.length
      ? '<div style="font-size:10px;color:var(--cabin-dim);margin-top:3px">' + esc(parts.join(' · ')) + '</div>'
      : '';
  }

  function renderHits(resultsEl, hits, server) {
    resultsEl.innerHTML = '';
    if (!hits || hits.length === 0) {
      resultsEl.innerHTML = '<span class="empty">nothing found</span>';
      return;
    }

    hits.forEach(function (hit) {
      const card = document.createElement('div');
      card.className = 'entry-card';
      const isWild = hit.forest === 'wild';
      const canFollow = hit.source_type === 'conversation' || isWild;
      card.innerHTML =
        '<div class="entry-body">'  + esc(hit.body) + '</div>' +
        '<div class="prov-row">'    + provTags(hit) + '</div>' +
        provDates(hit) +
        '<div class="entry-actions">' +
        (canFollow ? '<button class="btn secondary" data-follow="' + esc(hit.id) + '">Follow thread →</button>' : '') +
        (isWild ? '' :
          (hit.dismissed
            ? '<button class="btn secondary" data-restore="' + esc(hit.id) + '" data-bucket="' + esc(hit.bucket) + '">Restore</button>'
            : '<button class="btn secondary" data-dismiss="' + esc(hit.id) + '" data-bucket="' + esc(hit.bucket) + '">Dismiss</button>'
          )
        ) +
        '</div>' +
        '<div class="thread-view" style="display:none"></div>';

      const dismissBtn = card.querySelector('[data-dismiss]');
      if (dismissBtn) {
        dismissBtn.addEventListener('click', function () {
          const id     = dismissBtn.getAttribute('data-dismiss');
          const bucket = dismissBtn.getAttribute('data-bucket');
          fetch(server + '/dismiss/' + encodeURIComponent(id) + '?bucket=' + encodeURIComponent(bucket),
            { method: 'POST' }).catch(function () {});
          card.style.opacity = '0.4';
          dismissBtn.textContent = 'dismissed';
          dismissBtn.disabled = true;
        });
      }

      const restoreBtn = card.querySelector('[data-restore]');
      if (restoreBtn) {
        restoreBtn.addEventListener('click', function () {
          const id     = restoreBtn.getAttribute('data-restore');
          const bucket = restoreBtn.getAttribute('data-bucket');
          fetch(server + '/undismiss/' + encodeURIComponent(id) + '?bucket=' + encodeURIComponent(bucket),
            { method: 'POST' }).catch(function () {});
          card.style.opacity = '1';
          restoreBtn.textContent = 'restored';
          restoreBtn.disabled = true;
        });
      }

      const followBtn = card.querySelector('[data-follow]');
      if (followBtn) {
        followBtn.addEventListener('click', function () {
          const id = followBtn.getAttribute('data-follow');
          const threadEl = card.querySelector('.thread-view');
          if (threadEl.style.display !== 'none') {
            threadEl.style.display = 'none';
            followBtn.textContent = 'Follow thread →';
            return;
          }
          followBtn.textContent = 'walking…';
          followBtn.disabled = true;
          fetch(server + '/traverse', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ entry_id: id }),
          })
            .then(function (r) { return r.json(); })
            .then(function (d) {
              followBtn.textContent = 'Close thread ↑';
              followBtn.disabled = false;
              if (d.error) {
                threadEl.innerHTML = '<div class="error-msg">' + esc(d.error) + '</div>';
                threadEl.style.display = 'block';
                return;
              }
              const th = d.trailhead;
              const win = d.window || [];
              const total = d.total_in_session;
              const sid = d.session_id;
              let html = '<div class="thread-inner">';
              if (th) {
                html += '<div class="thread-trailhead">⌂ ' + esc(th.body ? th.body.slice(0, 120) : sid) + '</div>';
              }
              if (total) {
                html += '<div class="thread-meta">' + win.length + ' of ' + total + ' in session</div>';
              }
              win.forEach(function (e) {
                const isFocus = e.id === id;
                html += '<div class="thread-entry' + (isFocus ? ' thread-focus' : '') + '">' + esc(e.body) + '</div>';
              });
              html += '</div>';
              threadEl.innerHTML = html;
              threadEl.style.display = 'block';
            })
            .catch(function (err) {
              followBtn.textContent = 'Follow thread →';
              followBtn.disabled = false;
              const threadEl2 = card.querySelector('.thread-view');
              threadEl2.innerHTML = '<div class="error-msg">' + esc(err.message) + '</div>';
              threadEl2.style.display = 'block';
            });
        });
      }

      resultsEl.appendChild(card);
    });
  }

  window.CabinComponents = window.CabinComponents || {};
  window.CabinComponents['forest'] = {
    id: 'forest',
    title: 'Ask the Forest',
    pollMs: null,
    mount(container, server) {
      container.innerHTML =
        '<div style="display:flex;gap:6px;margin-bottom:8px">' +
        '  <input class="cabin-input" type="text" id="forest-query" placeholder="type anything — the forest surfaces what it knows">' +
        '  <button class="btn" id="forest-search">Search</button>' +
        '</div>' +
        '<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px;align-items:center">' +
        '  <div style="display:flex;gap:2px">' +
        '    <button class="btn forest-tab active" data-forest="home" style="font-size:11px;padding:2px 8px">Home</button>' +
        '    <button class="btn forest-tab" data-forest="wild" style="font-size:11px;padding:2px 8px">Wild</button>' +
        '  </div>' +
        '  <label style="font-size:11px;display:flex;align-items:center;gap:4px"><input type="checkbox" id="forest-voiced-only"> voiced only</label>' +
        '  <label style="font-size:11px;display:flex;align-items:center;gap:4px"><input type="checkbox" id="forest-dismissed"> show dismissed</label>' +
        '</div>' +
        '<div id="forest-results"></div>';

      const input    = container.querySelector('#forest-query');
      const btn      = container.querySelector('#forest-search');
      const results  = container.querySelector('#forest-results');
      const voicedCb = container.querySelector('#forest-voiced-only');
      const dismCb   = container.querySelector('#forest-dismissed');
      const tabs     = container.querySelectorAll('.forest-tab');

      let currentForest = 'home';
      tabs.forEach(function (tab) {
        tab.addEventListener('click', function () {
          currentForest = tab.getAttribute('data-forest');
          tabs.forEach(function (t) { t.classList.toggle('active', t === tab); });
          const isWild = currentForest === 'wild';
          voicedCb.disabled = isWild;
          dismCb.disabled = isWild;
          voicedCb.parentElement.style.opacity = isWild ? '0.4' : '1';
          dismCb.parentElement.style.opacity = isWild ? '0.4' : '1';
        });
      });

      let searchSeq = 0;
      function search() {
        const q = input.value.trim();
        if (!q) return;
        results.innerHTML = '<span class="loading">foraging…</span>';
        const seq = ++searchSeq;
        const isWild = currentForest === 'wild';
        fetch(server + '/forage', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: q,
            k: 12,
            forest: currentForest,
            voiced_only: isWild ? false : voicedCb.checked,
            include_dismissed: isWild ? false : dismCb.checked,
          }),
        })
          .then(function (r) { return r.json(); })
          .then(function (d) {
            if (seq !== searchSeq) return;
            renderHits(results, d.hits, server);
            const errs = d.errors || {};
            const errKeys = Object.keys(errs);
            if (errKeys.length) {
              const errDiv = document.createElement('div');
              errDiv.style.marginTop = '8px';
              errDiv.innerHTML = errKeys.map(function (b) {
                return '<div class="error-msg" style="font-size:10px;font-family:monospace">' +
                       esc(b) + ': ' + esc(errs[b]) + '</div>';
              }).join('');
              results.appendChild(errDiv);
            }
          })
          .catch(function (e) {
            if (seq !== searchSeq) return;
            results.innerHTML = '<span class="error-msg">' + e.message + '</span>';
          });
      }

      btn.addEventListener('click', search);
      input.addEventListener('keydown', function (e) { if (e.key === 'Enter') search(); });
    },
  };
})();
