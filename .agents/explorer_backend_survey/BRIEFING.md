# BRIEFING — 2026-08-20T20:05:00Z

## Mission
Comprehensive survey and dead code analysis of the Backend & Database architecture (Flask routes, Python scripts, database schema, views, triggers, orphaned endpoints, unused functions, unreferenced DB objects).

## 🔒 My Identity
- Archetype: explorer
- Roles: Backend & Database Surveyor, Dead Code Investigator
- Working directory: C:\Users\david\Desktop\Gestionale_Macelleria\.agents\explorer_backend_survey
- Original parent: 417b37a5-594d-4b26-8aae-a3a1bc58b9a5
- Milestone: backend_database_survey

## 🔒 Key Constraints
- Read-only investigation — do NOT implement or delete anything
- Write only to .agents/explorer_backend_survey/
- Deliver exhaustive evidence-based report in backend_survey.md and handoff.md

## Current Parent
- Conversation ID: 417b37a5-594d-4b26-8aae-a3a1bc58b9a5
- Updated: 2026-08-20T20:05:00Z

## Investigation State
- **Explored paths**: `app.py`, `database.sql`, `metadata.json`, `package.json`, `tsconfig.json`, `vite.config.ts`, `src/App.tsx`, `src/main.tsx`, `src/index.css`, `static/js/status_monitor.js`, `templates/header.html`, `templates/footer.html`, `templates/index.html`, `templates/carico.html`, `templates/magazzino.html`, `templates/etichetta.html`, `templates/etichetta_taglio.html`, `README.md`.
- **Key findings**:
  - Flask backend defines 10 HTTP routes + 1 context processor, all actively wired to UI/JS.
  - Database schema defines 7 tables, 7 sequences, 2 indexes, 1 SQL view (`vw_etichetta_preparato`), 0 triggers.
  - Dead code/anomalies found:
    1. `LOTTO_MADRE.flg_lotto_del_giorno` (zombie/never written to TRUE).
    2. `RICETTA.versione` and `RICETTA.data_creazione` (defined in DDL, never read/queried in code).
    3. `import psycopg2` at `app.py:4` (redundant top-level import).
    4. `else: pass` at `app.py:334-336` (dead/empty branch on missing ingredient lot).
    5. Session creation redundancy at `app.py:303` (creates new session per item).
    6. React/Vite scaffolding (`src/`, `package.json`, `vite.config.ts`) is legacy AI Studio demo code.
- **Unexplored areas**: None for backend and database. Full survey complete.

## Key Decisions Made
- Analyzed all files with read-only tools (`view_file`, `find_by_name`, `list_dir`).
- Compiled comprehensive report in `backend_survey.md` and 5-component `handoff.md`.

## Artifact Index
- `C:\Users\david\Desktop\Gestionale_Macelleria\.agents\explorer_backend_survey\backend_survey.md` — Detailed survey report
- `C:\Users\david\Desktop\Gestionale_Macelleria\.agents\explorer_backend_survey\handoff.md` — 5-component handoff report
- `C:\Users\david\Desktop\Gestionale_Macelleria\.agents\explorer_backend_survey\progress.md` — Progress tracker
