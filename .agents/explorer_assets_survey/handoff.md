# Handoff Report — Static Assets, Dependencies & Configuration Survey

**Agent**: `explorer_assets_survey`  
**Date**: 2026-08-20  
**Type**: Hard Handoff (Investigation Complete)  
**Deliverable File**: `C:\Users\david\Desktop\Gestionale_Macelleria\.agents\explorer_assets_survey\assets_survey.md`

---

## 1. Observation

1. **Static Files Directory (`static/`)**:
   - `static/` contains exactly 1 file: `static/js/status_monitor.js` (1,085 bytes, 30 lines).
   - `static/js/status_monitor.js` is imported in `templates/footer.html` (line 40: `<script src="{{ url_for('static', filename='js/status_monitor.js') }}" defer></script>`).
   - It references DOM element IDs `db-status-dot` (`templates/footer.html:4`) and `db-status-text` (`templates/footer.html:5`), and calls endpoint `fetch('/api/db_status')`.
   - In `app.py` lines 464–477, endpoint `@app.route('/api/db_status')` is defined and returns JSON `{"status": "ok"}` or `{"status": "error"}`.
   - There are 0 images (`.png`, `.jpg`, `.svg`, `.ico`), 0 local fonts (`.woff`), and 0 local stylesheets (`.css`) in `static/`.

2. **Template External Asset References**:
   - `templates/header.html` line 7 loads Tailwind CDN: `https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4`.
   - `templates/header.html` line 8 loads Google Font: `https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined...`.
   - `templates/etichetta.html` line 8 and `templates/etichetta_taglio.html` line 8 load JsBarcode CDN: `https://cdn.jsdelivr.net/npm/jsbarcode@3.11.5/dist/JsBarcode.all.min.js`.

3. **Node / NPM Configuration (`package.json`)**:
   - `package.json` line 14: `"@google/genai": "^2.4.0"` is declared, but 0 references/imports exist in the repository.
   - `package.json` line 21: `"express": "^4.21.2"` and line 33: `"@types/express": "^4.17.21"` are declared, but backend is Flask (`app.py`); express is never imported.
   - `package.json` line 22: `"dotenv": "^17.2.3"` is declared, but never imported in any JS/TS file (`app.py` uses python `python-dotenv`).
   - `package.json` line 30: `"tsx": "^4.21.0"` is declared in devDependencies, but no tsx command or script is used.
   - `package.json` line 27: `"autoprefixer": "^10.4.21"` is declared, but Tailwind v4 uses `@tailwindcss/vite` without autoprefixer config.
   - `package.json` lines 20 & 32: `"vite": "^6.2.3"` is declared in both `dependencies` and `devDependencies`.
   - `package.json` line 10: `"clean": "rm -rf dist server.js"` references `server.js`, which does not exist in the codebase.
   - `package.json` line 2: `"name": "react-example"` is an unrenamed template placeholder.

4. **Python Dependencies & Manifest**:
   - `requirements.txt` is absent from the repository root.
   - `app.py` imports `flask` (line 3), `psycopg2` / `SimpleConnectionPool` / `RealDictCursor` (lines 4–6), `pandas` (line 7), `openpyxl` (line 127), and `python-dotenv` (line 8).

5. **Root Configuration & Metadata**:
   - `metadata.json` line 5 specifies `"majorCapabilities": ["MAJOR_CAPABILITY_SERVER_SIDE_GEMINI_API"]`, but no Gemini API is implemented.
   - `.gitignore` line 8 specifies `!.env.example`, but `.env.example` is missing from the repository. Standard Python ignore rules (`__pycache__/`, `venv/`, `*.xlsx`) are missing.
   - `templates/carico.html` lines 1–3 and `templates/magazzino.html` lines 1–3 declare `active_page`, `show_search`, `page_title` via `{% set %}`, but `templates/header.html` never reads these variables.

---

## 2. Logic Chain

1. **Static Assets Assessment**:
   - Step 1: Catalog all files in `static/` -> Found only `static/js/status_monitor.js`.
   - Step 2: Cross-reference across `templates/` -> Found active `<script>` tag in `templates/footer.html:40`.
   - Step 3: Verify JS target elements and API route -> Found matching IDs in `footer.html:4,5` and matching route in `app.py:464`.
   - Conclusion: The only static file in `static/` is 100% active and necessary for the Flask app's health-check indicator.

2. **Dual-Architecture & Scaffolding Assessment**:
   - Step 1: Read `README.md:13-14` -> Explicitly notes that `src/` is a Google AI Studio demo preview screen, while `app.py` is the real application.
   - Step 2: Audit all imports in `src/App.tsx`, `src/main.tsx`, and `vite.config.ts`.
   - Step 3: Match against `package.json` dependencies.
   - Conclusion: Within the React demo scaffolding, 6 packages (`@google/genai`, `express`, `@types/express`, `dotenv`, `tsx`, `autoprefixer`) are completely unused dead code, and `vite` is declared twice. `clean` script targets a non-existent `server.js`.

3. **Backend & Configuration Assessment**:
   - Step 1: Scan repository for Python dependency manifests -> Missing `requirements.txt`.
   - Step 2: Inspect `app.py` imports -> Identified 5 required third-party Python packages (`flask`, `psycopg2-binary`, `pandas`, `openpyxl`, `python-dotenv`).
   - Step 3: Audit `.gitignore` -> Identified missing Python rules and orphan negation rule for missing `.env.example`.
   - Step 4: Audit template context variables -> Identified dead `{% set %}` variables in `carico.html` and `magazzino.html`.

---

## 3. Caveats

- **No modifications performed**: In strict compliance with read-only constraints, no files were added, edited, or removed in the workspace.
- **Node vs Python Duality**: The React scaffolding is technically functional as a standalone demo dashboard for AI Studio; classifying packages as "dead" is done strictly based on whether they are imported or executed anywhere in either the Flask app or the React demo.

---

## 4. Conclusion

The repository's static assets and configurations are well-scoped but contain specific dead dependencies, missing manifests, and configuration anomalies resulting from AI Studio boilerplate generation:
1. **Static Assets**: Exactly 1 local file (`static/js/status_monitor.js`), which is active. 3 external CDNs are utilized for styles, icons, and barcodes.
2. **Dead Dependencies in `package.json`**: 6 unused packages (`@google/genai`, `express`, `@types/express`, `dotenv`, `tsx`, `autoprefixer`), 1 duplicate (`vite`), and 1 dead file reference (`server.js` in clean script).
3. **Missing Configurations**: Missing `requirements.txt`, missing `.env.example`, missing Python `.gitignore` entries.
4. **Dead Template Variables**: `show_search`, `page_title`, and `active_page` in `carico.html` and `magazzino.html`.

---

## 5. Verification Method

To independently verify these findings:
1. **Verify Static File Usage**:
   - Check `templates/footer.html:40` for `static/js/status_monitor.js`.
   - Check `app.py:464` for `@app.route('/api/db_status')`.
2. **Verify Dead NPM Dependencies**:
   - Search whole repo for `@google/genai` -> 0 imports.
   - Search whole repo for `express` -> 0 imports.
   - Search whole repo for `server.js` -> 0 occurrences outside `package.json:10`.
3. **Verify Template Variable Disconnect**:
   - Check `templates/carico.html:1-3` vs `templates/header.html:6,65-69` to confirm `page_title` and `show_search` are unconsumed.
