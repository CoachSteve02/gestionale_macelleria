# Adversarial Challenge & Dynamic Verification Report

**Repository**: `Gestionale_Macelleria`  
**Date**: 2026-08-20  
**Investigator**: Challenger Subagent (`challenger_dynamic`)  
**Role**: Critic / Empirical Verification Specialist  
**Constraint Enforcement**: Strictly Read-Only Investigation (No modifications to original codebase)

---

## 1. Challenge Summary & Executive Assessment

**Overall Risk Assessment**: **LOW** (Codebase is clean and well-scoped, but critical edge-case warnings apply to prevent breaking changes).

This adversarial review challenged all dead code hypotheses across the Python backend (`app.py`), PostgreSQL database schema (`database.sql`), Jinja2 templates (`templates/`), static resources (`static/`), and Node.js/React scaffolding (`src/`, `package.json`, etc.).

### Critical Adversarial Insight & False Positive Prevention:
- **`LOTTO_MADRE.flg_lotto_del_giorno` IS NOT A ZERO-REFERENCE DEAD COLUMN**: While the column is never written to `TRUE` (making it a zombie/inactive feature), it is **actively queried in `app.py:84` and `app.py:324`**. Dropping this column from PostgreSQL schema without simultaneously modifying the Python backend will trigger an immediate **runtime crash** (`psycopg2.errors.UndefinedColumn: column "flg_lotto_del_giorno" does not exist`).
- **All 10 Flask routes and all 7 Jinja2 templates are 100% active**: No dynamic route dispatching (`url_for(var)`) or dynamic template loading (`{% include var %}`) exists. Every route has a static caller and every template is rendered or included.
- **Node.js/React stack (`src/`) is 100% inert in production**: Confirmed by `README.md:13` and `src/App.tsx:28-35`. It does not interact with Flask or PostgreSQL.

---

