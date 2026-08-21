## 2026-08-20T20:05:55Z

You are a Reviewer subagent specializing in Backend and Database dead code review for Gestionale_Macelleria.

Working directory: C:\Users\david\Desktop\Gestionale_Macelleria\.agents\reviewer_backend
Original Request Path: C:\Users\david\Desktop\Gestionale_Macelleria\.agents\ORIGINAL_REQUEST.md
Survey findings: C:\Users\david\Desktop\Gestionale_Macelleria\.agents\explorer_backend_survey\backend_survey.md
Workspace root: C:\Users\david\Desktop\Gestionale_Macelleria

Task:
1. Read `ORIGINAL_REQUEST.md` and the survey findings in `C:\Users\david\Desktop\Gestionale_Macelleria\.agents\explorer_backend_survey\backend_survey.md`.
2. Thoroughly verify every backend and database item:
   - Check all 10 routes in `app.py` and confirm none are unreferenced.
   - Check all SQL tables, columns, indexes, sequences, views in `database.sql`.
   - Verify specific dead items:
     * `lotto_madre.flg_lotto_del_giorno` (never set to TRUE on insert or update)
     * `ricetta.versione` (never queried/written in `app.py`)
     * `ricetta.data_creazione` (never queried/written in `app.py`)
     * `import psycopg2` at `app.py:4` (redundant top-level import)
     * `app.py:334-336` empty `else: pass`
     * `app.py:303` session creation logic
   - Confirm if any other function, helper, or SQL object is unused.
3. ABSOLUTE CONSTRAINT: Strictly read-only analysis. DO NOT modify any code.
4. Write your review report to `C:\Users\david\Desktop\Gestionale_Macelleria\.agents\reviewer_backend\backend_review.md` and provide a 5-section `handoff.md` with explicit APPROVE/REQUEST_CHANGES verdict.
5. Send a completion message back to orchestrator.
