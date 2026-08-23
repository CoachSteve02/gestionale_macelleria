# Handoff Report — Backend & Database Investigation (Dynamic Carico Merci)

## 1. Observation

### 1.1 GET Route `/carico` (`app.py:194-213`)
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
- Line 199: Queries all articles where `tipo_categoria IN ('TAGLIO', 'VARIO')`.
- Line 203-208: Groups them by `cat = art['categoria']` into `articoli_per_categoria`.
- Line 210: Passes `articoli_per_categoria` to `carico.html`.
- Each article item dict contains: `id_articolo`, `denominazione`, `categoria`, `allergeni`, `tipo_categoria`.

### 1.2 POST Route `/salva_carico` (`app.py:214-262`)
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

    if not all([id_articolo, codice_lotto_fornitore, fornitore, data_scadenza]):
        flash('I campi obbligatori (Prodotto, Lotto, Fornitore, Scadenza) non sono stati compilati.', 'error')
        return redirect(url_for('carico'))

    # Validazione formato e data di scadenza
    try:
        data_scad_parsed = datetime.datetime.strptime(data_scadenza, '%Y-%m-%d').date()
    except ValueError:
        flash('Formato data di scadenza non valido.', 'error')
        return redirect(url_for('carico'))

    if data_scad_parsed < datetime.date.today():
        flash('La data di scadenza non può essere nel passato.', 'error')
        return redirect(url_for('carico'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO LOTTO_MADRE (
                    id_articolo, codice_lotto_fornitore, fornitore, data_scadenza, 
                    paese_nascita, paese_allevamento, paese_macellazione, paese_sezionamento
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                id_articolo, codice_lotto_fornitore, fornitore, data_scad_parsed, 
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
- Line 216-223: Extracts only 8 form fields; does not extract `data_macellazione`.
- Line 225: Enforces `data_scadenza` unconditionally for all categories.
- Line 243-251: INSERT statement omits `data_macellazione`.
- No DB query is executed to determine `categoria` of `id_articolo`.

### 1.3 `database.sql` Schema (`database.sql:10-23`)
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
- Line 17: `data_scadenza DATE NOT NULL` constraint exists in `database.sql`.
- `data_macellazione` column is missing from `LOTTO_MADRE`.

---

## 2. Logic Chain

1. **GET Route Capability**: Observation 1.1 shows that `/carico` GET already queries and passes `art.categoria` and `art.id_articolo` to Jinja2 in `articoli_per_categoria`. Therefore, the backend GET route requires no changes, and the frontend can immediately use `data-categoria="{{ art.categoria }}"` on each `<option>`.
2. **Authoritative Category Verification**: In Observation 1.2, `salva_carico` currently has no knowledge of `categoria`. Because client-submitted data cannot be trusted for HACCP compliance, `salva_carico` must execute `SELECT categoria FROM ARTICOLO WHERE id_articolo = %s` inside the database transaction.
3. **Conditional Validation Matrix**:
   - For Meat (`categoria IN ('Bovino', 'Suino', 'Avicolo')`):
     - `paese_nascita`, `paese_allevamento`, `paese_macellazione`, `paese_sezionamento` are strictly mandatory (`not all(...)` triggers flash error and redirect).
     - At least one date between `data_macellazione` and `data_scadenza` must be present.
   - For Non-Meat:
     - Origin country fields and `data_macellazione` are optional.
     - `data_scadenza` is mandatory.
4. **Database Constraint & Schema Alignment**:
   - Observation 1.3 shows `data_scadenza DATE NOT NULL` in `database.sql`.
   - If a meat batch is entered with only `data_macellazione` and no `data_scadenza`, saving `data_scadenza = NULL` violates `NOT NULL`.
   - Therefore, the migration must both add `data_macellazione DATE NULL` and drop `NOT NULL` on `data_scadenza`:
     ```sql
     ALTER TABLE LOTTO_MADRE ADD COLUMN IF NOT EXISTS data_macellazione DATE;
     ALTER TABLE LOTTO_MADRE ALTER COLUMN data_scadenza DROP NOT NULL;
     ```
   - In `database.sql`, `LOTTO_MADRE` definition must include `data_macellazione DATE` and `data_scadenza DATE` (without `NOT NULL`).
5. **psycopg2 Binding Safety (NULL vs Empty String)**:
   - When text/date inputs are submitted blank in HTML forms, `request.form.get()` returns `""` (empty string).
   - Passing `""` to PostgreSQL `DATE` columns triggers `invalid input syntax for type date: ""`.
   - Sanitizing strings with `.strip() or None` ensures clean SQL `NULL` injection via psycopg2 `%s`.

---

## 3. Caveats

1. **Downstream queries selecting `LOTTO_MADRE`**:
   - In `app.py:80-87` (`aggiorna_file_excel`), `query_carichi` lists explicit column names. Adding `data_macellazione` to this query will ensure the Excel export contains the slaughter date.
   - In `app.py:329` (`produci_preparato`), the clause `data_scadenza >= CURRENT_DATE` should ideally be `(data_scadenza IS NULL OR data_scadenza >= CURRENT_DATE)` to avoid excluding fresh meat lots that were loaded with only `data_macellazione`.
2. **Date comparison logic**:
   - `data_macellazione` cannot be in the future (`<= today`).
   - `data_scadenza` cannot be in the past (`>= today`).
   - If both are provided, `data_scadenza >= data_macellazione`.

---

## 4. Conclusion

- **GET `/carico`**: Fully compliant as is.
- **POST `/salva_carico`**: Update form parsing, query `categoria` from `ARTICOLO`, implement conditional validation branches for meat vs non-meat, sanitize empty strings to `None`, and update `INSERT INTO LOTTO_MADRE` with 9 parameters including `data_macellazione`.
- **`database.sql`**: Update `CREATE TABLE LOTTO_MADRE` to add `data_macellazione DATE` and make `data_scadenza DATE` nullable.
- **DB Migration SQL**:
  ```sql
  ALTER TABLE LOTTO_MADRE ADD COLUMN IF NOT EXISTS data_macellazione DATE;
  ALTER TABLE LOTTO_MADRE ALTER COLUMN data_scadenza DROP NOT NULL;
  ```

---

## 5. Verification Method

1. **Inspect Code and Schema**:
   - Verify `database.sql` lines 10-24 contains `data_macellazione DATE` and nullable `data_scadenza`.
   - Verify `app.py` `/salva_carico` contains `SELECT categoria FROM ARTICOLO` and the 9-column `INSERT INTO LOTTO_MADRE`.
2. **Execute Database Migration**:
   - Run `ALTER TABLE LOTTO_MADRE ADD COLUMN IF NOT EXISTS data_macellazione DATE;` and `ALTER TABLE LOTTO_MADRE ALTER COLUMN data_scadenza DROP NOT NULL;` in PostgreSQL.
3. **Manual Functional Tests**:
   - **Test 1 (Meat with all fields)**: Select "Carne Macinata Bovino", fill lot, supplier, data_macellazione, origin countries. Submit -> Success flash, record in `LOTTO_MADRE`.
   - **Test 2 (Meat missing origin)**: Select "Capocollo di Maiale", fill lot, supplier, data_scadenza, leave "Nato in" blank. Submit -> Error flash, redirect to `/carico`, no DB insertion.
   - **Test 3 (Non-meat simplified)**: Select "Sale Marino Fine", fill lot, supplier, data_scadenza, leave origin countries and data_macellazione blank. Submit -> Success flash, record inserted with `NULL` origin/slaughter fields.
