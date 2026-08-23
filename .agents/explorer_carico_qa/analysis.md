# Piano di Analisi QA & Strategia di Verifica: Form Dinamico Carico Merci e Validazione HACCP

## 1. Ispezione dell'Ambiente e Configurazione

### 1.1 Stack Tecnologico e Dipendenze (`requirements.txt`)
Dall'ispezione di `requirements.txt`:
- **Flask** `3.0.0`: Web framework WSGI. Fornisce il client di test integrato `app.test_client()` con supporto completo a sessioni, flash message e context manager.
- **psycopg2-binary** `2.9.9`: Driver PostgreSQL con connection pooling (`SimpleConnectionPool`).
- **pandas** `2.2.0` & **openpyxl** `3.1.2`: Utilizzati in `app.py` per l'estrazione e generazione del report Excel mensile HACCP in `/download_excel`.
- **python-dotenv** `1.0.0`: Carica automaticamente le variabili d'ambiente da `.env`.

### 1.2 Configurazione Database e Connessioni
- **Variabili d'ambiente**:
  - `DATABASE_URL`: `postgresql://postgres:postgres@localhost:5432/gestionale_macelleria_dev` (fallback di default in `app.py:36`).
  - `SECRET_KEY`: Chiave per la firma dei cookie di sessione Flask e gestione dei messaggi `flash()`.
- **Connection Pool**: `SimpleConnectionPool(minconn=1, maxconn=10)` configurato globalmente in `app.py`. Ogni endpoint gestisce le connessioni con pattern `try ... finally: db_pool.putconn(conn)`.
- **Integrità Transazionale**: Le operazioni di scrittura (`salva_carico`, `produci_preparato`, `chiudi_sessione`) usano `conn.commit()` esplicito e `conn.rollback()` nel blocco `except`.

### 1.3 Modalità di Esecuzione e Test dell'App Flask
L'applicazione può essere testata in tre modalità complementari:
1. **Flask Test Client (`app.test_client()`)**:
   Permette l'esecuzione di test programmatici veloci e deterministici senza avviare il server HTTP, testando le route GET e POST, i redirect HTTP 302, i messaggi flash in sessione e i template Jinja2 renderizzati.
2. **Server Locale (`python app.py`)**:
   Avvia l'app su `http://localhost:5000` (host `0.0.0.0`, porta 5000, `debug=True`, `use_reloader=False`). Ideale per verifiche interattive manuali nel browser e ispezione visiva del DOM.
3. **Script SQL Diretto su PostgreSQL**:
   Per la verifica dello schema, l'applicazione della migrazione `ALTER TABLE` e l'ispezione dei vincoli di tabella.

---

## 2. Analisi dei Requisiti e Comportamento Atteso

### 2.1 Requisiti Frontend (R1, R4)
1. **`data-categoria` su `<option>`**:
   Nel `<select id="id_articolo">` generato in `templates/carico.html`, ogni `<option>` deve esporre l'attributo `data-categoria="{{ categoria }}"` (o `art.categoria`).
2. **Sezione Dinamica HACCP (`#sezione-tracciabilita`)**:
   - Racchiusa in un container con intestazione visiva distinta (es. bordo colorato rosso/ambra, badge "DATI HACCP OBBLIGATORI", icona).
   - Contiene i 4 campi paese (`paese_nascita`, `paese_allevamento`, `paese_macellazione`, `paese_sezionamento`) e il nuovo campo `data_macellazione`.
   - **Stato iniziale (nessun prodotto selezionato)**: Nascosta (`hidden` / `display: none`). Campi non required.
   - **Selezione Carni (`Bovino`, `Suino`, `Avicolo`)**: Visibile (`hidden` rimossa). Campi paese impostati con `required = true`.
   - **Selezione Non-Carni (`Spezie`, `Latticini`, `Farinacei`, `Uova`, `Involucri`, `Pronto Cuoci`, ecc.)**: Nascosta. Campi paese impostati con `required = false` e valori svuotati per evitare invio di dati incoerenti.
