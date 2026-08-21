# Project: Gestionale_Macelleria Dead Code Audit

## Architecture & Scope
- **Backend**: Flask application (`app.py`), helper scripts, database schema (`database.sql`), SQLite queries.
- **Frontend**: Jinja2 templates (`templates/`), React/TypeScript (`src/`), static assets (`static/`), build/package configurations (`package.json`, `tsconfig.json`, `vite.config.ts`, etc.).
- **Deliverable**: `dead_code_report.md` in `C:\Users\david\.gemini\antigravity\brain\9ec63668-a379-47d1-b92f-29d5c59e1ed2\dead_code_report.md`

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Survey & Inventory | Survey full codebase structure, files, endpoints, components, assets, templates | None | IN_PROGRESS |
| 2 | Backend & DB Analysis | Analyze `app.py`, python helper files, `database.sql`, endpoints, unused functions/classes/imports, unreferenced tables/columns | M1 | PLANNED |
| 3 | Frontend & Asset Analysis | Analyze `templates/`, `src/`, `static/`, dependencies, unimported components, orphan templates, unused assets | M1 | PLANNED |
| 4 | Verification & False Positive Filtering | Reviewer & Challenger verification of all flagged dead code items | M2, M3 | PLANNED |
| 5 | Synthesis & Final Report Generation | Assemble comprehensive `dead_code_report.md` and verify all requirements | M4 | PLANNED |
