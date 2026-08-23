# BRIEFING — 2026-08-23T11:00:37Z

## Mission
Investigate backend and database logic for dynamic meat load (Carico Merci) in Flask app.py and database.sql, providing exact validation rules, queries, and migrations.

## 🔒 My Identity
- Archetype: explorer
- Roles: Backend & Database Explorer
- Working directory: c:\Users\david\Desktop\Gestionale_Macelleria\.agents\explorer_carico_be
- Original parent: 09d1bc6c-4840-4880-8c86-10aacc9a7bdd
- Milestone: milestone_1_survey_and_spec

## 🔒 Key Constraints
- Read-only investigation — do NOT implement in project source code
- Produce structured analysis.md and handoff.md with 5 components
- Examine /carico GET, /salva_carico POST, database.sql, LOTTO_MADRE schema, conditional validation, NULL/empty string handling, ALTER TABLE statement

## Current Parent
- Conversation ID: 09d1bc6c-4840-4880-8c86-10aacc9a7bdd
- Updated: 2026-08-23T11:00:37Z

## Investigation State
- **Explored paths**: `app.py` (/carico, /salva_carico, /magazzino, /produci_preparato, /stampa_etichetta_taglio, /download_excel), `database.sql` (LOTTO_MADRE, ARTICOLO), `templates/carico.html`, `templates/magazzino.html`, `templates/etichetta_taglio.html`.
- **Key findings**:
  - `/carico` GET already provides `articoli_per_categoria` with all necessary metadata; no backend GET changes required.
  - `/salva_carico` POST requires DB lookup for `categoria`, conditional validation (meat vs non-meat), string/date sanitization (`None` for SQL `NULL`), and updated INSERT into `LOTTO_MADRE` with 9 parameters including `data_macellazione`.
  - `database.sql` schema and PostgreSQL migration require adding `data_macellazione DATE` and dropping `NOT NULL` on `data_scadenza`.
- **Unexplored areas**: None for backend/DB scope.

## Key Decisions Made
- Specified exact DB migration SQL: `ALTER TABLE LOTTO_MADRE ADD COLUMN IF NOT EXISTS data_macellazione DATE; ALTER TABLE LOTTO_MADRE ALTER COLUMN data_scadenza DROP NOT NULL;`.
- Specified authoritative DB-backed category lookup in `salva_carico` instead of trusting form parameters.
- Documented full implementation snippets in `analysis.md` and `handoff.md`.

## Artifact Index
- `DISPATCH.md` — Task instructions
- `BRIEFING.md` — Persistent working memory
- `progress.md` — Heartbeat and status tracking
- `analysis.md` — In-depth technical analysis and code snippets
- `handoff.md` — 5-Component handoff report