3. **UX & Vanilla JS**:
   - Esecuzione immediata al cambio (`change` event) senza chiamate AJAX né reload.
   - Gestione corretta dell'evento `DOMContentLoaded` per gestire il ripristino dello stato del form da cache del browser (bfcache/page refresh).

### 2.2 Requisiti Backend (`/salva_carico`, R3)
1. **Recupero Categoria da DB**:
   - Ricevuto `id_articolo`, eseguire una query su `ARTICOLO` per ricavare la `categoria` reale da DB (non fidarsi unicamente del client).
   - Se `id_articolo` non esiste in `ARTICOLO` -> flash error `'Articolo selezionato non valido.'`, redirect a `/carico`.
2. **Validazione Condizionale**:
   - Se `categoria` appartiene a `('Bovino', 'Suino', 'Avicolo')`:
     * `paese_nascita`, `paese_allevamento`, `paese_macellazione`, `paese_sezionamento` sono **obbligatori** (non vuoti).
     * Almeno uno tra `data_macellazione` e `data_scadenza` deve essere presente. Se entrambi mancano -> flash error.
     * Se `data_macellazione` è presente: validare formato `%Y-%m-%d`.
     * Se `data_scadenza` è presente: validare formato `%Y-%m-%d` e verificare che non sia nel passato.
   - Se `categoria` **NON è carne**:
     * I campi paese e `data_macellazione` sono facoltativi.
     * I campi non compilati (stringhe vuote) devono essere salvati come `NULL` nel database.
3. **Aggiornamento INSERT INTO `LOTTO_MADRE`**:
   - Includere `data_macellazione` nella query di inserimento.
   - Valori vuoti convertiti esplicitamente in `None` (salvati come `NULL` in SQL).

### 2.3 Requisiti Database (R2)
1. **Migrazione**:
   ```sql
   ALTER TABLE LOTTO_MADRE ADD COLUMN IF NOT EXISTS data_macellazione DATE;
   ```
2. **Allineamento `database.sql`**:
   La definizione della tabella `LOTTO_MADRE` deve includere `data_macellazione DATE`.

---

## 3. Matrice Completa dei Casi di Test (Test Matrix)

