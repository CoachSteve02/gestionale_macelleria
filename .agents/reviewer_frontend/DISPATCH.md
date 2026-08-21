## 2026-08-20T20:05:55Z
You are a Reviewer subagent specializing in Frontend, Templates, and Asset dead code review for Gestionale_Macelleria.

Working directory: C:\Users\david\Desktop\Gestionale_Macelleria\.agents\reviewer_frontend
Original Request Path: C:\Users\david\Desktop\Gestionale_Macelleria\.agents\ORIGINAL_REQUEST.md
Survey findings:
- Frontend: C:\Users\david\Desktop\Gestionale_Macelleria\.agents\explorer_frontend_survey\frontend_survey.md
- Assets: C:\Users\david\Desktop\Gestionale_Macelleria\.agents\explorer_assets_survey\assets_survey.md
Workspace root: C:\Users\david\Desktop\Gestionale_Macelleria

Task:
1. Read `ORIGINAL_REQUEST.md` and the survey findings above.
2. Thoroughly verify:
   - All 7 Jinja2 templates in `templates/` and confirm if any template is orphaned.
   - Template variables `active_page`, `show_search`, `page_title` in `carico.html` and `magazzino.html` vs `header.html`.
   - Search bar `#searchInput` in `header.html` and JavaScript filter in `footer.html`.
   - `static/js/status_monitor.js` usage in `footer.html` and `/api/db_status`.
   - React/Vite scaffolding (`src/App.tsx`, `src/main.tsx`, `src/index.css`, `vite.config.ts`, `tsconfig.json`, `metadata.json`).
   - Dead npm dependencies in `package.json` (`@google/genai`, `express`, `@types/express`, `dotenv`, `tsx`, `autoprefixer`), duplicate `vite`, and `"clean"` script referencing `server.js`.
   - Missing `requirements.txt` and `.env.example`.
3. ABSOLUTE CONSTRAINT: Strictly read-only analysis. DO NOT modify any code.
4. Write your review report to `C:\Users\david\Desktop\Gestionale_Macelleria\.agents\reviewer_frontend\frontend_review.md` and provide a 5-section `handoff.md` with explicit APPROVE/REQUEST_CHANGES verdict.
5. Send a completion message back to orchestrator.
