# Dispatch Log

## 2026-08-23T10:57:34Z
You are the Project Orchestrator for the Gestionale_Macelleria project.

## Working Directory
- Project Root: c:\Users\david\Desktop\Gestionale_Macelleria
- Your Agent Directory: c:\Users\david\Desktop\Gestionale_Macelleria\.agents\orchestrator_2
- Original Request: c:\Users\david\Desktop\Gestionale_Macelleria\.agents\ORIGINAL_REQUEST.md

## Mission
Make the "Carico Merci" page of the butcher management system (Flask 3.0 + PostgreSQL + Jinja2 + Tailwind CSS + vanilla JS) dynamic, meeting all requirements and acceptance criteria in ORIGINAL_REQUEST.md (under the latest header 2026-08-23T10:57:09Z).

### Key Objectives:
1. R1: Client-side dynamic form (vanilla JS + CSS show/hide) showing HACCP meat traceability fields (paese_nascita, paese_allevamento, paese_macellazione, paese_sezionamento, data_macellazione) only when Bovino, Suino, or Avicolo is selected, via data-categoria attribute on <option> elements, without page reload or AJAX calls.
2. R2: DB migration adding `data_macellazione DATE NULL` to `LOTTO_MADRE`, updating `database.sql`, and updating INSERT query in `/salva_carico`.
3. R3: Backend conditional validation in `/salva_carico` verifying required country fields and at least one between data_macellazione and data_scadenza for meat categories, keeping them optional for non-meat categories.
4. R4: Distinct visual styling with Tailwind CSS for the HACCP meat traceability section.
5. Verification: Verify local app startup (`python app.py`) and test GET/POST behavior for both meat and non-meat categories, ensuring no regressions on other routes.

Maintain your `BRIEFING.md`, `plan.md`, and `progress.md` in your agent directory. Decompose tasks, dispatch to specialists, review work thoroughly, and report completion back to the Sentinel via send_message when ready for independent Victory Audit.