| ID Test | Ambito | Scenario / Payload | Comportamento Atteso | Tipo Verifica |
| :--- | :--- | :--- | :--- | :--- |
| **TC-FE-01** | Frontend | Caricamento iniziale GET `/carico` | Select su `-- Seleziona un prodotto --`; `#sezione-tracciabilita` ha classe `hidden`; campi paese NON hanno attributo `required`; ogni `<option>` ha `data-categoria`. | DOM / Ispezione HTML |
| **TC-FE-02** | Frontend | Selezione articolo categoria "Bovino" (es. Carne Macinata) | `#sezione-tracciabilita` diventa visibile; riceve badge "DATI HACCP"; campi paese ricevono `required = true`. Nessun reload di pagina. | Interazione UI / JS |
| **TC-FE-03** | Frontend | Selezione articolo "Suino" o "Avicolo" | `#sezione-tracciabilita` visibile; campi tracciabilità attivi e required. | Interazione UI / JS |
| **TC-FE-04** | Frontend | Selezione articolo non-carne (es. "Sale Marino Fine" - Spezie) | `#sezione-tracciabilita` si nasconde (`hidden`); attributi `required` rimossi dai campi paese; campi paese e data macellazione resettati/svuotati. | Interazione UI / JS |
| **TC-FE-05** | Frontend | Submit form non-carne con campi base compilati | Il browser NON blocca l'invio (nessun errore "invalid form control not focusable"); invio del form POST a `/salva_carico`. | Validazione HTML5 Form |
| **TC-BE-01** | Backend | POST `/salva_carico` con campi base mancanti (`id_articolo` o `codice_lotto_fornitore` o `fornitore` mancanti) | Flash error: `"I campi obbligatori ... non sono stati compilati."`; HTTP 302 redirect a `/carico`; nessun inserimento in DB. | Test Client / HTTP |
| **TC-BE-02** | Backend | POST `/salva_carico` con `id_articolo` inesistente (es. 99999) | Flash error: `"Articolo selezionato non valido."`; HTTP 302 redirect a `/carico`; rollback transazione. | Test Client / HTTP |
| **TC-BE-03** | Backend | POST `/salva_carico` Carne (Bovino) SENZA campi paese (stringhe vuote) | Flash error: `"Per gli articoli di carne (Bovino, Suino, Avicolo) i campi di tracciabilità ... sono obbligatori."`; redirect `/carico`; nessun record creato. | Test Client / HTTP |
| **TC-BE-04** | Backend | POST `/salva_carico` Carne (Bovino) con campi paese MA SENZA `data_macellazione` E SENZA `data_scadenza` | Flash error: `"Per le carni è obbligatorio specificare almeno una tra Data di Macellazione e Data di Scadenza."`; redirect `/carico`; nessun record creato. | Test Client / HTTP |
| **TC-BE-05** | Backend | POST `/salva_carico` Carne con campi paese validi + SOLO `data_macellazione` (senza `data_scadenza` o con `data_scadenza` valida) | Flash success: `"Carico merce registrato con successo."`; redirect a `/magazzino`; record presente in `LOTTO_MADRE` con `data_macellazione` valorizzata. | Test Client + DB Query |
| **TC-BE-06** | Backend | POST `/salva_carico` Carne con campi paese validi + SOLO `data_scadenza` | Flash success; redirect `/magazzino`; record inserito con `data_macellazione = NULL` e `data_scadenza` valorizzata. | Test Client + DB Query |
| **TC-BE-07** | Backend | POST `/salva_carico` Carne con TUTTI i campi compilati (`paese_*`, `data_macellazione`, `data_scadenza`) | Flash success; redirect `/magazzino`; record inserito con tutti i campi corretti. | Test Client + DB Query |
| **TC-BE-08** | Backend | POST `/salva_carico` con data di scadenza passata o formato data non valido | Flash error: `"La data di scadenza non può essere nel passato."` o `"Formato data ... non valido."`; redirect `/carico`. | Test Client / HTTP |
| **TC-BE-09** | Backend | POST `/salva_carico` Non-Carne (es. Spezie/Latticini) con campi paese e data macellazione vuoti | Flash success; redirect `/magazzino`; record inserito in `LOTTO_MADRE` con campi `paese_*` salvati come `NULL` e `data_macellazione` come `NULL`. | Test Client + DB Query |
| **TC-BE-10** | Backend | POST `/salva_carico` Non-Carne con campi paese facoltativamente compilati | Flash success; redirect `/magazzino`; record inserito con i valori forniti. | Test Client + DB Query |
| **TC-DB-01** | Database | Verifica colonna `data_macellazione` in tabella `LOTTO_MADRE` | Colonna `data_macellazione` di tipo `DATE`, nullable (`is_nullable = 'YES'`). | SQL Query |
| **TC-DB-02** | Database | Esecuzione ripetuta della migrazione (Idempotenza) | `ALTER TABLE LOTTO_MADRE ADD COLUMN IF NOT EXISTS data_macellazione DATE;` esegue senza errori ripetutamente. | SQL Execution |
| **TC-REG-01** | Non-Regr | GET `/` (Home / Vetrina) | HTTP 200 OK; catalogo renderizzato correttamente con TAGLI, PREPARATI e VARI. | Test Client / HTTP |
| **TC-REG-02** | Non-Regr | GET `/magazzino` | HTTP 200 OK; tabella lotti madre renderizzata con data carico, scadenza e pulsante stampa etichetta per i tagli. | Test Client / HTTP |
| **TC-REG-03** | Non-Regr | GET `/stampa_etichetta_taglio/<id_lotto_madre>` su lotto Bovino con tracciabilità completa | HTTP 200 OK; template etichetta generato con dati origine, date e codice a barre. | Test Client / HTTP |
| **TC-REG-04** | Non-Regr | POST `/produci_preparato/<id_articolo>` | HTTP 302 redirect a `/stampa_etichetta/<id_lotto_preparato>`; creazione sessione e associazione lotti madre senza errori. | Test Client / HTTP |
| **TC-REG-05** | Non-Regr | GET `/download_excel` | HTTP 200 OK; file Excel generato e scaricato (`Registro_Tracciabilita_*.xlsx`) senza eccezioni su `LOTTO_MADRE`. | Test Client / HTTP |
| **TC-REG-06** | Non-Regr | GET `/api/db_status` | HTTP 200 OK; payload JSON `{"status": "ok"}`. | Test Client / JSON |

