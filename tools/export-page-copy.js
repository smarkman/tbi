/*
 * TBI page COPY export — READ-ONLY. Second pass after export-cms.js.
 *
 * ShulCloud keeps body copy on the live page, not in the CMS settings form, so this script
 * reads the CMS Pages list, then opens each page's public URL and pulls the main content.
 *
 * How to use (same as before):
 *   1. Open https://www.tbiport.org/admin/cms.php?query=&status=&setPerPage=100 while logged in
 *   2. Open the Console (Ctrl+Shift+J / Cmd+Option+J), type  allow pasting  + Enter if asked
 *   3. Paste this whole file, press Enter, leave the tab open (~10 min for ~1,100 pages)
 *   4. Downloads tbi-page-copy.csv (plain text) and tbi-page-copy.json (text + HTML)
 *
 * Only GET requests are made. Nothing is edited, saved, cloned or deleted.
 */
(async () => {
  const DELAY_MS = 400;
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const abs = (h) => { try { return new URL(h, location.href).href; } catch { return ''; } };
  const getDoc = async (url) => {
    const res = await fetch(url, { credentials: 'include' });
    return { status: res.status, finalUrl: res.url, doc: new DOMParser().parseFromString(await res.text(), 'text/html') };
  };

  // ---- 1. Walk the CMS Pages list (all numbered pages) ----
  const listUrls = [location.href], seenLists = new Set(listUrls), pages = new Map();
  for (let i = 0; i < listUrls.length; i++) {
    const doc = i === 0 ? document : (await getDoc(listUrls[i])).doc;
    doc.querySelectorAll('a[href]').forEach((a) => {
      const u = abs(a.getAttribute('href')), t = a.textContent.trim();
      if (u && new URL(u).pathname === location.pathname && /^(\d+|Next.*)$/i.test(t) && !seenLists.has(u)) { seenLists.add(u); listUrls.push(u); }
    });
    doc.querySelectorAll('tr').forEach((tr) => {
      const links = [...tr.querySelectorAll('a[href]')];
      const edit = links.find((a) => a.textContent.trim() === 'Edit');
      const view = links.find((a) => /view/i.test(a.textContent));
      if (!edit || !view) return;
      const c = [...tr.cells].map((td) => td.innerText.trim());
      pages.set(abs(view.getAttribute('href')), { status: c[0], title_col: c[1], admin_name: c[2], type: c[3], sidebar: c[4], edit_url: abs(edit.getAttribute('href')) });
    });
    if (i) await sleep(DELAY_MS);
  }
  console.log(`Found ${pages.size} pages across ${listUrls.length} list pages.`);

  // ---- 2. Pull main content from each live page ----
  const JUNK = 'script,style,noscript,iframe,header,nav,footer,aside,form[action*="search"],[class*="nav" i],[id*="nav" i],[class*="menu" i],[id*="menu" i],[class*="header" i],[id*="header" i],[class*="footer" i],[id*="footer" i],[class*="sidebar" i],[id*="sidebar" i],[class*="breadcrumb" i],[class*="slider" i],[id*="slider" i],[class*="admin" i],[id*="admin" i]';
  const CANDIDATES = 'main,article,[role=main],#content,.content,#main,.main,.page-content,.cms-content,.cms_content,#cms_content,.entry-content,.container';
  const clean = (s) => s.replace(/[ \t ]+/g, ' ').replace(/\n\s*\n+/g, '\n\n').trim();
  const records = [];
  let n = 0;
  for (const [url, meta] of pages) {
    n++;
    try {
      const { status, finalUrl, doc } = await getDoc(url);
      const pageTitle = doc.title.trim();
      const h1 = doc.querySelector('h1')?.textContent.trim() || '';
      doc.querySelectorAll(JUNK).forEach((el) => { if (el !== doc.body && !el.querySelector('h1')) el.remove(); });
      let best = doc.body, bestLen = 0, sel = 'body';
      doc.querySelectorAll(CANDIDATES).forEach((el) => {
        const len = (el.textContent || '').trim().length;
        // prefer the smallest container that still holds most of the text
        if (len > 50 && (bestLen === 0 || (len < bestLen && len > bestLen * 0.6) || len > bestLen * 1.6)) { best = el; bestLen = len; sel = el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (el.className ? '.' + String(el.className).trim().split(/\s+/).join('.') : ''); }
      });
      const tmp = document.createElement('div'); tmp.innerHTML = best.innerHTML;
      const text = clean(tmp.innerText || tmp.textContent || '');
      const links = [...best.querySelectorAll('a[href]')].map((a) => abs(a.getAttribute('href'))).filter(Boolean);
      const images = [...best.querySelectorAll('img[src]')].map((i) => abs(i.getAttribute('src')));
      records.push({ ...meta, view_url: url, final_url: finalUrl, http_status: status, page_title: pageTitle, h1, content_selector: sel,
        word_count: text ? text.split(/\s+/).length : 0, text, html: best.innerHTML.trim(), links, images });
      console.log(`[${n}/${pages.size}] ${meta.admin_name} — ${records.at(-1).word_count} words`);
    } catch (e) {
      records.push({ ...meta, view_url: url, error: String(e) });
      console.warn(`[${n}/${pages.size}] failed ${url}`, e);
    }
    await sleep(DELAY_MS);
  }

  // ---- 3. Download ----
  const dl = (name, content, type) => { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([content], { type })); a.download = name; document.body.appendChild(a); a.click(); a.remove(); };
  dl('tbi-page-copy.json', JSON.stringify({ exported_at: new Date().toISOString(), records }, null, 1), 'application/json');
  const cols = ['admin_name', 'status', 'view_url', 'final_url', 'http_status', 'page_title', 'h1', 'word_count', 'link_count', 'image_count', 'content_selector', 'text', 'edit_url'];
  const esc = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`;
  const csv = [cols.join(',')].concat(records.map((r) => cols.map((c) => esc(c === 'link_count' ? r.links?.length : c === 'image_count' ? r.images?.length : r[c])).join(',')));
  dl('tbi-page-copy.csv', '﻿' + csv.join('\n'), 'text/csv');
  console.log(`Done. ${records.length} pages exported.`);
})();
