# Backend & Database Quality Review and Adversarial Analysis Report
**Milestone**: Carico Merci HACCP Dynamic Form  
**Reviewer**: Backend & Database Reviewer / Adversarial Critic (`reviewer_carico_be`)  
**Date**: 2026-08-23  
**Verdict**: **APPROVE**  

---

## 1. Executive Summary

This report documents the independent quality review and adversarial challenge of the backend and database implementation for the "Carico Merci HACCP Dynamic Form" feature in `Gestionale_Macelleria`.

The reviewed artifacts include:
- `app.py`: `init_db_migrations()`, `/carico`, `/salva_carico`, `/magazzino`, `/stampa_etichetta_taglio`, `aggiorna_file_excel`, `/produci_preparato`
- `database.sql`: `LOTTO_MADRE` table schema and initial data
- `templates/etichetta_taglio.html`: Thermal label template rendering logic
- `test_carico_verification.py`: Automated test suite for regression and validation testing

**Final Verdict**: **APPROVE**. All requirements (R1–R4) from `ORIGINAL_REQUEST.md` and the dispatch specification have been implemented rigorously with authentic business logic, parameterized SQL security, resilient error handling, input sanitization, and defensive non-regression safeguards. No integrity violations or cheating facades were found.

---

## 2. Quality Review & Evidence Chain

### 2.1 Database Schema and DDL Migrations (R2)

#### Observations:
1. **`database.sql` (`LOTTO_MADRE` DDL, lines 10–24)**:
   ```sql
   CREATE TABLE LOTTO_MADRE (
       id_lotto_madre SERIAL PRIMARY KEY,
       id_articolo INT NOT NULL REFERENCES ARTICOLO(id_articolo),
       codice_lotto_fornitore VARCHAR(100) NOT NULL,
       fornitore VARCHAR(255) NOT NULL,
       data_carico TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       data_scadenza DATE,
       data_macellazione DATE,
       paese_nascita VARCHAR(100),
       paese_allevamento VARCHAR(100),
       paese_macellazione VARCHAR(100),
       paese_sezionamento VARCHAR(100),
       flg_lotto_del_giorno BOOLEAN DEFAULT FALSE
   );
   ```
   - `data_macellazione DATE` is explicitly present as a nullable date column.
   - `data_scadenza DATE` is nullable (omits `NOT NULL`).

2. **`app.py` (`init_db_migrations()`, lines 39–55)**:
   ```python
   def init_db_migrations():
       """Esegue migrazioni DDL idempotenti all'avvio dell'applicazione."""
       try:
           conn = db_pool.getconn()
           try:
               with conn.cursor() as cursor:
                   cursor.execute("""
                       ALTER TABLE LOTTO_MADRE ADD COLUMN IF NOT EXISTS data_macellazione DATE;
                       ALTER TABLE LOTTO_MADRE ALTER COLUMN data_scadenza DROP NOT NULL;
                   """)
               conn.commit()
           finally:
               db_pool.putconn(conn)
       except Exception as e:
           app.logger.warning(f"Migrazione DB non eseguita o database non raggiungibile: {e}")
   ```
   - Automatically executed at module import (line 55).
   - Fully idempotent: uses `ADD COLUMN IF NOT EXISTS` and `ALTER COLUMN data_scadenza DROP NOT NULL`.
   - Safe pool management: wraps connection acquisition in `try...finally` with `db_pool.putconn(conn)`.
   - Safe failure mode: catches any database connection exception and logs a warning without crashing ungracefully.

---

### 2.2 Server-Side Validation in `/salva_carico` (R3)

#### Observations & Logic Verification:
1. **Input Sanitization (`app.py:234-246`)**:
   ```python
   id_articolo = (request.form.get('id_articolo') or '').strip() or None
   codice_lotto_fornitore = (request.form.get('codice_lotto_fornitore') or '').strip() or None
   fornitore = (request.form.get('fornitore') or '').strip() or None
   data_scadenza_str = (request.form.get('data_scadenza') or '').strip() or None
   data_macellazione_str = (request.form.get('data_macellazione') or '').strip() or None
   paese_nascita = (request.form.get('paese_nascita') or '').strip() or None
   paese_allevamento = (request.form.get('paese_allevamento') or '').strip() or None
   paese_macellazione = (request.form.get('paese_macellazione') or '').strip() or None
   paese_sezionamento = (request.form.get('paese_sezionamento') or '').strip() or None
   ```
   - Whitespace strings (`'   '`) and empty form fields are converted to `None` (Python `None` maps to PostgreSQL `NULL`).
   - Common mandatory fields (`id_articolo`, `codice_lotto_fornitore`, `fornitore`) are checked upfront.

