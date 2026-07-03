// main.js — mounts LAYOUT components into the panel root.
// The layout engine. Knows nothing about what any component does.
// Runs after all component scripts and layout.js have loaded.

(function () {
  const SERVER = window.__CABIN_SERVER__ || 'http://127.0.0.1:7771';
  const root   = document.getElementById('cabin-panel');
  const layout = window.CabinLayout || [];
  const comps  = window.CabinComponents || {};
  const cleanups = [];

  layout.forEach(({ id, hidden }) => {
    if (hidden) return;
    const component = comps[id];
    if (!component) {
      console.warn('cabin: no component registered for id:', id);
      return;
    }

    const section = document.createElement('section');
    section.className = 'cabin-section';
    section.dataset.componentId = id;

    const header = document.createElement('div');
    header.className = 'section-header collapsible';
    header.textContent = component.title;
    section.appendChild(header);

    const content = document.createElement('div');
    content.className = 'section-content';
    section.appendChild(content);

    header.addEventListener('click', () => {
      header.classList.toggle('collapsed');
      content.classList.toggle('collapsed');
    });

    root.appendChild(section);

    try {
      const cleanup = component.mount(content, SERVER);
      if (cleanup && typeof cleanup.then === 'function') {
        cleanup.then(fn => { if (typeof fn === 'function') cleanups.push(fn); });
      } else if (typeof cleanup === 'function') {
        cleanups.push(cleanup);
      }
    } catch (err) {
      content.innerHTML = '<span class="error-msg">mount error: ' + err.message + '</span>';
    }
  });

  window.addEventListener('beforeunload', () => cleanups.forEach(fn => fn()));
})();
