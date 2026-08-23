# Dispatch for Backend & Database Reviewer

Perform an independent, objective review of:
- `app.py` (specifically `/carico`, `/salva_carico`, `init_db_migrations`, `aggiorna_file_excel`, `produci_preparato`, `stampa_etichetta_taglio`)
- `database.sql`
- `templates/etichetta_taglio.html`

Verify:
1. `init_db_migrations()` and `database.sql` schema updates (`data_macellazione DATE NULL` and nullable `data_scadenza`).
2. Server-side validation logic in `/salva_carico`:
   - DB lookup for `categoria`.
   - Meat categories (`Bovino`, `Suino`, `Avicolo`): strictly requires `paese_nascita`, `paese_allevamento`, `paese_macellazione`, `paese_sezionamento` and at least one of `data_macellazione` or `data_scadenza`.
   - Non-meat categories: requires `data_scadenza`, saves origin fields and `data_macellazione` as `NULL`.
   - Proper date parsing, range checks (no future slaughter date, no past expiration date, expiration >= slaughter if both given).
   - Safe psycopg2 query parameter binding (no string concatenation, empty strings converted to `None` for SQL `NULL`).
3. Non-regression across existing routes and reporting features.

Write your findings to `analysis.md` and your verdict (`APPROVE` or `REQUEST_CHANGES`) in `handoff.md`.
