# Handoff Report — Frontend & Templates Survey

**Task**: Comprehensive survey of Frontend & Templates architecture for dead code analysis  
**Working Directory**: `C:\Users\david\Desktop\Gestionale_Macelleria\.agents\explorer_frontend_survey`  
**Target Report**: `frontend_survey.md`  
**Date**: 2026-08-20  

---

## 1. Observation

Direct observations from codebase inspection:

1. **Jinja2 Templates in `templates/`**:
   - `templates/index.html`: Rendered at `app.py:191` via `render_template('index.html', catalogo=catalogo)`. Includes `header.html` (line 1) and `footer.html` (line 77).
   - `templates/carico.html`: Rendered at `app.py:211` via `render_template('carico.html', articoli_per_categoria=articoli_per_categoria)`. Includes `header.html` (line 4) and `footer.html` (line 78). Defines `{% set active_page = 'carico' %}`, `{% set show_search = false %}`, `{% set page_title = 'Carico Merce - Gestionale Macelleria' %}` on lines 1–3.
   - `templates/magazzino.html`: Rendered at `app.py:276` via `render_template('magazzino.html', giacenze=giacenze)`. Includes `header.html` (line 4) and `footer.html` (line 62). Defines `{% set active_page = 'magazzino' %}`, `{% set show_search = false %}`, `{% set page_title = 'Magazzino - Gestionale Macelleria' %}` on lines 1–3.
   - `templates/etichetta.html`: Rendered at `app.py:385` via `render_template('etichetta.html', preparato=preparato, ingredienti=", ".join(lista_ingredienti), allergeni=list(allergeni_set))`. Standalone HTML for thermal printing, loads JsBarcode 3.11.5 from CDN (line 8).
   - `templates/etichetta_taglio.html`: Rendered at `app.py:430` via `render_template('etichetta_taglio.html', taglio=taglio)`. Standalone HTML for beef traceability thermal printing, loads JsBarcode 3.11.5 from CDN (line 8).
   - `templates/header.html`: Included by `index.html`, `carico.html`, `magazzino.html`. Hardcodes `<title>Gestionale Macelleria</title>` (line 6); highlights nav tabs using `request.endpoint` (lines 34, 41, 48); renders `#searchInput` unconditionally (lines 66–69).
   - `templates/footer.html`: Included by `index.html`, `carico.html`, `magazzino.html`. Displays `{{ excel_filename }}` (injected via `@app.context_processor` at `app.py:27-31`); includes inline JS for filtering `.product-item` by `data-name` (lines 21–39); links `/static/js/status_monitor.js` (line 40).

2. **Static Assets in `static/`**:
   - `static/js/status_monitor.js`: 30 lines. Calls `fetch('/api/db_status')` (handled by `app.py:465`) on `DOMContentLoaded` and every 30s (`setInterval`), updating `#db-status-dot` and `#db-status-text`.

3. **React / TypeScript in `src/` & Build Tools**:
   - `src/main.tsx` (11 lines): React 19 root mounting `<App />` to `#root`.
   - `src/App.tsx` (83 lines): Static mockup card describing the Flask architecture.
   - `src/index.css` (2 lines): `@import "tailwindcss";`.
   - `vite.config.ts` (23 lines) & `tsconfig.json` (27 lines): Bundler & TS configuration.
   - Root `index.html`: Does not exist at repository root (Vite has no entry point).
   - `README.md:13`: Verbatim note stating `src/` is an automatic scaffolding from Google AI Studio and "non è l'applicazione reale".

4. **Node Dependencies in `package.json`**:
   - `@google/genai` (line 14): 0 references across repository.
   - `express` (line 21) & `@types/express` (line 33): 0 references across repository.
   - `dotenv` (line 22): 0 references in JS/TS.
   - `"clean": "rm -rf dist server.js"` (line 10): References nonexistent `server.js`.

---

## 2. Logic Chain

1. **Jinja2 Template Completeness**:
   - Each of the 7 `.html` files in `templates/` is directly accounted for: 5 are rendered via Flask's `render_template()` in `app.py`, and 2 (`header.html`, `footer.html`) are included via `{% include %}`.
   - Conclusion: There are **zero orphan HTML template files** in `templates/`.

2. **Template Variable Usage & Dead Variables**:
   - `carico.html` and `magazzino.html` define `active_page`, `show_search`, and `page_title`.
   - Inspection of `header.html` reveals that navigation highlighting uses `request.endpoint`, `<title>` is hardcoded, and the search bar is rendered without condition.
   - Conclusion: The variables `active_page`, `show_search`, and `page_title` in `carico.html` (lines 1–3) and `magazzino.html` (lines 1–3) are **dead/unused template variables**.

3. **Client-Side Search Behavior**:
   - The search filter in `footer.html` operates only on `.product-item` elements.
   - Only `index.html` contains `.product-item` elements.
   - Conclusion: The search bar rendered on `/carico` and `/magazzino` is visually present but functionally inoperable.

4. **Status of React / Vite Subsystem**:
   - The entire `src/` folder, `vite.config.ts`, `tsconfig.json`, `metadata.json`, and `package.json` form a detached prototype scaffold.
   - Flask does not serve static assets from `dist/` or `src/`, nor is there any build step in `app.py`.
   - Conclusion: `src/`, `vite.config.ts`, `tsconfig.json`, `metadata.json`, and unused npm dependencies (`@google/genai`, `express`, `dotenv`, `@types/express`, `tsx`) represent **dead scaffolding artifacts**.

---

## 3. Caveats

1. **AI Studio Environment**: If this repository is opened in Google AI Studio, `metadata.json` and `src/` may be used by the platform to display a preview container, even though the production app is purely Flask. Deletion should be deliberate depending on deployment target.
2. **CDN Resilience**: The application relies on external CDNs (Tailwind CSS, Google Fonts, JsBarcode). Offline functionality would require downloading these assets into `static/`.

---

## 4. Conclusion

- **Production UI Layer**: Fully functional, consisting of 7 Jinja2 templates, 1 static JS file (`status_monitor.js`), and CDN dependencies. All templates and endpoints are mapped 1-to-1 with Flask backend routes.
- **Dead Code Identified**:
  1. Unused Jinja variables (`active_page`, `show_search`, `page_title`) in `carico.html:1-3` and `magazzino.html:1-3`.
  2. Inoperable search input on `/carico` and `/magazzino`.
  3. Scaffolding React files (`src/main.tsx`, `src/App.tsx`, `src/index.css`, `vite.config.ts`, `tsconfig.json`, `metadata.json`).
  4. Dead npm dependencies (`@google/genai`, `express`, `dotenv`, `@types/express`, `tsx`) and dead script target `server.js` in `package.json`.

---

## 5. Verification Method

To independently verify these findings:

1. **Verify Template Inclusions and Render Calls**:
   - Check `app.py` lines 191 (`index.html`), 211 (`carico.html`), 276 (`magazzino.html`), 385 (`etichetta.html`), 430 (`etichetta_taglio.html`).
   - Check `templates/index.html` lines 1, 77 (`header.html`, `footer.html`).
   - Check `templates/carico.html` lines 4, 78 (`header.html`, `footer.html`).
   - Check `templates/magazzino.html` lines 4, 62 (`header.html`, `footer.html`).

2. **Verify Unused Variables in Header**:
   - Open `templates/header.html` and verify that `active_page`, `show_search`, and `page_title` are nowhere referenced.

3. **Verify Dead NPM Dependencies**:
   - Inspect `package.json` dependencies and search across `src/`, `templates/`, and `app.py` for `@google/genai`, `express`, or `server.js`.
