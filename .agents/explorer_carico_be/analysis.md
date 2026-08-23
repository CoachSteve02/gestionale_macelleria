# Backend & Database Technical Analysis: Dynamic Carico Merci

## 1. Executive Summary

This report documents the backend and database investigation for implementing the dynamic "Carico Merci" (Goods Inward) functionality in the `Gestionale_Macelleria` Flask application.

Key findings:
1. **Route `/carico` (GET)** already retrieves all required article fields (`id_articolo`, `denominazione`, `categoria`, `tipo_categoria`) and groups them by `categoria` into `articoli_per_categoria`. No Python backend modifications are needed for `/carico` GET; the frontend template only needs `data-categoria="{{ art.categoria }}"` on each `<option>`.
2. **Route `/salva_carico` (POST)** requires:
   - Form parsing for `data_macellazione` alongside existing fields.
   - Server-side lookup of `categoria` from the `ARTICOLO` table using `id_articolo` (never trusting client-submitted category strings).
   - Conditional validation:
     - **Meat categories (`Bovino`, `Suino`, `Avicolo`)**: `paese_nascita`, `paese_allevamento`, `paese_macellazione`, `paese_sezionamento` are strictly mandatory; at least one of `data_macellazione` or `data_scadenza` must be provided.
     - **Non-meat categories**: origin country fields and `data_macellazione` are optional; `data_scadenza` is mandatory.
   - String and date sanitization ensuring empty form values map to Python `None` (SQL `NULL`), preventing PostgreSQL date parsing errors and empty string pollution.
   - Updated `INSERT INTO LOTTO_MADRE` query including `data_macellazione`.
3. **Database schema (`database.sql`) & Migration**:
   - `LOTTO_MADRE` table requires `data_macellazione DATE NULL`.
   - `data_scadenza` in `database.sql` should be nullable (`DATE` instead of `DATE NOT NULL`) to support meat batches where only `data_macellazione` is recorded upon delivery.
   - Exact migration SQL:
     ```sql
     ALTER TABLE LOTTO_MADRE ADD COLUMN IF NOT EXISTS data_macellazione DATE;
     ALTER TABLE LOTTO_MADRE ALTER COLUMN data_scadenza DROP NOT NULL;
     ```

---

## 2. Route `/carico` (GET) Analysis

### Current Implementation (`app.py:194-213`)
```python
@app.route('/carico')
def carico():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM ARTICOLO WHERE tipo_categoria IN ('TAGLIO', 'VARIO') ORDER BY categoria, denominazione;")
            articoli = cursor.fetchall()
            
            # Raggruppa per categoria per optgroup
            articoli_per_categoria = {}
            for art in articoli:
                cat = art['categoria']
                if cat not in articoli_per_categoria:
                    articoli_per_categoria[cat] = []
                articoli_per_categoria[cat].append(art)
                
        return render_template('carico.html', articoli_per_categoria=articoli_per_categoria)
    finally:
        db_pool.putconn(conn)
```

### Assessment
- **Query**: Selects all columns (`id_articolo`, `denominazione`, `categoria`, `allergeni`, `tipo_categoria`) for raw cuts (`TAGLIO`) and miscellaneous ingredients (`VARIO`).
- **Grouping**: Produces a dictionary where keys are category names (e.g. `Bovino`, `Suino`, `Avicolo`, `Spezie`, `Latticini`, `Farinacei`, `Uova`, `Involucri`), and values are lists of dict records.
- **Template Contract**: In `templates/carico.html`, iterating over `articoli_per_categoria.items()` provides direct access to each article's `art.categoria` and `art.id_articolo`.
- **Verdict**: The GET route is complete, robust, and provides all necessary data for client-side category classification.

---

## 3. Route `/salva_carico` (POST) Analysis

### Current Implementation (`app.py:214-262`)
```python
@app.route('/salva_carico', methods=['POST'])
def salva_carico():
    id_articolo = request.form.get('id_articolo')
    codice_lotto_fornitore = request.form.get('codice_lotto_fornitore')
    fornitore = request.form.get('fornitore')
    data_scadenza = request.form.get('data_scadenza')
    paese_nascita = request.form.get('paese_nascita')
    paese_allevamento = request.form.get('paese_allevamento')
    paese_macellazione = request.form.get('paese_macellazione')
    paese_sezionamento = request.form.get('paese_sezionamento')
...
```

