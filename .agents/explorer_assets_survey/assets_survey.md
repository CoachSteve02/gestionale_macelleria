# Static Assets, Dependencies & Configuration Survey Report

**Repository**: `Gestionale_Macelleria`  
**Date**: 2026-08-20  
**Investigator**: Explorer Subagent (`explorer_assets_survey`)  
**Scope**: Static assets (`static/`), dependencies (`package.json`, `requirements.txt`), build configurations (`vite.config.ts`, `tsconfig.json`, `metadata.json`, `.gitignore`), and cross-layer references across Backend (`app.py`), Templates (`templates/`), and Frontend (`src/`).

---

## 1. Executive Summary

An exhaustive audit of the `Gestionale_Macelleria` repository reveals a fundamental architectural coexistence between two distinct layers:
1. **The Core Production Application**: A server-side Python 3 / Flask web application with PostgreSQL persistence (`app.py`, `database.sql`, `templates/`, `static/js/status_monitor.js`).
2. **The AI Studio Scaffolding Layer**: A client-side React 19 / TypeScript / Vite dashboard in `src/` (`src/App.tsx`, `src/main.tsx`, `src/index.css`, `package.json`, `vite.config.ts`, `tsconfig.json`, `metadata.json`), generated as initial boilerplate by Google AI Studio. As explicitly noted in `README.md` (lines 13–14), this React layer is purely a summary interface and does not run the business logic.

### Key Metrics Summary
| Metric Category | Found | Active / Used | Dead / Unused / Orphaned | Redundant / Misconfigured |
| :--- | :---: | :---: | :---: | :---: |
| **Static Files in `static/`** | 1 | 1 | 0 | 0 |
| **External CDN Assets in Templates** | 3 | 3 | 0 | 0 |
| **NPM Dependencies (`dependencies`)** | 10 | 4 (demo only) | 3 (`@google/genai`, `express`, `dotenv`) | 3 (`vite` dup, `@tailwindcss/vite`, `@vitejs/plugin-react`) |
| **NPM DevDependencies (`devDependencies`)** | 8 | 4 | 3 (`@types/express`, `tsx`, `autoprefixer`) | 1 (`vite` dup) |
| **Python Dependencies (`requirements.txt`)** | 0 (File Missing) | 5 (in `app.py`) | 0 | Missing config file |
| **Root Config Files** | 6 | 4 | 0 | 2 (`metadata.json` unused capability, `.gitignore` missing python) |

---

## 2. Comprehensive Inventory of Static Assets (`static/`)

### 2.1 File Catalog & Reference Mapping
The `static/` directory contains exactly **one file**:

| Path | Size (Bytes) | Referenced In | Line Number(s) | Status | Role & Verification |
| :--- | :---: | :--- | :--- | :---: | :--- |
| `static/js/status_monitor.js` | 1,085 B | `templates/footer.html` | Line 40 | **ACTIVE** | Included via `{{ url_for('static', filename='js/status_monitor.js') }}` with `defer`. |

### 2.2 Functional Analysis of `static/js/status_monitor.js`
- **Behavior**: Executes `checkDbStatus()` upon `DOMContentLoaded` and every 30,000 ms (30 seconds) via `setInterval`.
- **Target DOM Elements**:
  - `document.getElementById('db-status-dot')`: Verified present in `templates/footer.html` (line 4).
  - `document.getElementById('db-status-text')`: Verified present in `templates/footer.html` (line 5).
- **Backend API Contract**: Issues `fetch('/api/db_status')`.
  - Verified endpoint in `app.py` (lines 464–477):
    ```python
    @app.route('/api/db_status')
    def db_status():
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1;")
            return jsonify({"status": "ok"})
        except Exception:
            return jsonify({"status": "error"}), 500
        finally:
            if conn:
                db_pool.putconn(conn)
    ```
- **Conclusion**: `status_monitor.js` is fully wired, active, and functional.

### 2.3 External CDN Static Assets (Not locally hosted in `static/`)
The Jinja2 templates rely on third-party CDNs rather than local static files:
1. **Tailwind CSS Browser Runtime**:
   - URL: `https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4`
   - Referenced in: `templates/header.html` (line 7)
   - Purpose: Runtime JIT styling for the Flask UI.
