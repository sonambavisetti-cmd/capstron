"""Legacy Flask entrypoint (deprecated).

VNK-VNK-1-ENH-001
This repository previously had two competing storefront "home" experiences:
- FastAPI monolith (canonical) running on :8000
- Flask app (legacy) running on :5000

To avoid end-user confusion and enforce a single canonical storefront entry,
Flask GET / redirects users to the FastAPI storefront UI.

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
          footer {
            margin-top: 50px;
            padding-top: 24px;
            border-top: 1px solid var(--line);
            color: var(--muted);
            font-size: 0.9rem;
          }
          @media (max-width: 820px) {
            .hero, .grid { grid-template-columns: 1fr; }
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

Safety:
- If STOREFRONT_BASE_URL is unset/invalid, default to localhost.
- Always redirect to <base>/storefront/.
"""

from __future__ import annotations

import os
import sys
from urllib.parse import urlparse

from flask import Flask, redirect

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

    parsed = urlparse(base)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        # Fall back to safe local default.
        base = "http://localhost:8000"

    return base.rstrip("/") + "/storefront/"


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



# Register API blueprints if available (register individually so one failing import doesn't disable others)
for _mod in ["products", "cart", "orders", "admin", "invoices", "quote_requests"]:
    try:
        if _mod == "products":
            from dev.api.products import products_bp as bp
        elif _mod == "cart":
            from dev.api.cart import cart_bp as bp
        elif _mod == "orders":
            from dev.api.orders import orders_bp as bp
        elif _mod == "admin":
            from dev.api.admin import admin_bp as bp
        elif _mod == "invoices":
            from dev.api.invoices import invoices_bp as bp
        elif _mod == "quote_requests":
            from dev.api.quote_requests import quote_bp as bp
        else:
            bp = None

        if bp is not None:
            app.register_blueprint(bp)
    except Exception:
        pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
