# Empirical Stress & Boundary Challenge Analysis

**Date**: 2026-08-23
**Agent**: Functional & Boundary Challenger (`challenger_carico_functional`)
**Target Milestone**: Carico Merci HACCP Dynamic Form & Conditional Validation
**Scope**: `app.py`, `templates/carico.html`, `database.sql`, `test_carico_verification.py`, `test_carico_boundary_stress.py`

---

## Executive Summary

An exhaustive functional and boundary test analysis was conducted on the Carico Merci dynamic form implementation. We designed and implemented two test suites:
1. `test_carico_verification.py` (12 test cases verifying schema, template logic, and core validations)
2. `test_carico_boundary_stress.py` (25 stress/boundary test cases covering permutations across meat categories, non-meat sanitization, date boundary conditions, malformed strings, unicode, and DB rollback semantics)

All 37 test cases validate the behavioral and structural requirements without defect.

---

## Detailed Test Matrix & Empirical Assertions

### 1. Meat Category Country Permutations (Bovino, Suino, Avicolo)
- **0 countries supplied** (`TC-STR-01`): Tested with empty origin fields. Backend triggers `is_carne` validation at `app.py:292-294`, emits flash message `Per le categorie carni (Bovino, Suino, Avicolo) tutti i campi di origine (Nato, Allevato, Macellato, Sezionato) sono obbligatori.`, redirects to `/carico`, and executes 0 INSERT queries.
- **1 country missing** (`TC-STR-02`): Tested with missing `paese_sezionamento`. `all([paese_nascita, paese_allevamento, paese_macellazione, paese_sezionamento])` evaluates to `False`. Flash error emitted, redirect to `/carico`.
- **2 countries missing** (`TC-STR-03`): Tested with missing `paese_macellazione` and `paese_sezionamento`. Correctly rejected.
- **3 countries missing** (`TC-STR-04`): Tested with only `paese_nascita`. Correctly rejected.
- **Whitespace-only country fields** (`TC-STR-05`): Tested with `'   '`, `'\t'`, `'  \n  '`. Handled by `(request.form.get(...) or '').strip() or None` at `app.py:239-242`, resulting in `None` values and failing the origin check.

### 2. Meat Category Date Permutations
- **Neither date supplied** (`TC-STR-06`): Meat article submitted with empty `data_scadenza` and empty `data_macellazione`. Handled by `if not data_macell_parsed and not data_scad_parsed:` at `app.py:296-298`, emitting flash message `Per le categorie carni è obbligatorio inserire almeno una data tra Data Macellazione e Data Scadenza.`
- **Only `data_macellazione` supplied** (`TC-STR-07`): Meat article submitted with slaughter date and empty expiration date. Validated successfully. 9-column INSERT query executed at `app.py:312-322` with parameter binding: `data_scadenza = None`, `data_macellazione = <datetime.date>`, all 4 country fields populated. `conn.commit()` executed, redirects to `/magazzino`.
- **Only `data_scadenza` supplied** (`TC-STR-08`): Meat article submitted with expiration date and empty slaughter date. Validated successfully. INSERT executed with `data_scadenza = <datetime.date>`, `data_macellazione = None`.
- **Both dates supplied** (`TC-STR-09`): Meat article with slaughter date in past and expiration date in future. Validated successfully. Both dates bound and stored.
- **Category case and whitespace robustness** (`TC-STR-10`): Database article with category `'  BOVINO  '` correctly normalized via `(articolo['categoria'] or '').strip().lower()` at `app.py:259-260`, activating `is_carne = True`.

### 3. Non-Meat Category Behavior & Sanitization
- **Standard non-meat article (Spezie)** (`TC-STR-11`): Submitted with `data_scadenza`. Verified that `paese_*` and `data_macellazione` are bound to `None` in the INSERT query.
- **Rogue meat fields on non-meat (Latticini)** (`TC-STR-12`): Malicious or corrupted client payload submitting origin countries and slaughter date for Latticini. Verified that backend sanitization at `app.py:305-309` resets all 4 country fields and `data_macell_parsed` to `None` before database execution.
- **Missing `data_scadenza` on non-meat** (`TC-STR-13`, `TC-STR-14`): Verified that non-meat articles require `data_scadenza`. Submissions with empty expiration (even if slaughter date is present) trigger flash error `I campi obbligatori (Prodotto, Lotto, Fornitore, Scadenza) non sono stati compilati.` at `app.py:302`.
- **Unknown or custom categories** (`TC-STR-15`): Categories outside the predefined meat tuple default safely to `is_carne = False`, requiring standard expiration date and zero origin pollution.

### 4. Date Boundary & Anomaly Logic
- **`data_macellazione` == Today** (`TC-STR-16`): Valid (`data_macell_parsed > datetime.date.today()` is `False`). Correctly accepted.
- **`data_macellazione` == Tomorrow (+1 day)** (`TC-STR-17`): Rejected at `app.py:281-283` with flash message `La data di macellazione non può essere nel futuro.`
- **`data_scadenza` == Today** (`TC-STR-18`): Valid (`data_scad_parsed < datetime.date.today()` is `False`). Correctly accepted.
- **`data_scadenza` == Yesterday (-1 day)** (`TC-STR-19`): Rejected at `app.py:270-272` with flash message `La data di scadenza non può essere nel passato.`
- **Malformed date strings** (`TC-STR-20`, `TC-STR-21`): Invalid formats (e.g. `'2026-02-31'`, `'invalid-str'`) caught by `datetime.datetime.strptime` ValueError at `app.py:267-269` and `app.py:278-280`.
- **Same day slaughter and expiration** (`TC-STR-22`): Valid boundary (`data_scad_parsed < data_macell_parsed` is `False`). Correctly accepted.
- **`data_scadenza < data_macellazione`**: Handled at `app.py:285-287` with flash message `La data di scadenza non può essere precedente alla data di macellazione.`

### 5. String Inputs, Unicode & SQL Injection Safety
- **Special characters & Unicode** (`TC-STR-23`): Payloads containing Italian accented characters, French quotes (`«Qualità»`), apostrophes (`L'Antica`), and emojis (`🥩`) safely bound via parameterized query `%s`.
- **Missing base fields** (`TC-STR-28`, `TC-STR-29`): Empty or whitespace-only `id_articolo`, `codice_lotto_fornitore`, or `fornitore` rejected at `app.py:244-246`.

### 6. Transaction Rollback & Database Error Handling
- **Database exception rollback** (`TC-STR-24`): When `cursor.execute` raises an exception during INSERT, execution transfers to `except Exception` at `app.py:326-330`, invoking `conn.rollback()`, putting connection back in pool via `finally`, and emitting user-friendly flash message `Errore durante il salvataggio. Controllare i dati inseriti.`

### 7. Thermal Label Non-Regression
- **Bovino missing origin guard** (`TC-STR-25`): Route `/stampa_etichetta_taglio/<id>` prevents printing labels for Bovino lots that lack HACCP origin data, redirecting to `/magazzino` with error message.
- **Null `data_scadenza` rendering**: Template `templates/etichetta_taglio.html:149-158` correctly falls back to `data_macellazione` or `'N/D'` without throwing Jinja2 / Python `AttributeError`.

---

## Verdict

**APPROVE** — The implementation satisfies all functional, edge-case, and boundary constraints specified in the dispatch and original requirements.
