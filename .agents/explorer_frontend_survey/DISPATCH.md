## 2026-08-20T20:01:41Z
You are an Explorer subagent conducting a comprehensive survey of the Frontend & Templates architecture for dead code analysis.

Working directory: C:\Users\david\Desktop\Gestionale_Macelleria\.agents\explorer_frontend_survey
Original Request Path: C:\Users\david\Desktop\Gestionale_Macelleria\.agents\ORIGINAL_REQUEST.md
Workspace root: C:\Users\david\Desktop\Gestionale_Macelleria

Task:
1. Read `C:\Users\david\Desktop\Gestionale_Macelleria\.agents\ORIGINAL_REQUEST.md`.
2. Inspect the frontend files: `templates/` (Jinja2 HTML templates), `src/` (React / TypeScript components, hooks, utils, styles, pages), `index.html` (if any), and frontend config files (`vite.config.ts`, `tsconfig.json`, `tailwind.config.js`, etc.).
3. Map out:
   - All Jinja2 templates in `templates/` and their rendering points (`render_template` calls in Python or includes/extends in Jinja).
   - All React components, pages, hooks, utils in `src/` and how they are imported / exported / mounted.
   - Frontend entry points (Vite index.html, main.tsx, App.tsx, etc.) and routing.
   - Initial findings of unimported components, orphan templates, dead UI code or commented out code.
4. ABSOLUTE CONSTRAINT: Read-only analysis. DO NOT modify or delete any code or files.
5. Write your detailed survey report to `C:\Users\david\Desktop\Gestionale_Macelleria\.agents\explorer_frontend_survey\frontend_survey.md` and write `handoff.md`.
6. Send a completion message back to the orchestrator when finished.
