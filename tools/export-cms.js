/*
 * TBI CMS content export — READ-ONLY.
 *
 * How to use:
 *   1. Log in and open https://www.tbiport.org/admin/cms.php?query=&status=&setPerPage=100
 *   2. Open DevTools (Cmd+Option+J on Mac / Ctrl+Shift+J on Windows) -> Console tab
 *   3. Paste this whole file and press Enter (Chrome may ask you to type "allow pasting" first)
 *   4. Wait for it to finish; two files download: tbi-cms-export.json and tbi-cms-export.csv
 *
 * What it does:
 *   - Collects every page/edit link from the CMS list (follows pagination too)
 *   - Opens each edit screen in the background with plain GET requests (nothing is saved,
 *     submitted, or deleted — links containing delete/remove/copy/status are skipped)
 *   - Reads every form field (title, URL/slug, meta title/description, body copy, etc.)
 *   - Downloads everything as JSON (full HTML) and CSV (plain text, for a spreadsheet)
 */
(async () => {
  const DELAY_MS = 400; // be gentle with the server
  const SKIP = /delete|remove|trash|copy|duplicate|clone|logout|status=|toggle|publish|unpublish|sort|order=|export/i;
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const origin = location.origin;
  const listPath = location.pathname; // e.g. /admin/cms.php

  const fetchDoc = async (url) => {
    const res = await fetch(url, { credentials: 'include' });
    const html = await res.text();
    return { status: res.status, doc: new DOMParser().parseFromString(html, 'text/html') };
  };
  const abs = (href) => { try { return new URL(href, location.href); } catch { return null; } };
  const text = (html) => {
    const d = new DOMParser().parseFromString(html || '', 'text/html');
    d.querySelectorAll('script,style').forEach((n) => n.remove());
    return (d.body?.innerText || d.body?.textContent || '').replace(/\s+\n/g, '\n').replace(/[ \t]+/g, ' ').trim();
  };

  // ---- 1. Gather list pages (pagination) and edit links ----
  const listPages = new Set([location.href]);
  const editLinks = new Map(); // url -> row label
  const queue = [location.href];
  while (queue.length) {
    const url = queue.shift();
    const { doc } = url === location.href ? { doc: document } : await fetchDoc(url);
    doc.querySelectorAll('a[href]').forEach((a) => {
      const u = abs(a.getAttribute('href'));
      if (!u || u.origin !== origin || SKIP.test(u.href)) return;
      const isPager = u.pathname === listPath && /[?&](page|p|pg|start|offset)=/i.test(u.search);
      if (isPager && !listPages.has(u.href)) { listPages.add(u.href); queue.push(u.href); return; }
      const inRow = a.closest('tr, li, .row, tbody');
      const looksLikeEdit = /edit|id=|cms/i.test(u.href) && u.href !== location.href && !isPager;
      if (inRow && looksLikeEdit && u.pathname.includes('/admin')) {
        const row = a.closest('tr');
        const label = (row ? row.innerText : a.innerText).replace(/\s+/g, ' ').trim().slice(0, 200);
        if (!editLinks.has(u.href)) editLinks.set(u.href, label);
      }
    });
    if (url !== location.href) await sleep(DELAY_MS);
  }
  console.log(`Found ${editLinks.size} candidate edit pages across ${listPages.size} list page(s).`);

  // ---- 2. Read every edit screen ----
  const records = [];
  let i = 0;
  for (const [url, listLabel] of editLinks) {
    i++;
    try {
      const { status, doc } = await fetchDoc(url);
      const fields = {};
      const labelFor = (el) => {
        if (el.id) { const l = doc.querySelector(`label[for="${CSS.escape(el.id)}"]`); if (l) return l.textContent.trim(); }
        const wrap = el.closest('label, .form-group, .field, tr, div');
        const l = wrap?.querySelector('label, th, .label');
        return (l?.textContent || el.name || el.id || '').replace(/\s+/g, ' ').trim();
      };
      doc.querySelectorAll('form input, form textarea, form select').forEach((el) => {
        const type = (el.getAttribute('type') || el.tagName).toLowerCase();
        if (['password', 'submit', 'button', 'file', 'image', 'reset'].includes(type)) return;
        if (/token|csrf|nonce|captcha/i.test(el.name || '')) return;
        let value;
        if (el.tagName === 'SELECT') value = [...el.selectedOptions].map((o) => o.textContent.trim()).join(', ');
        else if (el.tagName === 'TEXTAREA') value = el.textContent;
        else if (type === 'checkbox' || type === 'radio') { if (!el.hasAttribute('checked')) return; value = el.value || 'on'; }
        else value = el.getAttribute('value') || '';
        const key = el.name || el.id || labelFor(el);
        if (!key) return;
        const k = fields[key] ? `${key} (${Object.keys(fields).length})` : key;
        fields[k] = { label: labelFor(el), type, value };
      });
      const heading = doc.querySelector('h1, h2, .page-title')?.textContent.trim() || '';
      records.push({ edit_url: url, list_row: listLabel, admin_heading: heading, http_status: status, fields });
      console.log(`[${i}/${editLinks.size}] ${heading || url} — ${Object.keys(fields).length} fields`);
    } catch (e) {
      records.push({ edit_url: url, list_row: listLabel, error: String(e) });
      console.warn(`[${i}/${editLinks.size}] failed: ${url}`, e);
    }
    await sleep(DELAY_MS);
  }

  // ---- 3. Download JSON + CSV ----
  const download = (name, content, type) => {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([content], { type }));
    a.download = name; document.body.appendChild(a); a.click(); a.remove();
  };
  download('tbi-cms-export.json', JSON.stringify({ exported_at: new Date().toISOString(), source: location.href, records }, null, 2), 'application/json');

  const allKeys = [...new Set(records.flatMap((r) => Object.keys(r.fields || {})))];
  const esc = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`;
  const rows = [['edit_url', 'list_row', 'admin_heading', ...allKeys].map(esc).join(',')];
  records.forEach((r) => rows.push([r.edit_url, r.list_row, r.admin_heading,
    ...allKeys.map((k) => { const f = r.fields?.[k]; return f ? (/<[a-z][\s\S]*>/i.test(f.value) ? text(f.value) : f.value) : ''; })].map(esc).join(',')));
  download('tbi-cms-export.csv', '﻿' + rows.join('\n'), 'text/csv');

  console.log(`Done. Exported ${records.length} pages.`);
})();