## 2. Adversarial Scrutiny of Survey Hypotheses

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    ADVERSARIAL SCRUTINY & VERDICT MATRIX                                 │
├────┬─────────────────────────────┬──────────────────┬─────────────────┬──────────────────────────────────┤
│ ID │ Candidate Item              │ Claimed Status   │ Verdict         │ Adversarial Verification Notes   │
├────┼─────────────────────────────┼──────────────────┼─────────────────┼──────────────────────────────────┤
│ C1 │ LOTTO_MADRE.                │ Dead / Zombie    │ ⚠️ ZOMBIE FLAG  │ Read in app.py:84, 324. Never    │
│    │ flg_lotto_del_giorno        │ Column           │ (CRITICAL WARN) │ written to TRUE. DB drop breaks! │
├────┼─────────────────────────────┼──────────────────┼─────────────────┼──────────────────────────────────┤
│ C2 │ RICETTA.versione            │ Dead Column      │ CONFIRMED DEAD  │ 0 reads, 0 writes, explicit SELECT│
├────┼─────────────────────────────┼──────────────────┼─────────────────┼──────────────────────────────────┤
│ C3 │ RICETTA.data_creazione      │ Dead Column      │ CONFIRMED DEAD  │ 0 reads, 0 writes, explicit SELECT│
├────┼─────────────────────────────┼──────────────────┼─────────────────┼──────────────────────────────────┤
│ C4 │ import psycopg2 (app.py:4)  │ Unused Import    │ CONFIRMED DEAD  │ psycopg2.* never called directly │
├────┼─────────────────────────────┼──────────────────┼─────────────────┼──────────────────────────────────┤
│ C5 │ Jinja Variables (carico &   │ Dead Variables   │ CONFIRMED DEAD  │ active_page, show_search,        │
│    │ magazzino lines 1-3)        │                  │                 │ page_title ignored by header.html│
├────┼─────────────────────────────┼──────────────────┼─────────────────┼──────────────────────────────────┤
│ C6 │ Search Bar on /carico and   │ Disconnected UI  │ CONFIRMED FLAW  │ .product-item selector absent;   │
│    │ /magazzino                  │                  │                 │ input event is a no-op           │
├────┼─────────────────────────────┼──────────────────┼─────────────────┼──────────────────────────────────┤
│ C7 │ React Scaffolding (`src/`,  │ Inert / Discon-  │ CONFIRMED INERT │ AI Studio presentation mockup;   │
│    │ `vite.config.ts`, etc.)     │ nected Layer     │                 │ no root index.html, not served   │
├────┼─────────────────────────────┼──────────────────┼─────────────────┼──────────────────────────────────┤
│ C8 │ NPM Dependencies            │ Dead Packages    │ CONFIRMED DEAD  │ 0 occurrences in codebase        │
│    │ (@google/genai, express,    │                  │                 │                                  │
│    │ @types/express, dotenv, tsx)│                  │                 │                                  │
├────┼─────────────────────────────┼──────────────────┼─────────────────┼──────────────────────────────────┤
│ C9 │ NPM clean script server.js  │ Dead File Ref    │ CONFIRMED DEAD  │ server.js does not exist on disk │
├────┼─────────────────────────────┼──────────────────┼─────────────────┼──────────────────────────────────┤
│ C10│ aggiorna_file_excel()       │ Claimed Dead by  │ REJECTED (FALSE │ ACTIVE: Called by /download_excel│
│    │ not in salva_carico         │ some heuristics  │ POSITIVE)       │ at runtime.                      │
├────┼─────────────────────────────┼──────────────────┼─────────────────┼──────────────────────────────────┤
│ C11│ static/js/status_monitor.js │ Asset in static/ │ CONFIRMED ACTIVE│ Polled every 30s; wires to       │
│    │                             │                  │ (NOT DEAD)      │ @app.route('/api/db_status')     │
└────┴─────────────────────────────┴──────────────────┴─────────────────┴──────────────────────────────────┘
```

---

## 3. Deep-Dive Dynamic Analysis & Stress-Testing

### 3.1 Dynamic Access Analysis in Python Backend & SQL (`app.py`)
- **`getattr()`, `setattr()`, `eval()`, `exec()`**: Zero instances found across the Python backend.
- **Dynamic Dictionary Access (`dict[key]`)**:
  - `articolo['tipo_categoria']` (`app.py:177`): Categorizes items into `catalogo['TAGLIO']`, `catalogo['PREPARATO']`, `catalogo['VARIO']`. All 3 categories match the SQL `CHECK` constraint `articolo_tipo_categoria_check`.
  - `taglio['id_ultimo_lotto_madre']` (`app.py:189`): Dynamically appended key for quick-print thermal label link. Used in `templates/index.html:18-20`.
  - `MESI_ITALIANI[now.month]` (`app.py:30, 52`): Dictionary lookup for Italian month names. Safe and active.
- **SQL Dynamic Construction**:
  - No string formatting (`%` or `f""`) is used for table or column names.
  - All queries use parameterized placeholders (`%s`) via `psycopg2` driver.
  - `query_carichi`, `query_preparati`, `query_haccp` in `aggiorna_file_excel()` (`app.py:81-109`) explicitly list selected columns.

### 3.2 Dynamic Route Dispatch Analysis
- **Flask Route Mapping**:
  - All 10 routes use static decorators (`@app.route('/', ...)` through `@app.route('/api/db_status')`).
  - No `app.add_url_rule` or custom URL converters.
  - Every `url_for` call in Python code and Jinja2 templates uses a static string literal matching a declared endpoint.
  - **Verdict**: ZERO orphaned routes.

### 3.3 Jinja2 Dynamic Template Loading Analysis
- **Template Hierarchy**:
  - 5 standalone views rendered via `render_template()`: `index.html`, `carico.html`, `magazzino.html`, `etichetta.html`, `etichetta_taglio.html`.
  - 2 partials included via static `{% include 'header.html' %}` and `{% include 'footer.html' %}`: `header.html`, `footer.html`.
  - No dynamic inclusions like `{% include template_name %}`.
  - **Verdict**: ZERO orphaned template files.

### 3.4 Build Pipeline & Hidden Execution Analysis
- **CI/CD & Containers**: No `.github/`, Dockerfile, Makefile, Procfile, or container orchestration manifests exist in the repository.
- **Vite Execution**: Vite expects a root `index.html` file to mount React (`<script type="module" src="/src/main.tsx"></script>`). The root only contains Jinja templates inside `templates/`. Therefore, Vite is purely an AI Studio container artifact.
- **Python Manifest**: `requirements.txt` is missing from the repository root, though dependencies are documented in `README.md:44`.

---

## 4. Blast Radius & Mitigation Guidelines

### Challenge 1: `LOTTO_MADRE.flg_lotto_del_giorno` Blast Radius
- **Assumption Challenged**: "This column is unused and can simply be dropped via `ALTER TABLE LOTTO_MADRE DROP COLUMN flg_lotto_del_giorno;`"
- **Attack Scenario**: If a developer executes this DDL change without touching `app.py`, calling `/download_excel` or `/produci_preparato/<id>` will execute:
  ```sql
  SELECT ... flg_lotto_del_giorno FROM LOTTO_MADRE ...
  ```
  PostgreSQL will throw `psycopg2.errors.UndefinedColumn` and return HTTP 500 error to users.
- **Mitigation / Safe Action**:
  - **Option A (Feature Activation)**: Add a checkbox `<input type="checkbox" name="flg_lotto_del_giorno">` in `carico.html` and update `salva_carico` to save `True` when checked.
  - **Option B (Feature Removal)**: Remove `flg_lotto_del_giorno` from `query_carichi` (`app.py:84`) and `produci_preparato` query (`app.py:324, 325`), THEN drop the column from `database.sql`.

### Challenge 2: Redundant `SESSIONE_LAVORAZIONE` Instantiation
- **Observation**: `app.py:303` executes `INSERT INTO SESSIONE_LAVORAZIONE` on every click of `produci_preparato`, producing hundreds of open sessions in a single day.
- **Mitigation**: Query for an existing open session for today (`WHERE stato_sessione = 'Aperta' AND DATE(data_ora_inizio) = CURRENT_DATE`) before inserting a new one.

### Challenge 3: Dead `else: pass` in `produci_preparato`
- **Observation**: `app.py:334-336` silently passes when an ingredient lot is missing from `LOTTO_MADRE`.
- **Mitigation**: Log a warning `app.logger.warning(f"Ingrediente {id_ing} non disponibile in magazzino per preparato {id_lotto_preparato}")`.

---

## 5. Unchallenged Areas
- Database Connection String Security: `.env` file credentials handling is out of dead code scope (standard environment separation).