---

## 4. Analisi dei Rischi di Regressione e Casi Limite (Edge Cases)

### 4.1 Rischio 1: Errore HTML5 "An invalid form control is not focusable"
- **Meccanismo**: Se un input ha l'attributo `required` ma il suo container genitore ha `display: none` (classe CSS `hidden`), al click del pulsante submit i browser moderni (Chrome, Firefox, Safari, Edge) bloccano l'invio visualizzando un errore in console: `An invalid form control with name='paese_nascita' is not focusable`. L'utente non riceve feedback e il form sembra "bloccato".
- **Prevenzione Verificata**: Il codice JavaScript deve impostare programmaticamente `input.required = isMeat` ogni volta che cambia la categoria selezionata, rimuovendo il vincolo `required` quando la sezione è nascosta.

### 4.2 Rischio 2: Gestione `NULL` vs Stringa Vuota `""` nel Database PostgreSQL
- **Meccanismo**: Nei form HTML, i campi vuoti vengono inviati come stringa vuota `""`. Se inseriti in colonne di tipo `DATE` (come `data_macellazione` o `data_scadenza`), PostgreSQL genera l'errore: `invalid input syntax for type date: ""`. Se inseriti in colonne `VARCHAR`, salvano la stringa vuota anziché `NULL`.
- **Prevenzione Verificata**: In `app.py`, ogni campo opzionale deve essere sanitizzato:
  ```python
  def parse_optional_str(val):
      if val and val.strip():
          return val.strip()
      return None

  def parse_optional_date(val):
      if val and val.strip():
          try:
              return datetime.datetime.strptime(val.strip(), '%Y-%m-%d').date()
          except ValueError:
              return 'INVALID_DATE'
      return None
  ```

### 4.3 Rischio 3: `data_scadenza` Nullable e Template `etichetta_taglio.html`
- **Meccanismo**: In `templates/etichetta_taglio.html` (riga 150), il template esegue:
  ```jinja2
  {{ taglio.data_scadenza.strftime('%d/%m/%Y') }}
  ```
  Se un lotto viene registrato con sola `data_macellazione` e `data_scadenza` è `None`, la chiamata `.strftime()` solleverà un `AttributeError: 'NoneType' object has no attribute 'strftime'` causando un HTTP 500 durante la stampa dell'etichetta.
- **Prevenzione Verificata**:
  1. Nel template `etichetta_taglio.html:150`, usare un controllo difensivo:
     ```jinja2
     {{ taglio.data_scadenza.strftime('%d/%m/%Y') if taglio.data_scadenza else '-' }}
     ```
  2. Nel template `magazzino.html:38`, il controllo difensivo è già presente (`{{ lotto.data_scadenza.strftime('%d/%m/%Y') if lotto.data_scadenza else '-' }}`).

### 4.4 Rischio 4: Normalizzazione del Controllo Categoria (Case-Insensitivity & Whitespace)
- **Meccanismo**: Se una categoria nel DB contiene spazi o variazioni di casing (es. `"Bovino "`, `"bovino"`, `"BOVINO"`), un check rigido `categoria in ('Bovino', 'Suino', 'Avicolo')` potrebbe fallire.
- **Prevenzione Verificata**:
  - Nel backend:
    ```python
    CATEGORIE_CARNE = {'bovino', 'suino', 'avicolo'}
    is_carne = (categoria.strip().lower() in CATEGORIE_CARNE) if categoria else False
    ```
  - Nel frontend JavaScript:
    ```javascript
    const CATEGORIE_CARNE = ['bovino', 'suino', 'avicolo'];
    const isCarne = CATEGORIE_CARNE.includes((categoria || '').trim().toLowerCase());
    ```

---

