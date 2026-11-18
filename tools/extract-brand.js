/*
 * TBI brand extractor — READ-ONLY.
 * Captures the logo, the theme's fonts and the theme's colors exactly as the live site renders them.
 *
 * How to use:
 *   1. Open https://www.tbiport.org/ (the public homepage; logging out first gives the cleanest result)
 *   2. Open the Console (Ctrl+Shift+J / Cmd+Option+J), type  allow pasting  + Enter if asked
 *   3. Paste this file, press Enter. One file downloads: tbi-brand.json
 *   4. If the console says the logo could not be embedded, also right-click the logo > "Save image as…"
 */
(async () => {
  const out = { url: location.href, captured_at: new Date().toISOString() };
  const cs = (el) => getComputedStyle(el);
  const visible = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const pick = (sel) => [...document.querySelectorAll(sel)].filter(visible);

  // ---- Logo ----
  const logoCandidates = [
    ...pick('header img, #header img, .header img, .logo img, #logo img, [class*="logo" i] img, img[src*="logo" i], img[alt*="logo" i]'),
  ];
  const bgLogos = pick('[class*="logo" i], [id*="logo" i]').map((el) => cs(el).backgroundImage).filter((b) => b && b !== 'none');
  out.logo = { images: [...new Set(logoCandidates.map((i) => i.currentSrc || i.src))], background_images: [...new Set(bgLogos)], embedded: [] };
  for (const src of out.logo.images.slice(0, 3)) {
    try {
      const blob = await (await fetch(src)).blob();
      const dataUrl = await new Promise((res) => { const fr = new FileReader(); fr.onload = () => res(fr.result); fr.readAsDataURL(blob); });
      out.logo.embedded.push({ src, type: blob.type, bytes: blob.size, dataUrl });
    } catch (e) { console.warn('Could not embed logo (save it manually):', src); }
  }
  // inline SVG logos
  out.logo.inline_svg = pick('header svg, .logo svg, #logo svg').slice(0, 2).map((s) => s.outerHTML.slice(0, 50000));

  // ---- Fonts ----
  const sample = { body: 'body', h1: 'h1', h2: 'h2', h3: 'h3', nav_link: 'nav a, .nav a, #nav a, .menu a, header a', button: 'button, .btn, .button, a.button, input[type=submit]', paragraph: 'p', footer: 'footer, #footer, .footer' };
  out.typography = {};
  for (const [k, sel] of Object.entries(sample)) {
    const el = pick(sel)[0];
    if (!el) continue;
    const s = cs(el);
    out.typography[k] = { selector_hit: el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).trim().split(/\s+/).join('.') : ''), fontFamily: s.fontFamily, fontSize: s.fontSize, fontWeight: s.fontWeight, lineHeight: s.lineHeight, letterSpacing: s.letterSpacing, textTransform: s.textTransform, color: s.color };
  }
  await document.fonts.ready;
  out.loaded_fonts = [...new Set([...document.fonts].filter((f) => f.status === 'loaded').map((f) => `${f.family.replace(/"/g, '')} ${f.weight} ${f.style}`))];
  out.font_stylesheets = [...document.querySelectorAll('link[rel="stylesheet"]')].map((l) => l.href).filter((h) => /font|typekit|googleapis/i.test(h));

  // ---- Colors ----
  const roles = { top_bar: '.top_links_wrapper, .topbar, .top-bar, #topbar', header: 'header, #header, .header', nav: 'nav, .nav, #nav, .menu', nav_link: 'nav a, .nav a, #nav a, .menu a', link: '#maincontent a, main a, .content a', h1: 'h1', h2: 'h2', button: 'button, .btn, .button, a.button, .action-button', footer: 'footer, #footer, .footer', body: 'body' };
  out.color_roles = {};
  for (const [k, sel] of Object.entries(roles)) {
    const el = pick(sel)[0];
    if (!el) continue;
    const s = cs(el);
    out.color_roles[k] = { color: s.color, background: s.backgroundColor, backgroundImage: s.backgroundImage.slice(0, 300), border: s.borderTopColor };
  }
  const tally = { text: {}, background: {} };
  for (const el of pick('body *')) {
    const s = cs(el), r = el.getBoundingClientRect();
    const bg = s.backgroundColor;
    if (bg && bg !== 'rgba(0, 0, 0, 0)') tally.background[bg] = (tally.background[bg] || 0) + Math.round(r.width * r.height / 100);
    const own = [...el.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent.trim()).join('');
    if (own) tally.text[s.color] = (tally.text[s.color] || 0) + own.length;
  }
  const top = (o) => Object.entries(o).sort((a, b) => b[1] - a[1]).slice(0, 15);
  out.color_tally = { text: top(tally.text), background: top(tally.background) };
  const rootStyle = cs(document.documentElement);
  out.css_variables = {};
  for (const sheet of document.styleSheets) {
    try { for (const rule of sheet.cssRules) if (rule.selectorText === ':root') for (const p of rule.style) if (p.startsWith('--')) out.css_variables[p] = rootStyle.getPropertyValue(p).trim(); } catch (e) {}
  }

  // ---- Theme CSS (for exact values) ----
  out.stylesheets = [];
  for (const sheet of document.styleSheets) {
    const entry = { href: sheet.href };
    try { entry.css = [...sheet.cssRules].map((r) => r.cssText).join('\n').slice(0, 400000); } catch (e) { entry.css = null; }
    out.stylesheets.push(entry);
  }

  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([JSON.stringify(out, null, 1)], { type: 'application/json' }));
  a.download = 'tbi-brand.json'; document.body.appendChild(a); a.click(); a.remove();
  console.log('Done. Logo images found:', out.logo.images, '| fonts:', out.loaded_fonts);
})();
