## 2026-08-20T20:01:41Z
You are an Explorer subagent conducting a comprehensive survey of the Backend & Database architecture for dead code analysis.

Working directory: C:\Users\david\Desktop\Gestionale_Macelleria\.agents\explorer_backend_survey
Original Request Path: C:\Users\david\Desktop\Gestionale_Macelleria\.agents\ORIGINAL_REQUEST.md
Workspace root: C:\Users\david\Desktop\Gestionale_Macelleria

Task:
1. Read `C:\Users\david\Desktop\Gestionale_Macelleria\.agents\ORIGINAL_REQUEST.md`.
2. Inspect the repository root and backend files: `app.py`, any Python scripts, utilities, blueprints, and database definition files (`database.sql`, migrations, sqlite files).
3. Map out:
   - All Flask routes / endpoints defined in `app.py` or elsewhere (methods, url rules, endpoint names).
   - All Python functions, helper classes, imports in backend scripts.
   - All database tables, columns, views, triggers defined in `database.sql`.
   - Initial findings of backend code or database objects that appear unreferenced, obsolete, duplicate, or dead.
4. ABSOLUTE CONSTRAINT: Read-only analysis. DO NOT modify or delete any code or database files.
5. Write your detailed survey report to `C:\Users\david\Desktop\Gestionale_Macelleria\.agents\explorer_backend_survey\backend_survey.md` and write `handoff.md`.
6. Send a completion message back to the orchestrator when finished.