## 5. Script di Test Automatico Consigliato (`test_carico_verification.py`)

Per permettere una verifica automatica, autonoma e ripetibile di tutte le route e della logica di validazione senza richiedere un framework di test esterno pesante, ecco lo script completo consigliato basato sul client di test di Flask.

```python
"""
Script di Verifica e Collaudo Funzionale: Carico Merci & Tracciabilità HACCP
Eseguibile direttamente con: python test_carico_verification.py
"""

import sys
import datetime
from app import app, get_db_connection, db_pool
from psycopg2.extras import RealDictCursor

def run_qa_suite():
    print("=" * 70)
    print("AVVIO QA SUITE: VERIFICA FORM CARICO & TRACCIABILITÀ HACCP")
    print("=" * 70)

    test_client = app.test_client()
    passed_tests = 0
    failed_tests = 0

    def assert_test(condition, test_id, description):
        nonlocal passed_tests, failed_tests
        if condition:
            print(f"  [PASS] {test_id}: {description}")
            passed_tests += 1
        else:
            print(f"  [FAIL] {test_id}: {description}")
            failed_tests += 1

    # -------------------------------------------------------------
    # 1. VERIFICA DATABASE SCHEMA & ARTICOLI ESISTENTI
    # -------------------------------------------------------------
    print("\n--- 1. Verifica Schema Database & Dati di Base ---")
    conn = get_db_connection()
    bovino_art = None
    spezie_art = None
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Verifica colonna data_macellazione
            cur.execute("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'lotto_madre' AND column_name = 'data_macellazione';
            """)
            col = cur.fetchone()
            assert_test(col is not None and col['data_type'] == 'date', 
                        "TC-DB-01", "Colonna data_macellazione presente in LOTTO_MADRE come DATE")

            # Recupera un articolo Bovino e uno Spezie per i test successivi
            cur.execute("SELECT id_articolo, denominazione, categoria FROM ARTICOLO WHERE categoria = 'Bovino' LIMIT 1;")
            bovino_art = cur.fetchone()
            assert_test(bovino_art is not None, "TC-DB-SETUP-01", f"Trovato articolo Bovino: {bovino_art['denominazione']} (ID {bovino_art['id_articolo']})")

            cur.execute("SELECT id_articolo, denominazione, categoria FROM ARTICOLO WHERE categoria = 'Spezie' LIMIT 1;")
            spezie_art = cur.fetchone()
            assert_test(spezie_art is not None, "TC-DB-SETUP-02", f"Trovato articolo Spezie: {spezie_art['denominazione']} (ID {spezie_art['id_articolo']})")
    finally:
        db_pool.putconn(conn)

    # -------------------------------------------------------------
    # 2. VERIFICA FRONTEND DOM (GET /carico)
    # -------------------------------------------------------------
    print("\n--- 2. Verifica Frontend DOM & Rendering (GET /carico) ---")
    resp = test_client.get('/carico')
    assert_test(resp.status_code == 200, "TC-FE-01a", "GET /carico restituisce HTTP 200")
    html = resp.get_data(as_text=True)

    assert_test('data-categoria="Bovino"' in html or 'data-categoria="bovino"' in html.lower(), 
                "TC-FE-01b", "Presenza dell'attributo data-categoria nelle option del select")
    assert_test('id="sezione-tracciabilita"' in html, 
                "TC-FE-01c", "Presenza del contenitore #sezione-tracciabilita per i dati HACCP")
    assert_test('name="data_macellazione"' in html, 
                "TC-FE-01d", "Presenza dell'input per data_macellazione nel template")

    # -------------------------------------------------------------
    # 3. VERIFICA BACKEND VALIDATION (/salva_carico)
    # -------------------------------------------------------------
    print("\n--- 3. Verifica Backend Validation (POST /salva_carico) ---")
    future_date = (datetime.date.today() + datetime.timedelta(days=30)).strftime('%Y-%m-%d')
    past_date = (datetime.date.today() - datetime.timedelta(days=5)).strftime('%Y-%m-%d')
    valid_slaughter_date = (datetime.date.today() - datetime.timedelta(days=2)).strftime('%Y-%m-%d')

    # Test 3.1: Campi base mancanti
    resp = test_client.post('/salva_carico', data={
        'id_articolo': bovino_art['id_articolo'] if bovino_art else 1,
        'codice_lotto_fornitore': '',
        'fornitore': 'Fornitore Test'
    }, follow_redirects=True)
    html = resp.get_data(as_text=True)
    assert_test('obbligatori' in html.lower() or 'errore' in html.lower(), 
                "TC-BE-01", "Blocco submit con campi base mancanti")

    # Test 3.2: Articolo Carne (Bovino) senza campi paese
    resp = test_client.post('/salva_carico', data={
        'id_articolo': bovino_art['id_articolo'],
        'codice_lotto_fornitore': 'L-TEST-ERR1',
        'fornitore': 'Fornitore Test',
        'data_scadenza': future_date,
        'paese_nascita': '',
        'paese_allevamento': '',
        'paese_macellazione': '',
        'paese_sezionamento': ''
    }, follow_redirects=True)
    html = resp.get_data(as_text=True)
    assert_test('tracciabilità' in html.lower() or 'campi' in html.lower() or 'obbligatori' in html.lower(), 
                "TC-BE-03", "Blocco carico carne se i campi paese sono vuoti")

    # Test 3.3: Articolo Carne (Bovino) senza né data macellazione né data scadenza
    resp = test_client.post('/salva_carico', data={
        'id_articolo': bovino_art['id_articolo'],
        'codice_lotto_fornitore': 'L-TEST-ERR2',
        'fornitore': 'Fornitore Test',
        'paese_nascita': 'ITA',
        'paese_allevamento': 'ITA',
        'paese_macellazione': 'ITA',
        'paese_sezionamento': 'ITA',
        'data_macellazione': '',
        'data_scadenza': ''
    }, follow_redirects=True)
    html = resp.get_data(as_text=True)
    assert_test('data' in html.lower() or 'macellazione' in html.lower() or 'scadenza' in html.lower(), 
                "TC-BE-04", "Blocco carico carne se mancano sia data macellazione che data scadenza")

    # Test 3.4: Carico Carne Valido con tutti i campi
    lotto_test_carne = f"L-BOV-{datetime.datetime.now().strftime('%M%S')}"
    resp = test_client.post('/salva_carico', data={
        'id_articolo': bovino_art['id_articolo'],
        'codice_lotto_fornitore': lotto_test_carne,
        'fornitore': 'Allevamento Rossi',
        'paese_nascita': 'ITA',
        'paese_allevamento': 'ITA',
        'paese_macellazione': 'IT-1234',
        'paese_sezionamento': 'IT-5678',
        'data_macellazione': valid_slaughter_date,
        'data_scadenza': future_date
    }, follow_redirects=True)
    html = resp.get_data(as_text=True)
    assert_test('successo' in html.lower() or 'registrato' in html.lower(), 
                "TC-BE-07", "Salvataggio riuscito per articolo carne completo")

    # Verifica DB inserimento carne
    conn = get_db_connection()
    inserted_carne_id = None
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM LOTTO_MADRE WHERE codice_lotto_fornitore = %s;", (lotto_test_carne,))
            row = cur.fetchone()
            assert_test(row is not None and str(row['data_macellazione']) == valid_slaughter_date,
                        "TC-BE-07-DB", "Record carne salvato nel DB con data_macellazione corretta")
            if row:
                inserted_carne_id = row['id_lotto_madre']
    finally:
        db_pool.putconn(conn)

    # Test 3.5: Carico Non-Carne (Spezie) con campi paese e data macellazione vuoti
    lotto_test_spezie = f"L-SPZ-{datetime.datetime.now().strftime('%M%S')}"
    resp = test_client.post('/salva_carico', data={
        'id_articolo': spezie_art['id_articolo'],
        'codice_lotto_fornitore': lotto_test_spezie,
        'fornitore': 'Spezie d\'Italia',
        'data_scadenza': future_date,
        'paese_nascita': '',
        'paese_allevamento': '',
        'paese_macellazione': '',
        'paese_sezionamento': '',
        'data_macellazione': ''
    }, follow_redirects=True)
    html = resp.get_data(as_text=True)
    assert_test('successo' in html.lower() or 'registrato' in html.lower(), 
                "TC-BE-09", "Salvataggio riuscito per articolo non-carne con campi paese vuoti")

    # Verifica DB inserimento non-carne (valori NULL)
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM LOTTO_MADRE WHERE codice_lotto_fornitore = %s;", (lotto_test_spezie,))
            row = cur.fetchone()
            assert_test(row is not None and row['paese_nascita'] is None and row['data_macellazione'] is None,
                        "TC-BE-09-DB", "Record non-carne salvato nel DB con paesi e data_macellazione a NULL")
    finally:
        db_pool.putconn(conn)

    # -------------------------------------------------------------
    # 4. VERIFICA NON-REGRESSIONE ROUTE ESISTENTI
    # -------------------------------------------------------------
    print("\n--- 4. Verifica Non-Regressione Route Esistenti ---")

    # 4.1 Index
    resp = test_client.get('/')
    assert_test(resp.status_code == 200, "TC-REG-01", "GET / risponde 200 OK")

    # 4.2 Magazzino
    resp = test_client.get('/magazzino')
    assert_test(resp.status_code == 200, "TC-REG-02", "GET /magazzino risponde 200 OK")

    # 4.3 Stampa Etichetta Taglio
    if inserted_carne_id:
        resp = test_client.get(f'/stampa_etichetta_taglio/{inserted_carne_id}')
        assert_test(resp.status_code == 200, "TC-REG-03", f"GET /stampa_etichetta_taglio/{inserted_carne_id} risponde 200 OK")

    # 4.4 DB Status API
    resp = test_client.get('/api/db_status')
    assert_test(resp.status_code == 200 and resp.json.get('status') == 'ok', 
                "TC-REG-06", "GET /api/db_status risponde 200 con status: ok")

    # 4.5 Download Excel
    resp = test_client.get('/download_excel')
    assert_test(resp.status_code == 200, "TC-REG-05", "GET /download_excel genera e scarica il file senza errori")

    # -------------------------------------------------------------
    # RIEPILOGO FINALE
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print(f"RIEPILOGO TEST: {passed_tests} SUPERATI, {failed_tests} FALLITI")
    print("=" * 70)
    return failed_tests == 0

if __name__ == '__main__':
    success = run_qa_suite()
    sys.exit(0 if success else 1)
```