### Issues with Current Implementation
1. Does not parse `data_macellazione`.
2. Hard-codes `data_scadenza` as mandatory for all items, preventing meat loads with only slaughter date from being saved.
3. Does not fetch or verify the article's `categoria` from the DB.
4. Does not enforce conditional validation for meat categories (`Bovino`, `Suino`, `Avicolo`).
5. Passes empty strings `""` for country fields when not filled, storing empty strings instead of `NULL` in the database.
6. The `INSERT INTO LOTTO_MADRE` does not include `data_macellazione`.

### Target Architecture for `/salva_carico`

#### 1. Input Extraction & String Sanitization
Form fields should be stripped of leading/trailing whitespace. Empty strings must be converted to `None` so psycopg2 binds them as SQL `NULL`:
```python
def clean_str(val):
    if val is None:
        return None
    val_clean = val.strip()
    return val_clean if val_clean != '' else None

id_articolo = request.form.get('id_articolo')
codice_lotto_fornitore = clean_str(request.form.get('codice_lotto_fornitore'))
fornitore = clean_str(request.form.get('fornitore'))
data_scadenza_str = clean_str(request.form.get('data_scadenza'))
data_macellazione_str = clean_str(request.form.get('data_macellazione'))
paese_nascita = clean_str(request.form.get('paese_nascita'))
paese_allevamento = clean_str(request.form.get('paese_allevamento'))
paese_macellazione = clean_str(request.form.get('paese_macellazione'))
paese_sezionamento = clean_str(request.form.get('paese_sezionamento'))
```

#### 2. Base Universal Validation
All loads require valid article selection, supplier lot code, and supplier name:
```python
if not id_articolo or not codice_lotto_fornitore or not fornitore:
    flash('I campi obbligatori (Prodotto, Lotto Fornitore, Fornitore) non sono stati compilati.', 'error')
    return redirect(url_for('carico'))
```

#### 3. Database Category Retrieval
Retrieve the authoritative `categoria` and `denominazione` from the database:
```python
cursor.execute("SELECT categoria, denominazione FROM ARTICOLO WHERE id_articolo = %s", (id_articolo,))
articolo = cursor.fetchone()
if not articolo:
    flash('Articolo selezionato non valido o non presente nel database.', 'error')
    return redirect(url_for('carico'))

categoria = articolo['categoria']
CATEGORIE_CARNE = {'Bovino', 'Suino', 'Avicolo'}
is_carne = categoria in CATEGORIE_CARNE
```

#### 4. Date Parsing & Semantic Validation
- **`data_macellazione`**:
  ```python
  data_macellazione_parsed = None
  if data_macellazione_str:
      try:
          data_macellazione_parsed = datetime.datetime.strptime(data_macellazione_str, '%Y-%m-%d').date()
      except ValueError:
          flash('Formato data di macellazione non valido.', 'error')
          return redirect(url_for('carico'))
      if data_macellazione_parsed > datetime.date.today():
          flash('La data di macellazione non può essere nel futuro.', 'error')
          return redirect(url_for('carico'))
  ```
- **`data_scadenza`**:
  ```python
  data_scad_parsed = None
  if data_scadenza_str:
      try:
          data_scad_parsed = datetime.datetime.strptime(data_scadenza_str, '%Y-%m-%d').date()
      except ValueError:
          flash('Formato data di scadenza non valido.', 'error')
          return redirect(url_for('carico'))
      if data_scad_parsed < datetime.date.today():
          flash('La data di scadenza non può essere nel passato.', 'error')
          return redirect(url_for('carico'))
  ```

#### 5. Conditional Category Validation
- **Meat (`is_carne == True`)**:
  1. Origin fields (`paese_nascita`, `paese_allevamento`, `paese_macellazione`, `paese_sezionamento`) must ALL be non-null and non-empty.
     ```python
     if not all([paese_nascita, paese_allevamento, paese_macellazione, paese_sezionamento]):
         flash('Per le carni (Bovino, Suino, Avicolo) tutti i campi di origine (Nascita, Allevamento, Macellazione, Sezionamento) sono obbligatori.', 'error')
         return redirect(url_for('carico'))
     ```
  2. At least one date (`data_macellazione` or `data_scadenza`) must be provided:
     ```python
     if not data_macellazione_parsed and not data_scad_parsed:
         flash('Per le carni è obbligatorio inserire almeno una data tra Data di Macellazione e Data di Scadenza.', 'error')
         return redirect(url_for('carico'))
     ```
