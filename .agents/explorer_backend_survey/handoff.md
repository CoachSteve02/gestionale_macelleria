# Handoff Report — Backend & Database Architecture & Dead Code Survey

**Agent**: `explorer_backend_survey`  
**Date**: 2026-08-20  
**Target Repository**: `C:\Users\david\Desktop\Gestionale_Macelleria`  
**Handoff Type**: Hard (Task Complete)

---

## 1. Observation

Direct observations from inspection of backend files (`app.py`, `database.sql`, `static/js/status_monitor.js`, `templates/*.html`, `src/App.tsx`, `README.md`):

1. **Flask Application Structure (`app.py`)**:
   - Lines 1-10: Imports include standard modules (`os`, `datetime`, `threading`, `tempfile`), Flask utilities (`render_template`, `request`, `redirect`, `url_for`, `flash`, `send_file`, `jsonify`), psycopg2 modules (`psycopg2`, `SimpleConnectionPool`, `RealDictCursor`), `pandas`, `dotenv`.
   - Line 4: `import psycopg2` is present, while line 5 imports `SimpleConnectionPool` from `psycopg2.pool` and line 6 imports `RealDictCursor` from `psycopg2.extras`. No direct call to `psycopg2.*` occurs in `app.py`.
   - Lines 26-31: Context processor `@app.context_processor def inject_excel_filename()` returns `{'excel_filename': nome_file}`.
   - Lines 34-38: Database connection pool `db_pool = SimpleConnectionPool(minconn=1, maxconn=10, dsn=...)`.
   - Lines 65-144: `def aggiorna_file_excel()` runs 3 SQL queries (`query_carichi`, `query_preparati`, `query_haccp`) and writes to sheets `'Carichi_Magazzino'`, `'Prodotti_Preparati'`, `'Registro_HACCP_Completo'` using `openpyxl`.
   - Lines 146-477: 10 Flask routes defined:
     - `GET /download_excel` (`download_excel` in `app.py:146-166`)
     - `GET /` (`index` in `app.py:167-194`)
     - `GET /carico` (`carico` in `app.py:195-214`)
     - `POST /salva_carico` (`salva_carico` in `app.py:215-263`)
     - `GET /magazzino` (`magazzino` in `app.py:264-279`)
     - `POST /produci_preparato/<int:id_articolo>` (`produci_preparato` in `app.py:280-348`)
     - `GET /stampa_etichetta/<int:id_lotto_preparato>` (`stampa_etichetta` in `app.py:349-391`)
     - `GET /stampa_etichetta_taglio/<int:id_lotto_madre>` (`stampa_etichetta_taglio` in `app.py:392-433`)
     - `POST /chiudi_sessione` (`chiudi_sessione` in `app.py:434-463`)
     - `GET /api/db_status` (`db_status` in `app.py:464-477`)
   - Lines 303-304: `cursor.execute("INSERT INTO SESSIONE_LAVORAZIONE (operatore) VALUES ('Operatore Banco') RETURNING id_sessione")` is executed unconditionally on every production click.
   - Lines 334-336: `else: # Registra tracciabilità mancante/vuota se l'ingrediente manca dal magazzino pass` is an empty branch.

2. **Database Definition (`database.sql`)**:
   - Tables defined: `articolo`, `sessione_lavorazione`, `lotto_madre`, `ricetta`, `ricetta_riga`, `lotto_preparato`, `composizione_lavorazione`.
   - Sequences defined: `articolo_id_articolo_seq`, `sessione_lavorazione_id_sessione_seq`, `lotto_madre_id_lotto_madre_seq`, `ricetta_id_ricetta_seq`, `ricetta_riga_id_ricetta_riga_seq`, `lotto_preparato_id_lotto_preparato_seq`, `composizione_lavorazione_id_composizione_seq`.
   - Indexes: `idx_articolo_tipo` ON `articolo (tipo_categoria)`, `idx_ricetta_attiva` UNIQUE ON `ricetta (id_articolo_preparato)` WHERE `(attiva = true)`.
   - View: `vw_etichetta_preparato` joining `lotto_preparato`, `ricetta`, `ricetta_riga`, `articolo`.
   - Column `lotto_madre.flg_lotto_del_giorno`: Defined at `database.sql:94` with `DEFAULT false`. Read in `app.py:84` and `app.py:324`. Not written in `salva_carico` (`app.py:245-252`) or anywhere else.
   - Columns `ricetta.versione` (line 122) and `ricetta.data_creazione` (line 124): Defined in DDL, never referenced in `app.py` or templates.

