from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# Ensure repo root is on sys.path when running the script directly (e.g., python dev/app.py)
# This helps importing dev.* packages when Python sets sys.path[0] to the script directory.
import os, sys
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)


@app.route('/')
def index():
    return render_template_string('''
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Vinayaka File Works</title>
        <style>
          :root {
            --bg: #f4efe7;
            --card: #fffdf9;
            --primary: #7c4a2d;
            --primary-dark: #4a2c1b;
            --accent: #d9b98b;
            --muted: #6a5a50;
            --text: #2a1b17;
            --line: #e8ddcf;
            --danger: #b42318;
          }
          * { box-sizing: border-box; }
          body {
            margin: 0;
            font-family: Arial, Helvetica, sans-serif;
            background: linear-gradient(180deg, #f8f3ee 0%, #efe5d8 100%);
            color: var(--text);
          }
          a { color: inherit; text-decoration: none; }
          .container {
            max-width: 1180px;
            margin: 0 auto;
            padding: 24px 20px 60px;
          }
          header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 0 18px;
            border-bottom: 1px solid var(--line);
          }
          .brand {
            font-weight: 700;
            font-size: 1.5rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: var(--primary-dark);
          }
          nav {
            display: flex;
            gap: 24px;
            color: var(--muted);
            font-size: 0.96rem;
          }
          .nav-btn {
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 999px;
            padding: 12px 18px;
            font-weight: 600;
            cursor: pointer;
          }
          .hero {
            display: grid;
            grid-template-columns: 1.2fr 0.8fr;
            gap: 32px;
            align-items: center;
            padding: 52px 0 32px;
          }
          .eyebrow {
            display: inline-block;
            background: #f2dfbf;
            color: var(--primary-dark);
            padding: 8px 12px;
            border-radius: 999px;
            font-size: 0.74rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-weight: 700;
          }
          h1 {
            font-size: clamp(2.5rem, 5vw, 5rem);
            margin: 16px 0;
            line-height: 0.96;
            letter-spacing: -0.04em;
          }
          .lead {
            font-size: 1.1rem;
            color: var(--muted);
            line-height: 1.7;
            max-width: 620px;
          }
          .cta-row {
            display: flex;
            gap: 16px;
            margin-top: 28px;
            flex-wrap: wrap;
          }
          .primary,
          .secondary {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 999px;
            padding: 14px 22px;
            font-weight: 700;
          }
          .primary {
            background: var(--primary);
            color: white;
          }
          .secondary {
            border: 1px solid var(--line);
            background: rgba(255,255,255,0.4);
            color: var(--text);
          }
          .hero-card {
            background: rgba(255,255,255,0.55);
            border: 1px solid rgba(124,74,45,0.14);
            border-radius: 28px;
            box-shadow: 0 30px 60px rgba(70, 48, 36, 0.08);
            padding: 20px;
          }
          .product-box {
            border-radius: 22px;
            overflow: hidden;
            background: linear-gradient(135deg, #efe1c8 0%, #f8f3ef 100%);
            border: 1px solid var(--line);
          }
          .product-image {
            height: 250px;
            background: linear-gradient(135deg, #c79863 0%, #9a5c38 100%);
            position: relative;
          }
          .product-image::before {
            content: "";
            position: absolute;
            inset: 22% 18% 24% 18%;
            border-radius: 16px;
            background: rgba(255,255,255,0.28);
            border: 1px solid rgba(255,255,255,0.7);
          }
          .product-meta {
            padding: 18px 18px 22px;
          }
          .price-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 12px;
          }
          .chips {
            display: flex;
            gap: 12px;
            margin-top: 28px;
            flex-wrap: wrap;
          }
          .chip {
            border: 1px solid var(--line);
            background: rgba(255,255,255,0.55);
            border-radius: 999px;
            padding: 10px 14px;
            color: var(--muted);
            font-size: 0.9rem;
          }
          .section {
            padding-top: 26px;
          }
          .section-header {
            display: flex;
            justify-content: space-between;
            align-items: end;
            margin-bottom: 18px;
          }
          .section-header h2 {
            margin: 0;
            font-size: 2rem;
          }
          .grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 22px;
          }
          .card {
            background: rgba(255,255,255,0.65);
            border: 1px solid var(--line);
            border-radius: 22px;
            padding: 20px;
          }
          .mini {
            width: 56px;
            height: 56px;
            border-radius: 18px;
            background: #f3e0c1;
            margin-bottom: 14px;
          }
          .card h3 {
            margin: 0 0 8px;
            font-size: 1.25rem;
          }
          .card p {
            margin: 0;
            color: var(--muted);
            line-height: 1.6;
          }
          .quote-form {
            background: rgba(255,255,255,0.7);
            border: 1px solid var(--line);
            border-radius: 24px;
            padding: 24px;
            box-shadow: 0 18px 40px rgba(70, 48, 36, 0.06);
          }
          .form-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 18px;
          }
          .field {
            display: flex;
            flex-direction: column;
            gap: 8px;
          }
          .field label {
            color: var(--primary-dark);
            font-size: 0.9rem;
            font-weight: 700;
          }
          .field input, .field select, .field textarea {
            width: 100%;
            border: 1px solid var(--line);
            background: rgba(255,255,255,0.8);
            border-radius: 12px;
            padding: 12px 14px;
            font: inherit;
            color: var(--text);
          }
          .field textarea {
            min-height: 120px;
            resize: vertical;
          }
          .field-error {
            min-height: 1.1em;
            color: var(--danger);
            font-size: 0.9rem;
            margin-top: 2px;
          }
          .input-error {
            border-color: var(--danger) !important;
            outline-color: var(--danger) !important;
          }
          .submit-row {
            margin-top: 20px;
            display: flex;
            align-items: center;
            gap: 16px;
            flex-wrap: wrap;
          }
          .submit-btn {
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 999px;
            padding: 13px 22px;
            font-weight: 700;
            cursor: pointer;
          }
          .form-message {
            margin: 0;
            font-size: 0.95rem;
          }
          .form-message.success {
            color: #0d7a3a;
          }
          .form-message.error {
            color: #a62b2b;
          }
          /* VNK-2: product search and filter */
          .search-block { margin-top: 28px; }
          .search-field { display: flex; flex-direction: column; gap: 8px; }
          .search-field label, .filter-field label {
            color: var(--primary-dark); font-size: 0.9rem; font-weight: 700;
          }
          .search-block input[type="search"], .search-block select {
            width: 100%; min-height: 44px; border: 1px solid var(--line);
            background: rgba(255,255,255,0.8); border-radius: 12px;
            padding: 10px 14px; font: inherit; color: var(--text);
          }
          .filters-panel { margin-top: 14px; }
          .filters-panel summary {
            cursor: pointer; min-height: 44px; display: flex; align-items: center;
            font-weight: 700; color: var(--primary-dark);
          }
          .filters-row {
            display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)) auto;
            gap: 16px; align-items: end; margin-top: 8px;
          }
          .filter-field { display: flex; flex-direction: column; gap: 8px; }
          .clear-btn {
            min-height: 44px; background: transparent; color: var(--primary-dark);
            border: 1px solid var(--primary); border-radius: 999px;
            padding: 10px 18px; font-weight: 700; cursor: pointer;
          }
          .results-count { margin: 16px 0 10px; color: var(--muted); min-height: 1.4em; }
          .product-results {
            display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 22px;
          }
          .product-results .card { min-width: 0; overflow-wrap: anywhere; }
          .product-results .card h3 { margin-bottom: 6px; }
          .product-results .meta { font-size: 0.9rem; margin-top: 6px; }
          .product-results .price { margin-top: 10px; font-weight: 700; color: var(--primary-dark); }
          .no-results, .search-error {
            padding: 24px; border: 1px dashed var(--line); border-radius: 22px;
            background: rgba(255,255,255,0.55); text-align: center;
          }
          .no-results p { margin: 6px 0 14px; color: var(--muted); }
          .search-error { color: var(--danger); border-color: var(--danger); }
          .search-block [hidden] { display: none !important; }
          footer {
            margin-top: 50px;
            padding-top: 24px;
            border-top: 1px solid var(--line);
            color: var(--muted);
            font-size: 0.9rem;
          }
          @media (max-width: 820px) {
            .hero, .grid { grid-template-columns: 1fr; }
            .filters-row { grid-template-columns: 1fr; }
            .product-results { grid-template-columns: 1fr; }
            .clear-btn { width: 100%; }
            nav { display: none; }
            header { padding-top: 10px; }
          }
        </style>
      </head>
      <body>
        <div class="container">
          <header>
            <div class="brand">Vinayaka File Works</div>
            <nav>
              <a href="#products">Products</a>
              <a href="#services">Services</a>
              <a href="#about">About</a>
              <a href="#contact">Contact</a>
            </nav>
            <a class="nav-btn" href="#quote-form">Get a quote</a>
          </header>

          <section class="hero">
            <div>
              <span class="eyebrow">Paper & printing solutions</span>
              <h1>Print smarter. Deliver better.</h1>
              <p class="lead">
                Vinayaka File Works helps businesses and families with custom stationery,
                packaging, printing, and office essentials—delivered with reliable service and quick turnaround.
              </p>
              <div class="cta-row">
                <a class="primary" href="#products">Shop products</a>
                <a class="secondary" href="#services">Explore services</a>
              </div>
              <div class="chips" style="margin-top: 18px;">
                <span class="chip">No. 42, Market Road, Bengaluru, Karnataka 560001</span>
                <span class="chip">+91 98765 43210</span>
              </div>
              <div class="chips">
                <span class="chip">Bulk printing</span>
                <span class="chip">Office supplies</span>
                <span class="chip">Custom stationery</span>
              </div>
            </div>

            <div class="hero-card">
              <div class="product-box">
                <div class="product-image"></div>
                <div class="product-meta">
                  <strong>Premium Office Pack</strong>
                  <div class="price-row">
                    <span>Starter bundle</span>
                    <strong>₹1,499</strong>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section class="section" id="products">
            <div class="section-header">
              <h2>Popular products</h2>
              <a href="#">View all →</a>
            </div>
            <div class="grid">
              <div class="card">
                <div class="mini"></div>
                <h3>Printed Forms</h3>
                <p>Custom invoice books, registers, and office forms designed to keep daily operations efficient.</p>
              </div>
              <div class="card">
                <div class="mini"></div>
                <h3>Packaging Kits</h3>
                <p>Professional packaging and business stationery for retail, gifting, and courier-ready deliveries.</p>
              </div>
              <div class="card">
                <div class="mini"></div>
                <h3>Files & Folders</h3>
                <p>Durable file folders, project tags, and archival materials built for everyday use.</p>
              </div>
            </div>

            <div class="search-block" id="product-search">
              <div class="search-field">
                <label for="product-search-input">Search products</label>
                <input id="product-search-input" type="search" maxlength="100" autocomplete="off"
                       placeholder="Search by name, material, category or SKU">
              </div>
              <details class="filters-panel" id="filters-panel">
                <summary>Filters</summary>
                <div class="filters-row">
                  <div class="filter-field">
                    <label for="filter-material">Material</label>
                    <select id="filter-material"><option value="">All</option></select>
                  </div>
                  <div class="filter-field">
                    <label for="filter-size">Size</label>
                    <select id="filter-size"><option value="">All</option></select>
                  </div>
                  <div class="filter-field">
                    <label for="filter-customization">Customization</label>
                    <select id="filter-customization"><option value="">All</option></select>
                  </div>
                  <button type="button" class="clear-btn" id="clear-filters">Clear All Filters</button>
                </div>
              </details>
              <p class="results-count" id="results-count" aria-live="polite"></p>
              <div class="search-error" id="search-error" role="alert" hidden>Unable to load products. Please try again.</div>
              <div class="no-results" id="no-results" hidden>
                <strong>No products found</strong>
                <p>Try a different search term or clear your filters.</p>
                <button type="button" class="clear-btn" id="no-results-clear">Clear All Filters</button>
              </div>
              <div class="product-results" id="product-grid"></div>
            </div>

            <script>
              // VNK-2: product search + filters. All API data is rendered via textContent only.
              (function () {
                const input = document.getElementById('product-search-input');
                const selMaterial = document.getElementById('filter-material');
                const selSize = document.getElementById('filter-size');
                const selCustom = document.getElementById('filter-customization');
                const clearBtn = document.getElementById('clear-filters');
                const clearBtn2 = document.getElementById('no-results-clear');
                const countEl = document.getElementById('results-count');
                const grid = document.getElementById('product-grid');
                const noResults = document.getElementById('no-results');
                const errorEl = document.getElementById('search-error');
                const panel = document.getElementById('filters-panel');
                if (!input || !grid || !panel) return;

                const LIMIT = 100;
                const DEBOUNCE_MS = 250;
                let timer = null;
                let controller = null;

                // F-08: open by default on wide viewports, collapsed on narrow ones.
                const mq = window.matchMedia('(max-width: 820px)');
                function syncPanel() { panel.open = !mq.matches; }
                syncPanel();
                if (mq.addEventListener) mq.addEventListener('change', syncPanel);
                else if (mq.addListener) mq.addListener(syncPanel);

                function el(tag, className, text) {
                  const n = document.createElement(tag);
                  if (className) n.className = className;
                  if (text !== undefined && text !== null) n.textContent = text;
                  return n;
                }

                function fillSelect(select, values) {
                  const keep = select.value;
                  while (select.options.length > 1) select.remove(1);
                  (values || []).forEach(function (v) {
                    const o = document.createElement('option');
                    o.value = v;
                    o.textContent = v;
                    select.appendChild(o);
                  });
                  select.value = keep;
                }

                function renderCard(p) {
                  const card = el('div', 'card');
                  card.setAttribute('data-sku', p.sku || '');
                  card.appendChild(el('div', 'mini'));
                  card.appendChild(el('h3', null, p.title));
                  if (p.description) card.appendChild(el('p', null, p.description));
                  const bits = [];
                  if (p.category) bits.push('Category: ' + p.category);
                  if (p.material) bits.push('Material: ' + p.material);
                  if (p.sizes && p.sizes.length) bits.push('Sizes: ' + p.sizes.join(', '));
                  if (p.customizations && p.customizations.length) bits.push('Customization: ' + p.customizations.join(', '));
                  bits.forEach(function (b) { card.appendChild(el('p', 'meta', b)); });
                  card.appendChild(el('div', 'price', '₹' + Number(p.price || 0).toFixed(2)));
                  return card;
                }

                function render(data) {
                  errorEl.hidden = true;
                  while (grid.firstChild) grid.removeChild(grid.firstChild);
                  const items = data.items || [];
                  if (!items.length) {
                    noResults.hidden = false;
                    countEl.textContent = '0 products';
                    return;
                  }
                  noResults.hidden = true;
                  items.forEach(function (p) { grid.appendChild(renderCard(p)); });
                  countEl.textContent = data.total > items.length
                    ? 'Showing ' + items.length + ' of ' + data.total
                    : items.length + (items.length === 1 ? ' product' : ' products');
                }

                function showError() {
                  while (grid.firstChild) grid.removeChild(grid.firstChild);
                  noResults.hidden = true;
                  countEl.textContent = '';
                  errorEl.hidden = false;
                }

                async function runSearch() {
                  if (controller) controller.abort();
                  controller = new AbortController();
                  const mine = controller;
                  const params = new URLSearchParams();
                  const q = input.value.trim();
                  if (q) params.set('q', q);
                  if (selMaterial.value) params.set('material', selMaterial.value);
                  if (selSize.value) params.set('size', selSize.value);
                  if (selCustom.value) params.set('customization', selCustom.value);
                  params.set('limit', String(LIMIT));
                  try {
                    const resp = await fetch('/api/products/search?' + params.toString(), { signal: mine.signal });
                    if (!resp.ok) throw new Error('bad status');
                    const data = await resp.json();
                    if (mine !== controller) return;
                    render(data);
                  } catch (e) {
                    if (e && e.name === 'AbortError') return;
                    if (mine !== controller) return;
                    showError();
                  }
                }

                function clearAll() {
                  input.value = '';
                  selMaterial.value = '';
                  selSize.value = '';
                  selCustom.value = '';
                  runSearch();
                }

                async function loadFilters() {
                  try {
                    const resp = await fetch('/api/products/filters');
                    if (!resp.ok) return;
                    const f = await resp.json();
                    fillSelect(selMaterial, f.materials);
                    fillSelect(selSize, f.sizes);
                    fillSelect(selCustom, f.customizations);
                  } catch (e) { /* filters stay at "All" */ }
                }

                input.addEventListener('input', function () {
                  clearTimeout(timer);
                  timer = setTimeout(runSearch, DEBOUNCE_MS);
                });
                input.addEventListener('keydown', function (evt) {
                  if (evt.key === 'Enter') {
                    evt.preventDefault();
                    clearTimeout(timer);
                    runSearch();
                  }
                });
                [selMaterial, selSize, selCustom].forEach(function (s) {
                  s.addEventListener('change', function () { clearTimeout(timer); runSearch(); });
                });
                clearBtn.addEventListener('click', clearAll);
                if (clearBtn2) clearBtn2.addEventListener('click', clearAll);

                loadFilters().then(runSearch);
              })();
            </script>
          </section>

          <section class="section" id="services">
            <div class="section-header">
              <h2>Why customers choose us</h2>
            </div>
            <div class="grid">
              <div class="card">
                <div class="mini"></div>
                <h3>Fast turnaround</h3>
                <p>Quick production timelines for urgent print jobs and repeat office supply orders.</p>
              </div>
              <div class="card">
                <div class="mini"></div>
                <h3>Quality assurance</h3>
                <p>Careful print checks, premium paper selection, and a focus on clean finishing details.</p>
              </div>
              <div class="card">
                <div class="mini"></div>
                <h3>Flexible support</h3>
                <p>Support for local businesses, schools, shops, and event organizers with tailored order planning.</p>
              </div>
            </div>
          </section>

          <section class="section" id="quote-form">
            <div class="section-header">
              <h2>Request a quote</h2>
            </div>
            <form id="quote-form-element" class="quote-form" novalidate>
              <div class="form-grid">
                <div class="field">
                  <label for="name">Name *</label>
                  <input id="name" name="name" type="text" required placeholder="Enter your full name">
                  <div class="field-error" id="err-name"></div>
                </div>
                <div class="field">
                  <label for="company">Company / Organization</label>
                  <input id="company" name="company" type="text" placeholder="Your organization name">
                  <div class="field-error" id="err-company"></div>
                </div>
                <div class="field">
                  <label for="mobile_number">Mobile Number *</label>
                  <input id="mobile_number" name="mobile_number" type="tel" required placeholder="+91 98765 43210">
                  <div class="field-error" id="err-mobile_number"></div>
                </div>
                <div class="field">
                  <label for="email">Email</label>
                  <input id="email" name="email" type="email" placeholder="you@example.com">
                  <div class="field-error" id="err-email"></div>
                </div>
                <div class="field">
                  <label for="product_category">Product / Category *</label>
                  <input id="product_category" name="product_category" type="text" required placeholder="e.g. Office stationery">
                  <div class="field-error" id="err-product_category"></div>
                </div>
                <div class="field">
                  <label for="required_quantity">Required Quantity</label>
                  <input id="required_quantity" name="required_quantity" type="text" placeholder="e.g. 250 units">
                  <div class="field-error" id="err-required_quantity"></div>
                </div>
                <div class="field" style="grid-column: 1 / -1;">
                  <label for="customization_requirements">Customization / Requirements</label>
                  <textarea id="customization_requirements" name="customization_requirements" placeholder="Tell us about your requirements, materials, printing, or sizing preferences."></textarea>
                  <div class="field-error" id="err-customization_requirements"></div>
                </div>
                <div class="field">
                  <label for="preferred_contact_method">Preferred Contact Method</label>
                  <select id="preferred_contact_method" name="preferred_contact_method">
                    <option value="Call">Call</option>
                    <option value="WhatsApp">WhatsApp</option>
                    <option value="Email">Email</option>
                  </select>
                  <div class="field-error" id="err-preferred_contact_method"></div>
                </div>
                <div class="field" style="grid-column: 1 / -1;">
                  <label for="additional_message">Additional Message</label>
                  <textarea id="additional_message" name="additional_message" placeholder="Add any additional details or timelines."></textarea>
                  <div class="field-error" id="err-additional_message"></div>
                </div>
              </div>
              <div class="submit-row">
                <button class="submit-btn" type="submit">Send enquiry</button>
                <p id="quote-message" class="form-message" aria-live="polite"></p>
              </div>
            </form>

            <script>
              // VNK-VNK-2-ENH-001: client-side validation + inline errors for quote form.
              (function () {
                const form = document.getElementById('quote-form-element');
                const message = document.getElementById('quote-message');
                if (!form || !message) return;

                const PHONE_MIN_LEN = 10;
                const PHONE_MAX_LEN = 15;
                const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

                function setMessage(text, kind) {
                  message.textContent = text || '';
                  message.classList.remove('success', 'error');
                  if (kind) message.classList.add(kind);
                }

                function fieldEl(fieldId) {
                  return document.getElementById(fieldId);
                }

                function errEl(fieldId) {
                  return document.getElementById('err-' + fieldId);
                }

                function setFieldError(fieldId, msg) {
                  const el = fieldEl(fieldId);
                  const er = errEl(fieldId);
                  if (er) er.textContent = msg || '';
                  if (el) el.classList.add('input-error');
                }

                function clearFieldError(fieldId) {
                  const el = fieldEl(fieldId);
                  const er = errEl(fieldId);
                  if (er) er.textContent = '';
                  if (el) el.classList.remove('input-error');
                }

                function clearAllErrors() {
                  const ids = [
                    'name',
                    'company',
                    'mobile_number',
                    'email',
                    'product_category',
                    'required_quantity',
                    'customization_requirements',
                    'preferred_contact_method',
                    'additional_message'
                  ];
                  ids.forEach(clearFieldError);
                }

                function normalizePhone(value) {
                  return (value || '').replace(/[\s-]/g, '').trim();
                }

                function validateRequired(fieldId, label) {
                  const el = fieldEl(fieldId);
                  const val = (el && el.value ? el.value : '').trim();
                  if (!val) {
                    setFieldError(fieldId, (label || 'This field') + ' is required.');
                    return false;
                  }
                  return true;
                }

                function validateEmail(fieldId) {
                  const el = fieldEl(fieldId);
                  const raw = (el && el.value ? el.value : '').trim();
                  if (!raw) return true; // optional
                  if (!EMAIL_RE.test(raw)) {
                    setFieldError(fieldId, 'Please enter a valid email address.');
                    return false;
                  }
                  return true;
                }

                function validatePhone(fieldId) {
                  const el = fieldEl(fieldId);
                  const raw = (el && el.value ? el.value : '').trim();
                  const normalized = normalizePhone(raw);
                  if (!normalized) {
                    setFieldError(fieldId, 'Mobile number is required.');
                    return false;
                  }
                  if (!/^\d+$/.test(normalized)) {
                    setFieldError(fieldId, 'Mobile number must contain digits only.');
                    return false;
                  }
                  if (normalized.length < PHONE_MIN_LEN || normalized.length > PHONE_MAX_LEN) {
                    setFieldError(fieldId, `Mobile number must be ${PHONE_MIN_LEN}–${PHONE_MAX_LEN} digits.`);
                    return false;
                  }
                  return true;
                }

                function validateForm() {
                  clearAllErrors();

                  const invalidIds = [];

                  if (!validateRequired('name', 'Name')) invalidIds.push('name');
                  if (!validatePhone('mobile_number')) invalidIds.push('mobile_number');
                  if (!validateEmail('email')) invalidIds.push('email');
                  if (!validateRequired('product_category', 'Product / Category')) invalidIds.push('product_category');

                  return {
                    ok: invalidIds.length === 0,
                    firstInvalid: invalidIds.length ? invalidIds[0] : null
                  };
                }

                // Clear error when user edits a field.
                form.addEventListener('input', function (evt) {
                  const t = evt.target;
                  if (!t || !t.id) return;
                  clearFieldError(t.id);
                });

                form.addEventListener('change', function (evt) {
                  const t = evt.target;
                  if (!t || !t.id) return;
                  clearFieldError(t.id);
                });

                form.addEventListener('submit', async function (evt) {
                  evt.preventDefault();

                  const res = validateForm();
                  if (!res.ok) {
                    setMessage('Please fix the highlighted fields and try again.', 'error');
                    const first = res.firstInvalid ? fieldEl(res.firstInvalid) : null;
                    if (first && typeof first.focus === 'function') first.focus();
                    return; // IMPORTANT: do not send request
                  }

                  setMessage('Sending...', '');

                  try {
                    const formData = new FormData(form);
                    const payload = {};
                    for (const [k, v] of formData.entries()) payload[k] = v;

                    const resp = await fetch('/api/quote-enquiries', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify(payload)
                    });

                    const data = await resp.json().catch(() => ({}));
                    if (!resp.ok) {
                      setMessage(data.error || 'Unable to submit request. Please try again.', 'error');
                      return;
                    }

                    setMessage('Thank you! Your enquiry has been submitted.', 'success');
                    form.reset();
                    clearAllErrors();
                  } catch (e) {
                    setMessage('Unable to submit request. Please try again.', 'error');
                  }
                });
              })();
            </script>
          </section>

          <footer id="contact">
            Vinayaka File Works • Office stationery, printing, and business essentials
          </footer>
        </div>
      </body>
    </html>
    ''')


# Register API blueprints if available (register individually so one failing import doesn't disable others)
for _mod in ['products', 'cart', 'orders', 'admin', 'invoices', 'quote_requests']:
    try:
        if _mod == 'products':
            from dev.api.products import products_bp as bp
        elif _mod == 'cart':
            from dev.api.cart import cart_bp as bp
        elif _mod == 'orders':
            from dev.api.orders import orders_bp as bp
        elif _mod == 'admin':
            from dev.api.admin import admin_bp as bp
        elif _mod == 'invoices':
            from dev.api.invoices import invoices_bp as bp
        elif _mod == 'quote_requests':
            from dev.api.quote_requests import quote_bp as bp
        else:
            bp = None
        if bp is not None:
            app.register_blueprint(bp)
    except Exception as e:
        # Log and continue; tests may run in environments where DB/backends are missing
        try:
            app.logger.warning(f"Could not import dev.api.{_mod}: {e}")
        except Exception:
            pass


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
