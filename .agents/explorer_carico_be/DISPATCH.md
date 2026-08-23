# Dispatch for Backend & Database Explorer

## 2026-08-23T10:58:15Z

You are the Backend & Database Explorer.
Your Working Directory is: c:\Users\david\Desktop\Gestionale_Macelleria\.agents\explorer_carico_be
Project Root: c:\Users\david\Desktop\Gestionale_Macelleria
Original Request Path: c:\Users\david\Desktop\Gestionale_Macelleria\.agents\ORIGINAL_REQUEST.md
Your Dispatch file: c:\Users\david\Desktop\Gestionale_Macelleria\.agents\explorer_carico_be\DISPATCH.md

Read ORIGINAL_REQUEST.md and your DISPATCH.md.
Investigate `app.py`, `database.sql`, and database queries:
1. Examine route `/carico` (GET): How items are retrieved, grouped, and passed to `templates/carico.html`.
2. Examine route `/salva_carico` (POST):
   - Current form data parsing (`request.form`).
   - How `categoria` of the selected `id_articolo` should be retrieved (e.g., query `ARTICOLO` table).
   - Backend conditional validation rules:
     * If `categoria` in `('Bovino', 'Suino', 'Avicolo')`: `paese_nascita`, `paese_allevamento`, `paese_macellazione`, `paese_sezionamento` required + at least one of `data_macellazione` or `data_scadenza` required.
     * If other category: country fields and `data_macellazione` are optional.
   - Exact INSERT INTO `LOTTO_MADRE` query updates, adding `data_macellazione` column.
   - Handling of NULL vs empty string values for dates and country fields.
3. Examine `database.sql` and `LOTTO_MADRE` definition:
   - Schema updates needed for `database.sql` (`data_macellazione DATE NULL`).
   - Exact `ALTER TABLE LOTTO_MADRE ADD COLUMN IF NOT EXISTS data_macellazione DATE;` migration SQL statement.
4. Document full findings, concrete code snippets, and exact query definitions in `analysis.md` and `handoff.md` in your working directory.
When finished, send a message to parent with the result summary and handoff path.
