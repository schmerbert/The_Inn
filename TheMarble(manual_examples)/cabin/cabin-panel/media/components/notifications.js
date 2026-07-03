// notifications.js — pressure neighbors + seam losses, with dismiss.
(function () {
  function esc(s) {
    return (s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  function provTags(item) {
    return [
      item.bucket       ? '<span class="tag">'          + esc(item.bucket)       + '</span>' : '',
      item.writer       ? '<span class="tag">'          + esc(item.writer)       + '</span>' : '',
      item.source_kind  ? '<span class="tag">'          + esc(item.source_kind)  + '</span>' : '',
      item.author       ? '<span class="tag">'          + esc(item.author)       + '</span>' : '',
      item.model        ? '<span class="tag">'          + esc(item.model)        + '</span>' : '',
      item.effective_pressure != null
        ? '<span class="tag pressure">pressure ' + item.effective_pressure + '</span>' : '',
    ].filter(Boolean).join('');
  }

  function render(container, items, server) {
    if (!items || items.length === 0) {
      container.innerHTML = '<span class="empty">no notifications</span>';
      return;
    }

    container.innerHTML = '';

    items.forEach(function (item) {
      const div = document.createElement('div');

      if (item.type === 'pressure') {
        div.className = 'notif-item pressure';
        div.innerHTML =
          '<div class="notif-label">pressure neighbor</div>' +
          '<div class="entry-body">' + esc(item.body) + '</div>' +
          '<div class="prov-row">' + provTags(item) + '</div>' +
          '<div class="entry-actions">' +
          '  <button class="btn secondary" data-dismiss="' + esc(item.id) + '" data-bucket="' + esc(item.bucket) + '">Dismiss</button>' +
          '</div>';
      } else if (item.type === 'seam_loss') {
        div.className = 'notif-item seam';
        const ids = (item.removed || []).map(function (id) {
          return '<div>· ' + esc(id) + '</div>';
        }).join('');
        div.innerHTML =
          '<div class="notif-label">seam loss — ' + item.count + ' file(s) dropped at last compact</div>' +
          '<div style="font-size:10px;font-family:monospace;margin-top:4px">' + ids + '</div>';
      }

      const btn = div.querySelector('[data-dismiss]');
      if (btn) {
        btn.addEventListener('click', function () {
          const id     = btn.getAttribute('data-dismiss');
          const bucket = btn.getAttribute('data-bucket');
          fetch(server + '/dismiss/' + encodeURIComponent(id) + '?bucket=' + encodeURIComponent(bucket),
            { method: 'POST' }).catch(function () {});
          btn.closest('.notif-item').remove();
          if (!container.querySelector('.notif-item')) {
            container.innerHTML = '<span class="empty">no notifications</span>';
          }
        });
      }

      container.appendChild(div);
    });
  }

  window.CabinComponents = window.CabinComponents || {};
  window.CabinComponents['notifications'] = {
    id: 'notifications',
    title: 'Live Notifications',
    pollMs: 8000,
    mount(container, server) {
      container.innerHTML = '<span class="loading">loading…</span>';
      const load = () =>
        fetch(server + '/notifications')
          .then(function (r) { return r.json(); })
          .then(function (d) { render(container, d.notifications, server); })
          .catch(function (e) { container.innerHTML = '<span class="error-msg">' + e.message + '</span>'; });
      load();
      const timer = setInterval(load, 8000);
      return () => clearInterval(timer);
    },
  };
})();