2. **Google Material Symbols Outlined Font**:
   - URL: `https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200`
   - Referenced in: `templates/header.html` (line 8)
   - Icons used: `search` (`header.html:67`), `download` (`footer.html:8`).
3. **JsBarcode Library**:
   - URL: `https://cdn.jsdelivr.net/npm/jsbarcode@3.11.5/dist/JsBarcode.all.min.js`
   - Referenced in: `templates/etichetta.html` (line 8), `templates/etichetta_taglio.html` (line 8)
   - Purpose: Generates CODE128 SVG barcodes on client-side thermal label prints.

### 2.4 Missing / Non-Existent Static Assets
- **No Favicon**: There is no `favicon.ico` in `static/` or root, leading browsers to generate 404 errors in Flask logs unless handled.
- **No Local Images/Fonts**: No `.png`, `.jpg`, `.svg`, or `.woff` files exist in `static/`.
- **No Local Compiled CSS**: No `.css` files exist in `static/css/` (Flask relies entirely on CDN Tailwind).

---

## 3. Node.js & NPM Dependencies Audit (`package.json`)

### 3.1 `package.json` Manifest Analysis
```json
{
  "name": "react-example",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite --port=3000 --host=0.0.0.0",
    "build": "vite build",
    "preview": "vite preview",
    "clean": "rm -rf dist server.js",
    "lint": "tsc --noEmit"
  },
  "dependencies": {
    "@google/genai": "^2.4.0",
    "@tailwindcss/vite": "^4.1.14",
    "@vitejs/plugin-react": "^5.0.4",
    "lucide-react": "^0.546.0",
    "react": "^19.0.1",
    "react-dom": "^19.0.1",
    "vite": "^6.2.3",
    "express": "^4.21.2",
    "dotenv": "^17.2.3",
    "motion": "^12.23.24"
  },
  "devDependencies": {
    "@types/node": "^22.14.0",
    "autoprefixer": "^10.4.21",
    "esbuild": "^0.25.0",
    "tailwindcss": "^4.1.14",
    "tsx": "^4.21.0",
    "typescript": "~5.8.2",
    "vite": "^6.2.3",
    "@types/express": "^4.17.21"
  }
}
```

### 3.2 Detailed Dependency Breakdown & Dead Code Classification

