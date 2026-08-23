# Handoff Report: QA & Verification Strategy for Carico Merci (HACCP)

## 1. Observation
1. **Project Environment & Dependencies (`requirements.txt:1-5`)**:
   - `Flask==3.0.0`, `psycopg2-binary==2.9.9`, `pandas==2.2.0`, `openpyxl==3.1.2`, `python-dotenv==1.0.0`.
   - Flask 3.0 provides a full-featured built-in test client (`app.test_client()`) supporting session tracking, flash message inspection, redirect following, and template rendering without running an external web server.

2. **Database & Application Configuration (`app.py:20-41`)**:
   - PostgreSQL connection pool initialized via `SimpleConnectionPool` with `os.environ.get('DATABASE_URL')`.
   - Secret key configured via `os.environ.get('SECRET_KEY')`.
   - Database schema `database.sql:10-23` defines table `LOTTO_MADRE` with origin columns `paese_nascita`, `paese_allevamento`, `paese_macellazione`, `paese_sezionamento`, but currently lacks `data_macellazione DATE`.

3. **Current Routes Implementation**:
   - `GET /carico` (`app.py:194-212`): Queries `ARTICOLO WHERE tipo_categoria IN ('TAGLIO', 'VARIO')`, groups into `articoli_per_categoria` dict passed to `templates/carico.html`.
   - `POST /salva_carico` (`app.py:214-261`): Currently validates only base presence of `id_articolo, codice_lotto_fornitore, fornitore, data_scadenza` without checking the meat category or origin completeness.
   - `GET /magazzino` (`app.py:263-277`): Queries `SELECT lm.*, a.denominazione, a.tipo_categoria FROM LOTTO_MADRE lm JOIN ARTICOLO a ...`.
   - `GET /stampa_etichetta_taglio/<id>` (`app.py:401-441`): Enforces presence of origin fields for Bovino articles before rendering `templates/etichetta_taglio.html`.
   - `GET /api/db_status` (`app.py:473-485`): Returns JSON health check `{"status": "ok"}`.
   - `GET /download_excel` (`app.py:145-164`): Generates on-demand multi-tab HACCP Excel workbook using pandas.

4. **DOM & Template Inspection (`templates/carico.html:14-62` & `templates/etichetta_taglio.html:150`)**:
   - In `templates/carico.html:19`, `<option>` elements lack `data-categoria` attributes.
   - In `templates/carico.html:45-62`, origin inputs are not isolated in a distinct card and lack `data_macellazione`.
   - In `templates/etichetta_taglio.html:150`, line executes `{{ taglio.data_scadenza.strftime('%d/%m/%Y') }}` which would raise an `AttributeError` if `taglio.data_scadenza` is `None` (potential regression risk if `data_scadenza` is made nullable).

---

## 2. Logic Chain
1. **Frontend Verification Logic**:
   - From Obs 3 & 4, when `data-categoria="{{ categoria }}"` is rendered on `<option>` tags, client-side vanilla JavaScript can read `selectedOption.dataset.categoria` instantaneously on the `change` event.
   - To prevent HTML5 form blocking (`An invalid form control is not focusable`), whenever the category is NOT in `['bovino', 'suino', 'avicolo']`, `#sezione-tracciabilita` must receive the `hidden` CSS class AND country inputs must be set to `required = false`.
   - When a meat category is selected, the `hidden` class is removed and country inputs are set to `required = true`.

2. **Backend Validation Logic**:
   - From Obs 3, `/salva_carico` must query `ARTICOLO` to retrieve the true `categoria` of `id_articolo`.
   - If `categoria.lower() in ['bovino', 'suino', 'avicolo']`:
     * Validate that `paese_nascita`, `paese_allevamento`, `paese_macellazione`, `paese_sezionamento` are non-empty strings.
     * Validate that at least one of `data_macellazione` or `data_scadenza` is provided.
   - If `categoria` is non-meat:
     * Country fields and `data_macellazione` are optional and must be converted from empty strings `""` to `None` so they are stored as `NULL` in PostgreSQL without date syntax parsing errors.

3. **Database Migration Verification Logic**:
   - From Obs 2, executing `ALTER TABLE LOTTO_MADRE ADD COLUMN IF NOT EXISTS data_macellazione DATE;` satisfies idempotency and schema compatibility.
   - Updating `database.sql` ensures fresh deployments match the production database structure.

4. **Non-Regression Logic**:
   - From Obs 3 & 4, `SELECT lm.*` in `/magazzino` seamlessly absorbs `data_macellazione`.
   - To avoid potential runtime errors in `etichetta_taglio.html:150`, date rendering should use defensive checking `{{ taglio.data_scadenza.strftime('%d/%m/%Y') if taglio.data_scadenza else '-' }}` or ensure `data_scadenza` is populated.

---

## 3. Caveats
- **Permission Limitations**: Terminal command execution via `run_command` and direct file read of `.env` timed out waiting for user interaction. All testing designs and verification suites are therefore designed as self-contained Python scripts (`test_carico_verification.py`) and standalone test cases using Flask's native WSGI test harness (`app.test_client()`), requiring no external dependencies beyond those already in `requirements.txt`.
- **Date Formatting Constraints**: The backend must strictly validate date inputs with `strptime('%Y-%m-%d')` and guard against future slaughter dates or past expiration dates.
- **Database Connection**: Automated test execution assumes a reachable PostgreSQL instance defined in `.env` / `DATABASE_URL`. If the database is unreachable, `app.py` logging records pool errors and test assertions fail gracefully.

---

## 4. Conclusion
1. The QA and verification strategy is fully specified and documented in `analysis.md`.
2. A comprehensive 17-point test matrix covering Frontend DOM/JS, Backend conditional validation, Database schema migration, and Non-regression health checks has been established.
3. A complete, standalone Python verification script `test_carico_verification.py` is ready for implementation/execution by the team.

---

## 5. Verification Method

To independently verify the implementation, execute the following steps:

1. **Database Schema Verification**:
   ```sql
   SELECT column_name, data_type, is_nullable 
   FROM information_schema.columns 
   WHERE table_name = 'lotto_madre' AND column_name = 'data_macellazione';
   ```
   *Expected*: 1 row returned with `data_type = 'date'` and `is_nullable = 'YES'`.

2. **Automated Test Suite Execution**:
   Run the verification script provided in `analysis.md`:
   ```bash
   python test_carico_verification.py
   ```
   *Expected*: Output shows all test cases passing (`[PASS] TC-DB-01`, `[PASS] TC-FE-01`, `[PASS] TC-BE-01` through `TC-BE-10`, `[PASS] TC-REG-01` through `TC-REG-06`), exit code 0.

3. **Manual UI Verification**:
   - Run `python app.py` and open `http://localhost:5000/carico`.
   - Select "Carne Macinata Bovino" -> HACCP card appears immediately, country fields are required.
   - Select "Sale Marino Fine" -> HACCP card disappears immediately, country fields are optional/cleared.
   - Submit form for non-meat -> successfully redirects to `/magazzino` with green flash message.
   - Click "🖨️ Stampa Etichetta" on a TAGLIO row in `/magazzino` -> thermal label renders without error.

4. **Invalidation Conditions**:
   - If submitting a non-meat article triggers a browser error "An invalid form control is not focusable", the JS failed to clear `required = false`.
   - If submitting a meat article without country fields succeeds in inserting a record, backend validation in `/salva_carico` was bypassed.
   - If `/download_excel` or `/stampa_etichetta_taglio` raises `500 Internal Server Error`, a schema or `NoneType` regression occurred.
