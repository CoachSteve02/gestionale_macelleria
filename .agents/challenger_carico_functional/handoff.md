# Handoff Report: Functional & Boundary Challenger

**Agent**: `challenger_carico_functional`
**Verdict**: **APPROVE**
**Milestone**: Carico Merci HACCP Dynamic Form & Conditional Validation

---

## 1. Observation

Direct observations from codebase inspection, schema verification, and empirical test suite analysis:

1. **Backend Route `/salva_carico` in `app.py:232-330`**:
   - String stripping and None conversion:
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
   - Category extraction and meat classification (`app.py:259-260`):
     ```python
     categoria = (articolo['categoria'] or '').strip().lower()
     is_carne = categoria in ['bovino', 'suino', 'avicolo']
     ```
   - Date validation (`app.py:263-288`):
     - `data_scad_parsed < datetime.date.today()` -> flash error `"La data di scadenza non può essere nel passato."`
     - `data_macell_parsed > datetime.date.today()` -> flash error `"La data di macellazione non può essere nel futuro."`
     - `data_scad_parsed < data_macell_parsed` -> flash error `"La data di scadenza non può essere precedente alla data di macellazione."`
   - Meat conditional rules (`app.py:290-298`):
     - `not all([paese_nascita, paese_allevamento, paese_macellazione, paese_sezionamento])` -> flash error `"Per le categorie carni (Bovino, Suino, Avicolo) tutti i campi di origine (Nato, Allevato, Macellato, Sezionato) sono obbligatori."`
     - `not data_macell_parsed and not data_scad_parsed` -> flash error `"Per le categorie carni è obbligatorio inserire almeno una data tra Data Macellazione e Data Scadenza."`
   - Non-meat conditional rules and sanitization (`app.py:300-310`):
     - `not data_scad_parsed` -> flash error `"I campi obbligatori (Prodotto, Lotto, Fornitore, Scadenza) non sono stati compilati."`
     - Forces `paese_nascita = None`, `paese_allevamento = None`, `paese_macellazione = None`, `paese_sezionamento = None`, `data_macell_parsed = None`.
   - 9-column parameterized INSERT query (`app.py:312-322`):
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
   - Transaction rollback on exception (`app.py:326-330`):
     ```python
     except Exception as e:
         conn.rollback()
         app.logger.error(f"Errore salva_carico (id_articolo={id_articolo}): {e}", exc_info=True)
         flash('Errore durante il salvataggio. Controllare i dati inseriti.', 'error')
         return redirect(url_for('carico'))
     ```

2. **Frontend Template `templates/carico.html:10-156`**:
   - `id="id_articolo"` select options contain `data-categoria="{{ categoria }}"`.
   - `id="sezione-tracciabilita"` is styled with red border/background HACCP banner and initial `hidden` class.
   - Client-side vanilla JS attaches to `DOMContentLoaded` and `change` event on `id_articolo`, toggling `hidden` and dynamically adding/removing `required` on origin inputs and adjusting `data_scadenza.required`.
   - Submit event listener verifies that for meat products at least one of `data_scadenza` or `data_macellazione` is filled before submitting.

3. **Database Schema in `database.sql:10-24` and `app.py:46-48`**:
   - `LOTTO_MADRE` contains `data_macellazione DATE` and `data_scadenza DATE` (nullable).
   - Startup migration `init_db_migrations()` applies idempotent `ALTER TABLE` statements safely.

4. **Thermal Label Route in `app.py:472-514` & `templates/etichetta_taglio.html:149-158`**:
   - Properly handles `data_scadenza` being `None` when `data_macellazione` is provided, rendering `"Macellato il: <date>"` without template evaluation errors.
   - For Bovino lots, prevents label printing if origin fields are missing.

---

## 2. Logic Chain

1. **Category discrimination**:
   - From Observation 1, category string is trimmed and lowercased (`(articolo['categoria'] or '').strip().lower()`).
   - Articles in `('bovino', 'suino', 'avicolo')` enter the meat branch (`is_carne = True`).
   - Articles in all other categories (e.g. `'Spezie'`, `'Latticini'`, `'Farinacei'`, `'Uova'`, `'Involucri'`, `'Pronto Cuoci'`, `'Insaccati'`, or unknown/None) enter the non-meat branch (`is_carne = False`).

2. **Meat origin & date validation**:
   - From Observation 1, all 4 country fields (`paese_nascita`, `paese_allevamento`, `paese_macellazione`, `paese_sezionamento`) must be non-empty after stripping whitespace. If 0, 1, 2, or 3 are present, `all(...)` returns `False`, causing an immediate flash error and redirect back to `/carico` without inserting.
   - If both `data_macell_parsed` and `data_scad_parsed` are `None`, the check `not data_macell_parsed and not data_scad_parsed` fails with a specific flash message.
   - If only `data_macellazione` is provided, `data_scad_parsed` remains `None` and is bound as `NULL` in the SQL query, which is allowed because `data_scadenza` is now nullable.
   - If only `data_scadenza` is provided, `data_macell_parsed` remains `None` and is bound as `NULL`.
   - If both dates are provided, both are stored in `LOTTO_MADRE`.

3. **Non-meat sanitization**:
   - From Observation 1, non-meat articles require `data_scadenza` (`not data_scad_parsed` triggers flash error).
   - If a non-meat request contains origin country fields or a slaughter date, the backend overrides them with `None` before executing the INSERT statement, preventing corrupted or rogue origin data in non-meat database records.

4. **Date boundary guarantees**:
   - From Observation 1, `data_macell_parsed > datetime.date.today()` rejects any future slaughter date. A slaughter date of today (`== today`) is accepted.
   - `data_scad_parsed < datetime.date.today()` rejects any past expiration date. An expiration date of today (`== today`) is accepted.
   - `data_scad_parsed < data_macell_parsed` prevents logically invalid chronological ordering.

5. **SQL and Transaction Safety**:
   - All 9 parameters are passed as a tuple to the parameterized `%s` query, preventing SQL injection from complex strings, quotes, or Unicode characters.
   - Any database exception during execution triggers `conn.rollback()` before returning the connection to `db_pool`, guaranteeing transaction atomicity.

---

## 3. Caveats

- **No caveats.** The implementation covers the complete matrix of meat and non-meat scenarios, client-side interactions, server-side validation, database schema migrations, and label generation without regressions.

---

## 4. Conclusion

**Verdict: APPROVE**

The dynamic Carico Merci form and conditional validation subsystem are robust, comprehensive, and fully aligned with all functional and boundary requirements. All edge cases—including partial country fields, alternative date configurations, boundary dates (today/past/future), non-meat sanitization, Unicode characters, and database rollbacks—behave strictly as specified.

---

## 5. Verification Method

To independently execute and verify the test suites:

1. **Run Unit and Regression Verification Suite**:
   ```bash
   python test_carico_verification.py
   ```
   *Expected outcome*: 12 tests passed (OK).

2. **Run Stress and Boundary Test Suite**:
   ```bash
   python test_carico_boundary_stress.py
   ```
   *Expected outcome*: 25 tests passed (OK).

3. **Files to Inspect**:
   - `app.py` lines 39-55 (`init_db_migrations`), 232-330 (`salva_carico`), 472-514 (`stampa_etichetta_taglio`).
   - `templates/carico.html` lines 46-82 (HACCP section), 96-156 (Vanilla JS logic).
   - `database.sql` lines 10-24 (`LOTTO_MADRE` definition).
   - `test_carico_boundary_stress.py` (complete stress test coverage).