| Dependency | Scope | Status | Evidence / Usage in Codebase | Recommendation |
| :--- | :--- | :---: | :--- | :--- |
| `@google/genai` (`^2.4.0`) | `dependencies` | **DEAD / UNUSED** | 0 imports found in `src/`, `app.py`, or any file. | Remove from `package.json`. |
| `express` (`^4.21.2`) | `dependencies` | **DEAD / UNUSED** | 0 imports found. The backend is Python Flask (`app.py`), not Express. | Remove from `package.json`. |
| `@types/express` (`^4.17.21`) | `devDependencies` | **DEAD / UNUSED** | Express is not used in the project. | Remove from `package.json`. |
| `dotenv` (`^17.2.3`) | `dependencies` | **DEAD / UNUSED** | Node `dotenv` is never imported. (`app.py` uses python `python-dotenv`). | Remove from `package.json`. |
| `tsx` (`^4.21.0`) | `devDependencies` | **DEAD / UNUSED** | No TSX execution script in `package.json` or project. | Remove from `package.json`. |
| `autoprefixer` (`^10.4.21`) | `devDependencies` | **DEAD / UNUSED** | Tailwind v4 via `@tailwindcss/vite` does not use Autoprefixer/PostCSS config. | Remove from `package.json`. |
| `vite` (`^6.2.3`) | `dependencies` & `devDependencies` | **DUPLICATE / REDUNDANT** | Listed in BOTH `dependencies` (line 20) and `devDependencies` (line 32). | Move exclusively to `devDependencies`. |
| `@tailwindcss/vite` (`^4.1.14`) | `dependencies` | **MISPLACED** | Used in `vite.config.ts` (line 1), but should be a dev tool. | Move to `devDependencies`. |
| `@vitejs/plugin-react` (`^5.0.4`) | `dependencies` | **MISPLACED** | Used in `vite.config.ts` (line 2), but should be a dev tool. | Move to `devDependencies`. |
| `esbuild` (`^0.25.0`) | `devDependencies` | **REDUNDANT** | Bundled internally by Vite; manual devDependency is redundant. | Optional / can be cleaned. |
| `react` (`^19.0.1`) | `dependencies` | **ACTIVE (DEMO)** | Used in `src/main.tsx` (line 1). | Active in React scaffolding. |
| `react-dom` (`^19.0.1`) | `dependencies` | **ACTIVE (DEMO)** | Used in `src/main.tsx` (line 2) for `createRoot`. | Active in React scaffolding. |
| `motion` (`^12.23.24`) | `dependencies` | **ACTIVE (DEMO)** | Used in `src/App.tsx` (line 6: `import { motion } from 'motion/react'`). | Active in React scaffolding. |
| `lucide-react` (`^0.546.0`) | `dependencies` | **ACTIVE (DEMO)** | Used in `src/App.tsx` (line 7: `Database, FileCode, FileSpreadsheet, Download, LayoutDashboard`). | Active in React scaffolding. |
| `tailwindcss` (`^4.1.14`) | `devDependencies` | **ACTIVE (DEMO)** | Used via `src/index.css` (`@import "tailwindcss";`). | Active in React scaffolding. |
| `@types/node` (`^22.14.0`) | `devDependencies` | **ACTIVE (DEMO)** | Used for Node types in `vite.config.ts` (`path`, `process.env`). | Active in React scaffolding. |
| `typescript` (`~5.8.2`) | `devDependencies` | **ACTIVE (DEMO)** | Used for `npm run lint` (`tsc --noEmit`). | Active in React scaffolding. |

### 3.3 NPM Scripts & Dead Artifact References
- `"clean": "rm -rf dist server.js"`:
  - **Dead Reference**: `server.js` does NOT exist in the repository. This is an orphan artifact from an Express boilerplate.
  - **Portability Flaw**: `rm -rf` is Unix-specific and fails in standard Windows `cmd.exe`.
- `"name": "react-example"`:
  - Default boilerplate placeholder name not updated to `gestionale-macelleria`.

---

## 4. Python Backend Dependencies Audit (`requirements.txt` vs `app.py`)

### 4.1 Missing `requirements.txt`
There is **no `requirements.txt` file** in the repository root.

### 4.2 Python Dependencies Usage Analysis (`app.py`)
Inspecting `app.py` (lines 1–10) reveals the required runtime dependencies:
1. `flask` (v3+ or v2.3+):
   - Used for routing, templates, session flash messages, send_file, and jsonify (`app.py:3`).
2. `psycopg2-binary` (or `psycopg2`):
   - Used for PostgreSQL connection pool `SimpleConnectionPool` and `RealDictCursor` (`app.py:4–6`).
3. `pandas`:
   - Used for `pd.read_sql_query` and `pd.ExcelWriter` in HACCP Excel export (`app.py:7, 118–130`).
4. `openpyxl`:
   - Used as the Excel writer engine in `pd.ExcelWriter(percorso_tmp, engine='openpyxl')` (`app.py:127`).
5. `python-dotenv`:
   - Used for `load_dotenv()` to read `.env` configuration (`app.py:8, 21`).
6. Python Standard Library (no pip installation required):
   - `os`, `datetime`, `threading`, `tempfile`.

### 4.3 Recommended `requirements.txt`
```txt
flask>=3.0.0
psycopg2-binary>=2.9.9
pandas>=2.2.0
openpyxl>=3.1.2
python-dotenv>=1.0.0
```

---

## 5. Configuration Files & Build System Audit

### 5.1 `vite.config.ts`
```typescript
import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import {defineConfig} from 'vite';

export default defineConfig(() => {
  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      },
    },
    server: {
      hmr: process.env.DISABLE_HMR !== 'true',
      watch: process.env.DISABLE_HMR === 'true' ? null : {},
    },
  };
});
```
- **Observations**:
  - Configures Vite to build the React demo app with React and Tailwind plugins.
  - Contains specific Google AI Studio environment flag handling (`DISABLE_HMR`).
  - `@` alias maps to repository root `.`.

