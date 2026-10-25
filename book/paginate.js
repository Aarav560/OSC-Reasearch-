/* Lays out a volume: window.SEQ is a list of
     {type: 'fixed', html, chapter, dark}      a finished page (cover, opener, blueprint, ...)
     {type: 'flow', chapter, blocks: [html]}   text that is poured onto as many pages as it needs
   Then numbers every page, fills running heads and tabs, and the table of contents
   (elements with data-toc="<chapter id>" receive that chapter's first page number). */
(function () {
  const book = document.getElementById('book');
  const V = window.VOLUME;
  const pages = [];

  function newPage(cls, chapter, dark) {
    const p = document.createElement('div');
    p.className = 'page ' + (cls || '');
    p.dataset.chapter = typeof chapter === 'string' ? chapter : (chapter && chapter.id) || '';
    if (dark) p.classList.add('dark');
    book.appendChild(p); pages.push(p);
    return p;
  }
  function furniture(p) {
    const ch = (window.CHAPTERS || {})[p.dataset.chapter] || {};
    if (p.classList.contains('nofurn')) return;
    const tab = document.createElement('div'); tab.className = 'tab';
    tab.style.background = ch.color || V.color;
    tab.innerHTML = `<div class="tabno">${ch.no || V.numeral}</div><span>${ch.short || V.title}</span>`;
    p.appendChild(tab);
    const rh = document.createElement('div'); rh.className = 'rh';
    rh.innerHTML = `<b>Vol. ${V.numeral}</b> &nbsp;·&nbsp; ${V.title} &nbsp;·&nbsp; ${ch.title || ''}`;
    p.appendChild(rh);
    const rule = document.createElement('div'); rule.className = 'rule'; p.appendChild(rule);
    const f = document.createElement('div'); f.className = 'folio';
    f.innerHTML = `<small>${V.short}</small>${p.dataset.n}`;
    p.appendChild(f);
  }
  const overflows = b => b.scrollHeight > b.clientHeight + 1;

  function pour(item) {
    let page = null, body = null;
    const fresh = () => {
      page = newPage('flow', item.chapter);
      body = document.createElement('div'); body.className = 'body'; page.appendChild(body);
    };
    fresh();
    const tmp = document.createElement('div');
    for (const html of item.blocks) {
      tmp.innerHTML = html;
      const queue = Array.from(tmp.children);
      while (queue.length) {
        const el = queue.shift();
        body.appendChild(el);
        if (!overflows(body)) continue;
        body.removeChild(el);
        const splittable = (el.tagName === 'P' || el.tagName === 'LI') && !el.classList.contains('keep');
        if (splittable && body.children.length) {
          const words = el.innerHTML.split(/(?<=\s)/);
          let lo = 0, hi = words.length;
          const probe = el.cloneNode(false);
          body.appendChild(probe);
          while (lo < hi) {                       // largest prefix that still fits
            const mid = (lo + hi + 1) >> 1;
            probe.innerHTML = words.slice(0, mid).join('');
            if (overflows(body)) hi = mid - 1; else lo = mid;
          }
          if (lo >= 12) {
            probe.innerHTML = words.slice(0, lo).join('');
            probe.style.textAlignLast = 'justify';
            const rest = el.cloneNode(false); rest.classList.remove('lead');
            rest.innerHTML = words.slice(lo).join('');
            fresh(); queue.unshift(rest); continue;
          }
          body.removeChild(probe);
        }
        if (el.tagName === 'TABLE' && el.tBodies[0] && el.tBodies[0].rows.length > 1) {
          // split a long table by rows, repeating its header on each page
          const rows = Array.from(el.tBodies[0].rows);
          const part = el.cloneNode(false);
          if (el.tHead) part.appendChild(el.tHead.cloneNode(true));
          const tb = document.createElement('tbody'); part.appendChild(tb);
          body.appendChild(part);
          let k = 0;
          while (k < rows.length) {
            tb.appendChild(rows[k]);
            if (overflows(body)) { tb.removeChild(rows[k]); break; }
            k++;
          }
          if (k === 0) {                          // nothing fit: put the first row back and start a fresh page
            el.tBodies[0].insertBefore(rows[0], el.tBodies[0].firstChild);
            body.removeChild(part);
            if (body.children.length) { fresh(); queue.unshift(el); continue; }
          }
          if (k > 0 && k < rows.length) {
            const rest = el.cloneNode(false);
            if (el.tHead) rest.appendChild(el.tHead.cloneNode(true));
            const tb2 = document.createElement('tbody'); rows.slice(k).forEach(r => tb2.appendChild(r)); rest.appendChild(tb2);
            fresh(); queue.unshift(rest); continue;
          }
          if (k === rows.length) continue;
        }
        if (body.children.length) fresh();
        body.appendChild(el);
        if (overflows(body)) {                    // too tall for a whole page: scale its art down
          el.querySelectorAll('img, svg').forEach(i => { i.style.maxHeight = (body.clientHeight * .62) + 'px'; });
        }
      }
    }
  }

  for (const item of window.SEQ) {
    if (item.type === 'fixed') {
      const p = newPage(item.cls || '', item.chapter, item.dark);
      p.innerHTML = item.html;
      if (item.nofurn) p.classList.add('nofurn');
    } else pour(item);
  }
  const first = {};
  pages.forEach((p, i) => {
    const n = (window.START_PAGE || 1) + i;
    p.dataset.n = n;
    p.classList.add(n % 2 ? 'odd' : 'even');
    if (p.dataset.chapter && !(p.dataset.chapter in first)) first[p.dataset.chapter] = n;
    furniture(p);
  });
  document.querySelectorAll('[data-toc]').forEach(e => { e.textContent = first[e.dataset.toc] || ''; });
  window.PAGE_COUNT = pages.length;
  window.FIRST_PAGES = first;
  window.BOOK_READY = true;
})();
