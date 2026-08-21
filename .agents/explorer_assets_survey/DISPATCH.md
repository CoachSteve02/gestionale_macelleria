## 2026-08-20T20:01:41Z
You are an Explorer subagent conducting a comprehensive survey of Static Assets, Dependencies, and Configuration for dead code analysis.

Working directory: C:\Users\david\Desktop\Gestionale_Macelleria\.agents\explorer_assets_survey
Original Request Path: C:\Users\david\Desktop\Gestionale_Macelleria\.agents\ORIGINAL_REQUEST.md
Workspace root: C:\Users\david\Desktop\Gestionale_Macelleria

Task:
1. Read `C:\Users\david\Desktop\Gestionale_Macelleria\.agents\ORIGINAL_REQUEST.md`.
2. Inspect `static/` (CSS, JS, images, fonts, icons), root config files (`package.json`, `requirements.txt`, `package-lock.json`, etc.), and static references across both backend and frontend.
3. Map out:
   - All static files in `static/` and where/if they are referenced in `templates/`, `src/`, `app.py`, or CSS stylesheets.
   - All dependencies in `package.json` and `requirements.txt` vs actual usage in the codebase.
   - Any orphaned assets, unused build artifacts, dead scripts, obsolete configurations.
4. ABSOLUTE CONSTRAINT: Read-only analysis. DO NOT modify or delete any code or files.
5. Write your detailed survey report to `C:\Users\david\Desktop\Gestionale_Macelleria\.agents\explorer_assets_survey\assets_survey.md` and write `handoff.md`.
6. Send a completion message back to the orchestrator when finished.