---

## 6. Procedura di Collaudo Manuale per Operatore / Reviewer

Se si desidera collaudare manualmente l'applicazione da interfaccia utente:

1. **Avvio dell'applicazione**:
   ```bash
   python app.py
   ```
   Aprire il browser all'indirizzo `http://localhost:5000/carico`.

2. **Test Dinamica Frontend**:
   - Verificare che all'apertura il form mostri solo i campi base e che la card con bordo rosso HACCP sia invisibile.
   - Aprire il dropdown "Prodotto" e selezionare **"Carne Macinata Bovino"**.
     * Verificare che la card **"TRACCIABILITÀ CARNE • DATI HACCP"** appaia istantaneamente.
   - Provare a premere "Salva Carico Merce" senza compilare i campi paese.
     * Verificare che il browser mostri l'avviso di campo obbligatorio sui campi paese.
   - Cambiare la selezione su **"Sale Marino Fine"** (Spezie).
     * Verificare che la card di tracciabilità scompaia immediatamente.
   - Compilare Lotto Fornitore (`L-SALE-01`), Fornitore (`Saline`), Scadenza (futura) e cliccare "Salva Carico Merce".
     * Verificare il redirect a `/magazzino` con messaggio verde di successo.

3. **Test Stampa Etichetta Taglio**:
   - Dalla schermata `/magazzino`, individuare un lotto di taglio fresco (badge rosso `TAGLIO`).
   - Cliccare sul pulsante **"🖨️ Stampa Etichetta"**.
   - Verificare che la pagina si apra correttamente visualizzando denominazione, origine tracciabilità, date e barcode.