2. **Authoritative DB Category Lookup (`app.py:251-260`)**:
   ```python
   cursor.execute("SELECT id_articolo, denominazione, categoria FROM ARTICOLO WHERE id_articolo = %s;", (id_articolo,))
   articolo = cursor.fetchone()
   if not articolo:
       flash('Articolo selezionato non valido o inesistente.', 'error')
       return redirect(url_for('carico'))

   categoria = (articolo['categoria'] or '').strip().lower()
   is_carne = categoria in ['bovino', 'suino', 'avicolo']
   ```
   - Validates that the selected `id_articolo` actually exists in `ARTICOLO`.
   - Does not trust any client-supplied category; reads the category directly from the database.
   - Case-insensitive and whitespace-resilient comparison via `.strip().lower()`.

3. **Safe Date Parsing and Semantic Range Validation (`app.py:263-288`)**:
   - `datetime.datetime.strptime(..., '%Y-%m-%d').date()` ensures format conformance. Invalid date strings trigger `ValueError` and flash user-friendly error messages rather than 500 errors.
   - `data_scad_parsed < datetime.date.today()`: rejects expired lots upon intake.
   - `data_macell_parsed > datetime.date.today()`: rejects impossible future slaughter dates.
   - `data_scad_parsed < data_macell_parsed`: rejects chronological contradictions where expiration precedes slaughter.

4. **Meat Category Conditional Validation (`app.py:290-298`)**:
   - For `is_carne == True` (`Bovino`, `Suino`, `Avicolo`):
     - `not all([paese_nascita, paese_allevamento, paese_macellazione, paese_sezionamento])`: strictly requires all 4 origin country fields.
     - `not data_macell_parsed and not data_scad_parsed`: enforces that at least one of slaughter date or expiration date is provided.

5. **Non-Meat Category Validation & Origin Sanitization (`app.py:299-310`)**:
   - For `is_carne == False` (Spezie, Latticini, Farinacei, Uova, Involucri, etc.):
     - `not data_scad_parsed`: requires `data_scadenza`.
     - Explicitly resets all origin fields and slaughter date to `None`:
       ```python
       paese_nascita = None
       paese_allevamento = None
       paese_macellazione = None
       paese_sezionamento = None
       data_macell_parsed = None
       ```
     - Guarantees database consistency even if origin values were maliciously or accidentally posted.

6. **Parameterized 9-Column SQL Insertion (`app.py:312-322`)**:
   ```python
   cursor.execute("""
       INSERT INTO LOTTO_MADRE (
           id_articolo, codice_lotto_fornitore, fornitore, data_scadenza, 
           paese_nascita, paese_allevamento, paese_macellazione, paese_sezionamento,
           data_macellazione
       ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
   """, (
       id_articolo, codice_lotto_fornitore, fornitore, data_scad_parsed, 
       paese_nascita, paese_allevamento, paese_macellazione, paese_sezionamento,
       data_macell_parsed
   ))
   ```
   - 100% parameterized query binding using psycopg2 `%s` tokens.
   - Zero string formatting or concatenation (SQL injection proof).
   - Atomic transaction management: `conn.commit()` on success, `conn.rollback()` on exception.

---

### 2.3 Non-Regression Verification across Dependent Routes

1. **`/carico` (`app.py:212-230`)**:
   - Groups articles by `categoria` for `<optgroup>` rendering in `templates/carico.html`.
   - Populates `data-categoria="{{ categoria }}"` on each `<option>` for seamless client-side visibility toggles.
2. **`/magazzino` (`app.py:334-349` & `templates/magazzino.html:38`)**:
   - Query selects `lm.*`, correctly handling new column `data_macellazione`.
   - Template renders `data_scadenza` with fallback: `{{ lotto.data_scadenza.strftime('%d/%m/%Y') if lotto.data_scadenza else '-' }}` preventing `NoneType.strftime` crashes.
3. **`/stampa_etichetta_taglio` (`app.py:472-513` & `templates/etichetta_taglio.html:149-159`)**:
   - Route selects `data_macellazione` and origin fields.
   - Thermal template conditionally renders:
     ```jinja2
     {% if taglio.data_scadenza %}
         <div style="font-size: 10px; font-weight: normal;">Da cons. entro:</div>
         {{ taglio.data_scadenza.strftime('%d/%m/%Y') }}
     {% elif taglio.data_macellazione %}
         <div style="font-size: 10px; font-weight: normal;">Macellato il:</div>
         {{ taglio.data_macellazione.strftime('%d/%m/%Y') }}
     {% else %}
         <div style="font-size: 10px; font-weight: normal;">Da cons. entro:</div>
         N/D
     {% endif %}
     ```
   - Preserves strict Bovino origin validation before label printing (`app.py:495-509`).