3. **Frontend Integration**:
   - `templates/header.html`: Links to `url_for('index')`, `url_for('carico')`, `url_for('magazzino')`.
   - `templates/footer.html`: Links to `url_for('download_excel')`, form submits to `url_for('chiudi_sessione')`, displays `{{ excel_filename }}`, includes `static/js/status_monitor.js`.
   - `templates/index.html`: Links to `url_for('stampa_etichetta_taglio')`, form action `url_for('produci_preparato')`.
   - `templates/carico.html`: Form action `url_for('salva_carico')`.
   - `templates/magazzino.html`: Links to `url_for('stampa_etichetta_taglio')`.
   - `static/js/status_monitor.js`: Calls `fetch('/api/db_status')` on page load and every 30s.
   - `README.md` (line 13) & `src/App.tsx` (lines 28-30): React files in `src/` are scaffolding artifacts from AI Studio.

---

## 2. Logic Chain

1. **Route Cohesion**:
   - Observation: Every route defined in `app.py` has a corresponding link, form action, or JS fetch in `templates/*.html` or `static/js/*.js`, or is the redirect target of a state mutation.
   - Deduction: There are no orphaned HTTP routes or dead API endpoints in `app.py`.

2. **Database Field Utilization**:
   - Observation: `LOTTO_MADRE.flg_lotto_del_giorno` has default `false`. Queries filter/order by it (`ORDER BY flg_lotto_del_giorno DESC`). However, `salva_carico` inserts only `(id_articolo, codice_lotto_fornitore, fornitore, data_scadenza, paese_nascita, paese_allevamento, paese_macellazione, paese_sezionamento)` without `flg_lotto_del_giorno`, and no UI input exists for it in `carico.html`.
   - Deduction: `flg_lotto_del_giorno` is an unpopulated/dead write column. In runtime, it always equals `false`.
   - Observation: `RICETTA.versione` and `RICETTA.data_creazione` exist in `database.sql` lines 122 and 124. Searching all `.py` and `.html` files reveals zero references.
   - Deduction: These two columns are unreferenced dead schema fields.

3. **Backend Logic & Code Cleanup**:
   - Observation: `import psycopg2` at `app.py:4` is never accessed directly as an identifier; `SimpleConnectionPool` and `RealDictCursor` are imported separately.
   - Deduction: Top-level `import psycopg2` is redundant.
   - Observation: `produci_preparato` executes `INSERT INTO SESSIONE_LAVORAZIONE` on line 303 for every produced item rather than checking for an active session of the day.
   - Deduction: This produces an 1:1 session-to-item ratio rather than a true batch work session, causing `chiudi_sessione` to close N sessions at once.

---

## 3. Caveats

- **Database Runtime Data**: The investigation analyzed `database.sql` (schema DDL). No live PostgreSQL database instance or SQLite file was connected/queried during this read-only inspection.
- **Environment File**: `.env` was confirmed present in root but not inspected directly to preserve security credentials; configuration parameter names were verified from `app.py` and `README.md`.
- No caveats regarding backend route mapping or DDL parsing.

---

## 4. Conclusion

1. The Flask backend (`app.py`) is well-structured and fully wired to its Jinja2 templates and status polling script. There are zero dead or unreferenced Flask routes.
2. The database schema (`database.sql`) contains 2 unreferenced columns (`ricetta.versione`, `ricetta.data_creazione`) and 1 zombie column (`lotto_madre.flg_lotto_del_giorno` which is never set to TRUE by any application logic).
3. Minor code cleanliness opportunities exist: remove redundant `import psycopg2` (`app.py:4`), address empty `else: pass` in ingredient matching (`app.py:334-336`), and consider session reuse in `produci_preparato` (`app.py:303`).
4. Full mapping details and cross-reference matrices have been saved in `C:\Users\david\Desktop\Gestionale_Macelleria\.agents\explorer_backend_survey\backend_survey.md`.

---

## 5. Verification Method

To independently verify these findings:
1. Inspect `app.py` lines 1-11, 26-31, 81-109, 146-477 to verify all route definitions, imports, and queries.
2. Inspect `database.sql` lines 20-270 to verify all table, column, index, and view definitions.
3. Check `templates/` and `static/js/status_monitor.js` to verify references to each endpoint.
4. Verify absence of write operations for `flg_lotto_del_giorno` in `salva_carico` (`app.py:245-252`).
5. Verify absence of queries targeting `ricetta.versione` and `ricetta.data_creazione` across `app.py`.
