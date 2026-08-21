## 2026-08-20T20:01:19Z

User Request received:
Perform a comprehensive, deep dead code and unused file/function/asset/database schema analysis across the `Gestionale_Macelleria` project and produce a detailed report `dead_code_report.md`.

Requirements:
1. R1 - Backend & Database Analysis:
   - Analyze Flask application (`app.py`), helper scripts, DB schema (`database.sql`).
   - Identify unreferenced endpoints, unused Python functions/imports/classes, and unused tables/columns.
2. R2 - Frontend & Static Assets:
   - Analyze Jinja2 templates (`templates/`), React/TypeScript (`src/`), static assets (`static/`), dependencies (`package.json`, `tsconfig.json`, `vite.config.ts`).
   - Identify unimported components, orphan templates, unreferenced static assets (images, styles, scripts).
3. R3 - Final Report:
   - Generate `dead_code_report.md` in the artifact folder (and create an artifact).
   - Categorize by Backend, DB, Frontend, Configuration/Assets with clear justifications for every identified item.
4. ABSOLUTE CONSTRAINT:
   - DO NOT delete or modify any source code, database scripts, or assets in the repository. This is strictly a read-only analysis.