- **Non-Meat (`is_carne == False`)**:
  1. `data_scadenza` is mandatory:
     ```python
     if not data_scad_parsed:
         flash('La data di scadenza è obbligatoria per questo prodotto.', 'error')
         return redirect(url_for('carico'))
     ```
  2. Origin country fields and `data_macellazione` remain optional (defaulting to `None`/`NULL`).

#### 6. Exact `INSERT INTO LOTTO_MADRE` Query
```python
cursor.execute("""
    INSERT INTO LOTTO_MADRE (
        id_articolo, codice_lotto_fornitore, fornitore, 
        data_scadenza, data_macellazione,
        paese_nascita, paese_allevamento, paese_macellazione, paese_sezionamento
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
""", (
    id_articolo, codice_lotto_fornitore, fornitore,
    data_scad_parsed, data_macellazione_parsed,
    paese_nascita, paese_allevamento, paese_macellazione, paese_sezionamento
))
```

---

## 4. Complete Reference Implementation for `salva_carico`

```python
@app.route('/salva_carico', methods=['POST'])
def salva_carico():
    def clean_str(val):
        if val is None:
            return None
        val_clean = val.strip()
        return val_clean if val_clean != '' else None

    id_articolo = request.form.get('id_articolo')
    codice_lotto_fornitore = clean_str(request.form.get('codice_lotto_fornitore'))
    fornitore = clean_str(request.form.get('fornitore'))
    data_scadenza_str = clean_str(request.form.get('data_scadenza'))
    data_macellazione_str = clean_str(request.form.get('data_macellazione'))
    paese_nascita = clean_str(request.form.get('paese_nascita'))
    paese_allevamento = clean_str(request.form.get('paese_allevamento'))
    paese_macellazione = clean_str(request.form.get('paese_macellazione'))
    paese_sezionamento = clean_str(request.form.get('paese_sezionamento'))

    # 1. Validazione campi base comuni
    if not id_articolo or not codice_lotto_fornitore or not fornitore:
        flash('I campi obbligatori (Prodotto, Lotto Fornitore, Fornitore) non sono stati compilati.', 'error')
        return redirect(url_for('carico'))

    # 2. Parsing e validazione data macellazione (se presente)
    data_macellazione_parsed = None
    if data_macellazione_str:
        try:
            data_macellazione_parsed = datetime.datetime.strptime(data_macellazione_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Formato data di macellazione non valido.', 'error')
            return redirect(url_for('carico'))
        if data_macellazione_parsed > datetime.date.today():
            flash('La data di macellazione non può essere nel futuro.', 'error')
            return redirect(url_for('carico'))

    # 3. Parsing e validazione data scadenza (se presente)
    data_scad_parsed = None
    if data_scadenza_str:
        try:
            data_scad_parsed = datetime.datetime.strptime(data_scadenza_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Formato data di scadenza non valido.', 'error')
            return redirect(url_for('carico'))
        if data_scad_parsed < datetime.date.today():
            flash('La data di scadenza non può essere nel passato.', 'error')
            return redirect(url_for('carico'))

    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 4. Recupero categoria articolo dal database
            cursor.execute("SELECT categoria, denominazione FROM ARTICOLO WHERE id_articolo = %s", (id_articolo,))
            articolo = cursor.fetchone()
            if not articolo:
                flash('Articolo selezionato non valido.', 'error')
                return redirect(url_for('carico'))

            categoria = articolo['categoria']
            is_carne = categoria in ('Bovino', 'Suino', 'Avicolo')

            # 5. Validazione condizionale per carni vs altre categorie
            if is_carne:
                if not all([paese_nascita, paese_allevamento, paese_macellazione, paese_sezionamento]):
                    flash('Per le carni (Bovino, Suino, Avicolo) tutti i campi di origine (Nascita, Allevamento, Macellazione, Sezionamento) sono obbligatori.', 'error')
                    return redirect(url_for('carico'))

                if not data_macellazione_parsed and not data_scad_parsed:
                    flash('Per le carni è obbligatorio inserire almeno una data tra Data di Macellazione e Data di Scadenza.', 'error')
                    return redirect(url_for('carico'))
            else:
                if not data_scad_parsed:
                    flash('La data di scadenza è obbligatoria per questo prodotto.', 'error')
                    return redirect(url_for('carico'))

            # 6. Inserimento in LOTTO_MADRE
            cursor.execute("""
                INSERT INTO LOTTO_MADRE (
                    id_articolo, codice_lotto_fornitore, fornitore, 
                    data_scadenza, data_macellazione,
                    paese_nascita, paese_allevamento, paese_macellazione, paese_sezionamento
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                id_articolo, codice_lotto_fornitore, fornitore, 
                data_scad_parsed, data_macellazione_parsed,
                paese_nascita, paese_allevamento, paese_macellazione, paese_sezionamento
            ))

        conn.commit()
        flash('Carico merce registrato con successo.', 'success')
        return redirect(url_for('magazzino'))
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Errore salva_carico (id_articolo={id_articolo}): {e}", exc_info=True)
        flash('Errore durante il salvataggio. Controllare i dati inseriti.', 'error')
        return redirect(url_for('carico'))
    finally:
        db_pool.putconn(conn)
```