4. **`aggiorna_file_excel` (`app.py:82-162`)**:
   - `query_carichi` includes `data_macellazione` in the exported columns.
   - Nullable dates are handled cleanly by pandas `to_excel` without errors.
5. **`/produci_preparato` (`app.py:350-428`)**:
   - Line 400 query updated to:
     ```sql
     SELECT id_lotto_madre FROM LOTTO_MADRE 
     WHERE id_articolo = %s AND (data_scadenza IS NULL OR data_scadenza >= CURRENT_DATE)
     ORDER BY data_carico DESC LIMIT 1
     ```
   - Crucial fix: prevents exclusion of fresh meat cuts entered with only `data_macellazione` (`data_scadenza IS NULL`).

---

## 3. Adversarial Stress-Testing & Attack Surface Analysis

| # | Attack Scenario / Edge Case | Expected System Behavior | Actual Implementation Behavior | Verdict |
|---|---|---|---|---|
| **A1** | **Client-side bypass**: POST request for non-meat article containing arbitrary origin country text and slaughter date. | Backend must strip origin/slaughter fields to `NULL`. | `app.py:305-309` resets `paese_* = None` and `data_macell_parsed = None`. | **PASS** |
| **A2** | **Category spoofing**: Manipulating form DOM to submit non-meat product with fake meat `data-categoria`. | Backend must query DB for genuine category. | `app.py:252` executes `SELECT categoria FROM ARTICOLO WHERE id_articolo = %s`. Ignores client metadata. | **PASS** |
| **A3** | **Whitespace injection**: Submitting spaces `'   '` for mandatory country or date fields. | Whitespace treated as empty / `None` and rejected. | `(request.form.get(...) or '').strip() or None` turns whitespace into `None`, failing `all([...])`. | **PASS** |
| **A4** | **Future slaughter date**: Submitting `data_macellazione` set to tomorrow. | Rejected with error flash. | `data_macell_parsed > datetime.date.today()` triggers error redirect. | **PASS** |
| **A5** | **Past expiration date**: Submitting `data_scadenza` set to yesterday. | Rejected with error flash. | `data_scad_parsed < datetime.date.today()` triggers error redirect. | **PASS** |
| **A6** | **Contradictory dates**: Submitting `data_scadenza < data_macellazione`. | Rejected with error flash. | `data_scad_parsed < data_macell_parsed` triggers error redirect. | **PASS** |
| **A7** | **Meat intake with slaughter date only**: Fresh meat cut without supplier expiration date. | Accepted, inserted with `data_scadenza = NULL`. | Permitted by `if not data_macell_parsed and not data_scad_parsed`, inserted cleanly. | **PASS** |
| **A8** | **Non-existent article ID**: Submitting `id_articolo = 999999` or non-integer string. | Catches missing record or SQL cast error cleanly. | Handled via `if not articolo` check and general `try...except` block with transaction rollback. | **PASS** |
| **A9** | **SQL Injection**: Injecting SQL tokens in `codice_lotto_fornitore` or `fornitore`. | Treated as literal string values. | Fully parameterized query binding via `%s`. | **PASS** |
| **A10**| **Thermal label printing with NULL expiration**: Accessing `/stampa_etichetta_taglio/<id>` on a lot having only slaughter date. | Renders slaughter date without crashing on `.strftime()`. | `templates/etichetta_taglio.html:149-159` guards with `{% if taglio.data_scadenza %} ... {% elif taglio.data_macellazione %}`. | **PASS** |

---

## 4. Integrity and Anti-Cheating Assessment

- **No Hardcoded Outputs**: Code performs live database queries, parameter bindings, and dynamic checks.
- **No Facades or Dummy Implementations**: All logic routes are fully functional end-to-end.
- **No Task Bypassing**: Schema, migrations, validation, and non-regression fixes are implemented directly in `app.py`, `database.sql`, and `templates/etichetta_taglio.html`.
- **Independent Verification**: Evaluated directly against codebase and test matrix.

---

## 5. Review Summary & Recommendation

The backend and database implementation is complete, secure, robust, and fully compliant with project standards.

**Verdict**: **APPROVE**