### 5.2 `tsconfig.json`
- Configured for React 19 JSX runtime (`"jsx": "react-jsx"`), ES2022 target, and bundler module resolution.
- `"allowImportingTsExtensions": true` and `"noEmit": true`.
- Clean configuration for the TypeScript demo layer.

### 5.3 `metadata.json`
```json
{
  "name": "Gestionale Macelleria",
  "description": "Sistema di tracciabilità alimentare HACCP e gestione magazzino macelleria, con esportazione in Excel e backend Python/Flask.",
  "requestFramePermissions": [],
  "majorCapabilities": ["MAJOR_CAPABILITY_SERVER_SIDE_GEMINI_API"]
}
```
- **Observations**:
  - Contains `"majorCapabilities": ["MAJOR_CAPABILITY_SERVER_SIDE_GEMINI_API"]`.
  - However, no Gemini API or `@google/genai` calls exist in `app.py` or `src/App.tsx`. This capability is currently dormant/unused.

### 5.4 `.gitignore`
```gitignore
node_modules/
build/
dist/
coverage/
.DS_Store
*.log
.env*
!.env.example
```
- **Observations & Gaps**:
  - References `!.env.example`, but `.env.example` does NOT exist in the repository.
  - Missing standard Python ignore rules: `__pycache__/`, `*.py[cod]`, `venv/`, `.venv/`, `*.xlsx`, `.pytest_cache/`.

### 5.5 Jinja2 Templates Unused Context Variables
In `templates/carico.html` and `templates/magazzino.html`:
- Lines 1–3 in `carico.html`:
  ```jinja2
  {% set active_page = 'carico' %}
  {% set show_search = false %}
  {% set page_title = 'Carico Merce - Gestionale Macelleria' %}
  ```
- Lines 1–3 in `magazzino.html`:
  ```jinja2
  {% set active_page = 'magazzino' %}
  {% set show_search = false %}
  {% set page_title = 'Magazzino - Gestionale Macelleria' %}
  ```
- **Finding**: In `templates/header.html`, neither `page_title` nor `show_search` are used!
  - `header.html` line 6 hardcodes `<title>Gestionale Macelleria</title>`.
  - `header.html` lines 65–69 unconditionally render the search bar on all pages.
  - `active_page` is not used in `header.html` for navigation highlighting (navigation instead checks `request.endpoint == 'index'`, `request.endpoint == 'carico'`, `request.endpoint == 'magazzino'` at lines 34, 41, 48).
  - Therefore, `active_page`, `show_search`, and `page_title` are dead template variable declarations.

---

## 6. Dead Code, Unused Dependencies & Obsolete Configurations Matrix