---

## 5. Database Schema & Migration Specification

### Current `database.sql` Definition
```sql
-- 2. Tabella LOTTO_MADRE (Materie prime e carichi da fornitore)
CREATE TABLE LOTTO_MADRE (
    id_lotto_madre SERIAL PRIMARY KEY,
    id_articolo INT NOT NULL REFERENCES ARTICOLO(id_articolo),
    codice_lotto_fornitore VARCHAR(100) NOT NULL,
    fornitore VARCHAR(255) NOT NULL,
    data_carico TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_scadenza DATE NOT NULL,
    paese_nascita VARCHAR(100),       -- o VARCHAR(3) se usi solo sigle ISO come ITA
    paese_allevamento VARCHAR(100),     -- o VARCHAR(3) se usi solo sigle ISO come ITA
    paese_macellazione VARCHAR(100),
    paese_sezionamento VARCHAR(100),
    flg_lotto_del_giorno BOOLEAN DEFAULT FALSE
);
```

### Proposed `database.sql` Schema Update
In `database.sql`:
1. Add `data_macellazione DATE` column.
2. Change `data_scadenza DATE NOT NULL` to `data_scadenza DATE` (nullable), since meat products may have only slaughter date.
```sql
-- 2. Tabella LOTTO_MADRE (Materie prime e carichi da fornitore)
CREATE TABLE LOTTO_MADRE (
    id_lotto_madre SERIAL PRIMARY KEY,
    id_articolo INT NOT NULL REFERENCES ARTICOLO(id_articolo),
    codice_lotto_fornitore VARCHAR(100) NOT NULL,
    fornitore VARCHAR(255) NOT NULL,
    data_carico TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_scadenza DATE,
    data_macellazione DATE,
    paese_nascita VARCHAR(100),       -- o VARCHAR(3) se usi solo sigle ISO come ITA
    paese_allevamento VARCHAR(100),     -- o VARCHAR(3) se usi solo sigle ISO come ITA
    paese_macellazione VARCHAR(100),
    paese_sezionamento VARCHAR(100),
    flg_lotto_del_giorno BOOLEAN DEFAULT FALSE
);
```

### PostgreSQL Migration Script (`migration.sql`)
To execute against existing databases:
```sql
-- 1. Aggiunge la nuova colonna data_macellazione se non già presente
ALTER TABLE LOTTO_MADRE ADD COLUMN IF NOT EXISTS data_macellazione DATE;

-- 2. Rende data_scadenza nullable per permettere carichi carni con solo data di macellazione
ALTER TABLE LOTTO_MADRE ALTER COLUMN data_scadenza DROP NOT NULL;
```

---

## 6. Downstream Impact Analysis & Recommendations

| Location in `app.py` | Current State | Impact / Recommendation |
|---|---|---|
| `app.py:80-87` (`aggiorna_file_excel`) | `SELECT ... data_scadenza, paese_nascita... FROM LOTTO_MADRE` | Add `data_macellazione` to `query_carichi` column list for complete HACCP Excel reporting. |
| `app.py:329` (`produci_preparato`) | `WHERE id_articolo = %s AND data_scadenza >= CURRENT_DATE` | If a meat raw material has only `data_macellazione` (where `data_scadenza IS NULL`), change to `WHERE id_articolo = %s AND (data_scadenza IS NULL OR data_scadenza >= CURRENT_DATE)`. |
| `app.py:408-416` (`stampa_etichetta_taglio`) | `SELECT ... data_scadenza, paese_nascita...` | Select `data_macellazione` as well. In `etichetta_taglio.html`, handle display when `data_scadenza` is None (`taglio.data_scadenza.strftime(...) if taglio.data_scadenza else 'N/D'`). |
| `templates/magazzino.html:38` | `{{ lotto.data_scadenza.strftime('%d/%m/%Y') if lotto.data_scadenza else '-' }}` | Already handles `NULL` `data_scadenza` safely without throwing exceptions. |