| ID | Category | Item / File | Line / Location | Status | Rationale / Evidence |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **DC-AS-01** | NPM Dependency | `@google/genai` | `package.json:14` | **DEAD** | Zero references or imports across entire codebase. |
| **DC-AS-02** | NPM Dependency | `express` | `package.json:21` | **DEAD** | Backend is Python Flask; Express is never imported. |
| **DC-AS-03** | NPM DevDependency | `@types/express` | `package.json:33` | **DEAD** | Express is unused; typing package is dead. |
| **DC-AS-04** | NPM Dependency | `dotenv` | `package.json:22` | **DEAD** | Node `dotenv` is never imported in any `.ts`, `.tsx`, or `.js` file. |
| **DC-AS-05** | NPM DevDependency | `tsx` | `package.json:30` | **DEAD** | No TSX execution script or runner configured in repository. |
| **DC-AS-06** | NPM DevDependency | `autoprefixer` | `package.json:27` | **DEAD** | Tailwind v4 uses `@tailwindcss/vite`; no PostCSS/Autoprefixer pipeline. |
| **DC-AS-07** | NPM Dependency | `vite` (duplicate) | `package.json:20,32` | **REDUNDANT** | `vite` is declared in both `dependencies` and `devDependencies`. |
| **DC-AS-08** | NPM Script Target | `server.js` | `package.json:10` | **DEAD TARGET** | `"clean": "rm -rf dist server.js"` targets non-existent `server.js`. |
| **DC-AS-09** | Configuration | `requirements.txt` | Repository Root | **MISSING** | Standard Python dependency manifest missing from repository root. |
| **DC-AS-10** | Metadata | `MAJOR_CAPABILITY_SERVER_SIDE_GEMINI_API` | `metadata.json:5` | **UNUSED** | Capability declared in AI Studio metadata without any API implementation. |
| **DC-AS-11** | Git Ignore | `!.env.example` | `.gitignore:8` | **DEAD EXCEPTION** | Negation rule exists for `.env.example`, but file is absent. |
| **DC-AS-12** | Git Ignore | Python ignore rules | `.gitignore` | **MISSING** | Missing `__pycache__/`, `venv/`, `*.xlsx` rules. |
| **DC-AS-13** | Template Logic | `active_page`, `show_search`, `page_title` | `templates/carico.html:1-3`, `magazzino.html:1-3` | **DEAD VARIABLES** | Variables set in views are never consumed in `header.html` or child templates. |
| **DC-AS-14** | Static Asset | `favicon.ico` | `static/` | **MISSING** | Missing favicon asset causes 404 logs on web browsers. |

---

## 7. Architectural Assessment & Strategic Recommendations

### 7.1 Architecture Classification
The codebase is structured around two distinct operational modes:
1. **Production Mode (Python/Flask/PostgreSQL)**:
   - Primary entry point: `app.py`
   - UI: `templates/*.html` + `static/js/status_monitor.js`
   - DB: PostgreSQL via `database.sql`
   - Exports: Excel files via Pandas/openpyxl
2. **Demo Mode (React/TypeScript/Vite)**:
   - Primary entry point: `src/main.tsx` -> `src/App.tsx`
   - Purpose: Static informational splash screen explaining the Flask architecture for AI Studio preview.

### 7.2 Actionable Recommendations for Cleanup & Maintenance

#### Recommendation 1: Clean `package.json` Dependencies
If retaining the React demo dashboard, trim unused packages:
```json
{
  "name": "gestionale-macelleria-preview",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite --port=3000 --host=0.0.0.0",
    "build": "vite build",
    "preview": "vite preview",
    "clean": "rm -rf dist",
    "lint": "tsc --noEmit"
  },
  "dependencies": {
    "lucide-react": "^0.546.0",
    "motion": "^12.23.24",
    "react": "^19.0.1",
    "react-dom": "^19.0.1"
  },
  "devDependencies": {
    "@tailwindcss/vite": "^4.1.14",
    "@types/node": "^22.14.0",
    "@vitejs/plugin-react": "^5.0.4",
    "tailwindcss": "^4.1.14",
    "typescript": "~5.8.2",
    "vite": "^6.2.3"
  }
}
```

#### Recommendation 2: Create `requirements.txt`
Add `requirements.txt` at the root with pinned minimum versions:
```txt
flask>=3.0.0
psycopg2-binary>=2.9.9
pandas>=2.2.0
openpyxl>=3.1.2
python-dotenv>=1.0.0
```

#### Recommendation 3: Add `.env.example` and Update `.gitignore`
- Create `.env.example` template:
  ```env
  DATABASE_URL=postgresql://postgres:postgres@localhost:5432/gestionale_macelleria_dev
  SECRET_KEY=cambiami_con_una_chiave_segreta_sicura
  ```
- Update `.gitignore` with Python rules:
  ```gitignore
  node_modules/
  dist/
  __pycache__/
  *.py[cod]
  *$py.class
  venv/
  .venv/
  *.xlsx
  *.log
  .env*
  !.env.example
  ```

#### Recommendation 4: Fix Jinja2 Header / Variable Sync
Either remove the unused `{% set %}` declarations in `carico.html` and `magazzino.html` or update `header.html` to consume `{{ page_title | default('Gestionale Macelleria') }}` and `{% if show_search | default(true) %}`.
