# Report di Indagine Backend e Database (Dead Code & Architecture Survey)

**Data indagine:** 2026-08-20  
**Agente:** Explorer Subagent (`explorer_backend_survey`)  
**Repository target:** `C:\Users\david\Desktop\Gestionale_Macelleria`  
**Modalità:** Read-Only Investigation (Nessuna modifica/cancellazione eseguita)

---

## 1. Executive Summary

L'architettura del backend dell'applicazione **Gestionale Macelleria** è costruita su **Python 3 / Flask** (`app.py`), interfacciata con un database relazionale **PostgreSQL** (`database.sql`) tramite connection pooling (`psycopg2.pool.SimpleConnectionPool`), rendering server-side Jinja2 (`templates/`) ed esportazione reportistica HACCP su fogli di calcolo Excel (`pandas` + `openpyxl`).

### Risultati Principali dell'Indagine:
1. **Rotte Flask:** 10 rotte HTTP + 1 context processor. Tutte le rotte risultano attive e collegate ai template Jinja2 o agli script frontend (`static/js/status_monitor.js`), senza endpoint completamente orfani.
2. **Funzioni e Helper Python:** 4 funzioni helper (`inject_excel_filename`, `get_db_connection`, `get_excel_path`, `aggiorna_file_excel`), 10 funzioni di gestione rotte. 
3. **Database Schema:** 7 tabelle relazionali, 7 sequenze associate, 2 indici secondari personalizzati, 1 vista SQL (`vw_etichetta_preparato`). Nessun trigger o stored procedure presente.
4. **Dead Code & Anomalie Identificate:**
   - **DB Flag orfano (`LOTTO_MADRE.flg_lotto_del_giorno`):** La colonna è letta nelle query di selezione (`app.py:84, 324`), ma **nessuna rotta o form frontend ne permette la scrittura o l'aggiornamento** a `TRUE`. Tutti i record mantengono permanentemente il valore di default `false`.
   - **DB Colonne mai referenziate (`RICETTA.versione`, `RICETTA.data_creazione`):** Definite nello schema DDL ma mai lette, filtrate o manipolate dal codice applicativo o dalle viste.
   - **Import ridondante (`import psycopg2` in `app.py:4`):** Modulo importato per intero al livello radice, ma l'applicazione utilizza esclusivamente le classi importate puntualmente (`SimpleConnectionPool`, `RealDictCursor`).
   - **Dead `else: pass` in `app.py:334-336`:** Blocco condizionale vuoto senza alcuna logica o logging di fallback per ingredienti mancanti.
   - **Creazione ridondante di sessioni (`app.py:303`):** Viene eseguita una `INSERT INTO SESSIONE_LAVORAZIONE` ad ogni singolo click di produzione anziché verificare se esiste già una sessione aperta per la giornata.
   - **Scaffolding React/Vite estraneo (`src/`, `package.json`, `vite.config.ts`, `tsconfig.json`):** Residuo informativo di Google AI Studio che non partecipa all'esecuzione del gestionale Flask.

---

## 2. Inventario File Backend e Database

| Percorso File | Dimensione | Tipo | Scopo nel Sistema |
|---|---|---|---|
| `app.py` | 20.7 KB (480 righe) | Backend Python (Flask) | Core application: connection pool, rotte, logica di business, export Excel |
| `database.sql` | 10.2 KB (270 righe) | Schema PostgreSQL (DDL) | Creazione tabelle, sequenze, vincoli di integrità referenziale, indici, vista |
| `.env` | ~80 B | Configurazione Ambiente | `DATABASE_URL` e `SECRET_KEY` |
| `static/js/status_monitor.js` | 1.1 KB (30 righe) | Frontend JS | Polling asincrono su `/api/db_status` per indicatore di connessione DB |

---

## 3. Mappatura Completa Rotte ed Endpoint Flask (`app.py`)

| # | Endpoint / Regola URL | Metodi HTTP | Funzione Python (Linee) | Input / Parametri | Interazioni DB / Operazioni | Output / Template / Risposta | Origine Chiamata (Template / JS) |
|---|---|---|---|---|---|---|---|
| 1 | `@app.context_processor` | N/A | `inject_excel_filename` (26-31) | Nessuno | Nessuna query DB. Calcola mese/anno corrente. | Inietta variabile `excel_filename` nel context Jinja2 | `templates/footer.html:9` |
| 2 | `/` | `GET` | `index` (167-194) | Nessuno | `SELECT * FROM ARTICOLO ORDER BY denominazione;`<br>`SELECT id_lotto_madre FROM LOTTO_MADRE WHERE id_articolo = %s ORDER BY data_carico DESC LIMIT 1;` | `render_template('index.html', catalogo=catalogo)` | `templates/header.html:32`, `templates/etichetta.html:167`, Redirect post-errore |
| 3 | `/carico` | `GET` | `carico` (195-214) | Nessuno | `SELECT * FROM ARTICOLO WHERE tipo_categoria IN ('TAGLIO', 'VARIO') ORDER BY categoria, denominazione;` | `render_template('carico.html', articoli_per_categoria=articoli_per_categoria)` | `templates/header.html:39` |
| 4 | `/salva_carico` | `POST` | `salva_carico` (215-263) | Form: `id_articolo`, `codice_lotto_fornitore`, `fornitore`, `data_scadenza`, `paese_nascita`, `paese_allevamento`, `paese_macellazione`, `paese_sezionamento` | `INSERT INTO LOTTO_MADRE (id_articolo, codice_lotto_fornitore, fornitore, data_scadenza, ...) VALUES (...)` | Redirect `url_for('magazzino')` (successo) o `url_for('carico')` (errore) | `templates/carico.html:13` |
| 5 | `/magazzino` | `GET` | `magazzino` (264-279) | Nessuno | `SELECT lm.*, a.denominazione, a.tipo_categoria FROM LOTTO_MADRE lm JOIN ARTICOLO a ON lm.id_articolo = a.id_articolo ORDER BY lm.data_carico DESC;` | `render_template('magazzino.html', giacenze=giacenze)` | `templates/header.html:46`, `templates/etichetta_taglio.html:165`, Redirect da `salva_carico` |
| 6 | `/produci_preparato/<int:id_articolo>` | `POST` | `produci_preparato` (280-348) | URL param: `id_articolo` | 1. `SELECT id_ricetta FROM RICETTA WHERE id_articolo_preparato = %s AND attiva = TRUE`<br>2. `INSERT INTO SESSIONE_LAVORAZIONE (operatore) VALUES ('Operatore Banco') RETURNING id_sessione`<br>3. `INSERT INTO LOTTO_PREPARATO (...) RETURNING id_lotto_preparato`<br>4. `SELECT id_articolo_ingrediente FROM RICETTA_RIGA WHERE id_ricetta = %s`<br>5. `SELECT id_lotto_madre FROM LOTTO_MADRE WHERE id_articolo = %s AND (flg_lotto_del_giorno = TRUE OR data_scadenza >= CURRENT_DATE) ORDER BY flg_lotto_del_giorno DESC, data_carico DESC LIMIT 1`<br>6. `INSERT INTO COMPOSIZIONE_LAVORAZIONE (...)` | Redirect `url_for('stampa_etichetta', id_lotto_preparato=...)` | `templates/index.html:41` (Pulsante 1-Click) |
| 7 | `/stampa_etichetta/<int:id_lotto_preparato>` | `GET` | `stampa_etichetta` (349-391) | URL param: `id_lotto_preparato` | 1. `SELECT lp.*, a.denominazione FROM LOTTO_PREPARATO lp JOIN ARTICOLO a ON lp.id_articolo = a.id_articolo WHERE lp.id_lotto_preparato = %s`<br>2. `SELECT ingrediente, allergeni FROM VW_ETICHETTA_PREPARATO WHERE id_lotto_preparato = %s ORDER BY ordine_etichetta` | `render_template('etichetta.html', preparato=preparato, ingredienti=..., allergeni=...)` | Redirect da `produci_preparato` |
| 8 | `/stampa_etichetta_taglio/<int:id_lotto_madre>` | `GET` | `stampa_etichetta_taglio` (392-433) | URL param: `id_lotto_madre` | `SELECT lm.*, a.denominazione, a.categoria, a.tipo_categoria FROM LOTTO_MADRE lm JOIN ARTICOLO a ON lm.id_articolo = a.id_articolo WHERE lm.id_lotto_madre = %s AND a.tipo_categoria = 'TAGLIO'` | `render_template('etichetta_taglio.html', taglio=taglio)` | `templates/index.html:19`, `templates/magazzino.html:44` |
| 9 | `/chiudi_sessione` | `POST` | `chiudi_sessione` (434-463) | Nessuno (Form POST vuoto con confirm) | `UPDATE SESSIONE_LAVORAZIONE SET data_fine = CURRENT_TIMESTAMP, stato_sessione = 'Chiusa' WHERE stato_sessione = 'Aperta';` | Redirect `url_for('index')` | `templates/footer.html:13` |
| 10 | `/api/db_status` | `GET` | `db_status` (464-477) | Nessuno | `SELECT 1;` | JSON: `{"status": "ok"}` (200) o `{"status": "error"}` (500) | `static/js/status_monitor.js:2` |
| 11 | `/download_excel` | `GET` | `download_excel` (146-166) | Nessuno | Chiama `aggiorna_file_excel()` (esegue 3 query analitiche via Pandas) | `send_file(percorso, as_attachment=True, download_name=...)` | `templates/footer.html:7` |

---

## 4. Moduli Python, Funzioni Helper e Stato Globale (`app.py`)

### 4.1. Import e Dipendenze
- `os`, `datetime`, `threading`, `tempfile` (Python Standard Library): tutti utilizzati attivamente.
- `from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify`: tutti utilizzati.
- `import psycopg2` (Linea 4): **Import ridondante**. L'applicazione non chiama funzioni dirette del modulo `psycopg2` (come `psycopg2.connect`), in quanto il pooling e i cursori provengono dai sotto-moduli `psycopg2.pool.SimpleConnectionPool` e `psycopg2.extras.RealDictCursor`.
- `from psycopg2.pool import SimpleConnectionPool`: utilizzato per istanziare `db_pool` (Linee 34-38).
- `from psycopg2.extras import RealDictCursor`: utilizzato nei cursori per restituire dizionari chiave-valore.
- `import pandas as pd`: utilizzato in `aggiorna_file_excel` (`pd.read_sql_query`, `pd.ExcelWriter`).
- `from dotenv import load_dotenv`: utilizzato per caricare `.env` all'avvio (Linea 21).

### 4.2. Costanti e Oggetti Globali
- `MESI_ITALIANI` (Linee 13-17): Dizionario di mapping `1: 'Gennaio' ... 12: 'Dicembre'`. Utilizzato in `inject_excel_filename`, `get_excel_path`, `download_excel`.
- `_excel_write_lock` (Linea 19): `threading.Lock()` per serializzare la generazione concorrente del file Excel.
- `app` (Linea 23): Istanza Flask configurata con `secret_key`.
- `db_pool` (Linee 34-38): Pool di connessioni PostgreSQL con capacità `minconn=1, maxconn=10`.

### 4.3. Funzioni Helper Interne
1. `get_db_connection() -> connection` (Linee 40-42):
   - Estrae una connessione dal pool `db_pool.getconn()`.
   - Pattern di rilascio: ogni route esegue `db_pool.putconn(conn)` in un blocco protetto `finally`.
2. `get_excel_path(anno: int = None, mese: int = None) -> str` (Linee 44-63):
   - Calcola il percorso `~/Desktop/tracciabilità negozio/Registro_Tracciabilita_{nome_mese}_{anno}.xlsx`.
   - Crea la directory se inesistente (`os.makedirs(cartella, exist_ok=True)`).
3. `aggiorna_file_excel()` (Linee 65-144):
   - Esegue 3 query analitiche con parametri di intervallo `[inizio_mese, fine_mese)`:
     - `query_carichi`: `SELECT ... FROM LOTTO_MADRE WHERE data_carico >= %s AND data_carico < %s`
     - `query_preparati`: `SELECT ... FROM LOTTO_PREPARATO WHERE data_lavorazione >= %s AND data_lavorazione < %s`
     - `query_haccp`: JOIN tra `COMPOSIZIONE_LAVORAZIONE`, `LOTTO_PREPARATO`, `ARTICOLO` (preparato e ingrediente), `LOTTO_MADRE`.
   - Scrittura atomica thread-safe tramite file temporaneo (`tempfile.mkstemp`) e `os.replace`.

---

## 5. Mappatura Dettagliata Schema Database (`database.sql`)

Lo schema SQL definisce 7 tabelle relazionali, 7 sequenze, vincoli di chiave primaria ed esterne, 2 indici B-Tree e 1 vista SQL.

```
+---------------------------------------------------------------------------------------------------+
|                                       SCHEMA RELAZIONALE                                          |
+---------------------------------------------------------------------------------------------------+

   +--------------------------+             1:N             +--------------------------+
   |         ARTICOLO         | <-------------------------- |       LOTTO_MADRE        |
   +--------------------------+                             +--------------------------+
   | PK id_articolo           |                             | PK id_lotto_madre        |
   |    denominazione         |                             | FK id_articolo           |
   |    categoria             |                             |    codice_lotto_fornitore|
   |    allergeni             |                             |    fornitore             |
   |    tipo_categoria        |                             |    data_carico           |
   +--------------------------+                             |    data_scadenza         |
        ^               ^                                   |    paese_nascita         |
        | 1:N           | 1:N                               |    paese_allevamento     |
        |               |                                   |    paese_macellazione    |
   +----+-----+   +-----+--------------------+              |    paese_sezionamento    |
   | RICETTA  |   |   RICETTA_RIGA           |              | [!]flg_lotto_del_giorno  |
   +----------+   +--------------------------+              +--------------------------+
   |PK id_ric. |   | PK id_ricetta_riga       |                           ^
   |FK id_art. |<--| FK id_ricetta            |                           | 1:N
   |[!]versione|   | FK id_articolo_ingred.   |                           |
   |   attiva  |   |    ordine_etichetta      |              +------------+-------------+
   |[!]data_cr.|   +--------------------------+              | COMPOSIZIONE_LAVORAZIONE |
   +----------+                                              +--------------------------+
        ^                                                    | PK id_composizione       |
        | 1:N                                                | FK id_lotto_preparato    |
   +----+---------------------+                              | FK id_lotto_madre        |
   |     LOTTO_PREPARATO      | <----------------------------|    note_associazione     |
   +--------------------------+         1:N                  +--------------------------+
   | PK id_lotto_preparato    |
   | FK id_sessione           | ----+
   | FK id_articolo           |     |
   | FK id_ricetta            |     | N:1
   |    codice_lotto_interno  |     v
   |    data_lavorazione      |  +--------------------------+
   |    data_scadenza_prepar. |  |   SESSIONE_LAVORAZIONE   |
   +--------------------------+  +--------------------------+
                                 | PK id_sessione           |
                                 |    data_ora_inizio       |
                                 |    operatore             |
                                 |    stato_sessione        |
                                 |    data_fine             |
                                 +--------------------------+
```

### 5.1. Tabelle, Colonne e Stato di Utilizzo

| Tabella | Colonna | Tipo Dati & Vincoli | Utilizzo nel Backend / UI | Stato / Diagnosi |
|---|---|---|---|---|
| **`articolo`** | `id_articolo` | `integer NOT NULL PK (seq)` | PK in tutte le selezioni, form di carico, produzione | **Attiva** |
| | `denominazione` | `varchar(255) NOT NULL` | Mostrata in Vetrina, Carico, Magazzino, Etichette, Excel | **Attiva** |
| | `categoria` | `varchar(100) NOT NULL` | Raggruppamento form carico, controllo HACCP bovini | **Attiva** |
| | `allergeni` | `text` | Badge UI vetrina, aggregazione etichetta preparati | **Attiva** |
| | `tipo_categoria` | `varchar(20) DEFAULT 'VARIO' CHECK` | Filtro vetrina (`TAGLIO`, `PREPARATO`, `VARIO`), filtro carico | **Attiva** |
| **`sessione_lavorazione`** | `id_sessione` | `integer NOT NULL PK (seq)` | FK in `LOTTO_PREPARATO`, tracciabilità sessione | **Attiva** |
| | `data_ora_inizio` | `timestamp DEFAULT CURRENT_TIMESTAMP`| Timestamp automatico di avvio | **Attiva** |
| | `operatore` | `varchar(100) NOT NULL` | Impostato a `'Operatore Banco'` | **Attiva** (valore fisso) |
| | `stato_sessione` | `varchar(50) DEFAULT 'Aperta'` | Filtro e aggiornamento in `/chiudi_sessione` | **Attiva** |
| | `data_fine` | `timestamp` | Aggiornato in `/chiudi_sessione` | **Attiva** |
| **`lotto_madre`** | `id_lotto_madre` | `integer NOT NULL PK (seq)` | PK, FK in composizione lavorazione, stampa etichetta taglio | **Attiva** |
| | `id_articolo` | `integer NOT NULL FK(articolo)` | Articolo associato al carico | **Attiva** |
| | `codice_lotto_fornitore` | `varchar(100) NOT NULL` | Inserito in carico, mostrato in magazzino/etichetta/Excel | **Attiva** |
| | `fornitore` | `varchar(255) NOT NULL` | Inserito in carico, mostrato in magazzino/Excel | **Attiva** |
| | `data_carico` | `timestamp DEFAULT CURRENT_TIMESTAMP`| Ordinamento carichi e filtro mensile Excel | **Attiva** |
| | `data_scadenza` | `date NOT NULL` | Validazione form, visualizzazione magazzino/etichetta/Excel | **Attiva** |
| | `paese_nascita` | `varchar(100)` | Tracciabilità carne bovina, etichetta taglio fresco | **Attiva** |
| | `paese_allevamento` | `varchar(100)` | Tracciabilità carne bovina, etichetta taglio fresco | **Attiva** |
| | `paese_macellazione`| `varchar(100)` | Tracciabilità carne bovina, etichetta taglio fresco | **Attiva** |
| | `paese_sezionamento`| `varchar(100)` | Tracciabilità carne bovina, etichetta taglio fresco | **Attiva** |
| | `flg_lotto_del_giorno`| `boolean DEFAULT false` | Letta in `query_carichi` e `produci_preparato`, ma **mai scritta a TRUE** | **⚠️ Zombie / Dead Write** |
| **`ricetta`** | `id_ricetta` | `integer NOT NULL PK (seq)` | PK, FK in ricetta_riga e lotto_preparato | **Attiva** |
| | `id_articolo_preparato`| `integer NOT NULL FK(articolo)` | Identifica il preparato collegato | **Attiva** |
| | `versione` | `integer DEFAULT 1` | **Mai referenziata** in alcuna query, logica o interfaccia | **❌ Colonna Inutilizzata** |
| | `attiva` | `boolean DEFAULT true` | Utilizzata per selezionare la ricetta corrente in produzione | **Attiva** |
| | `data_creazione` | `timestamp DEFAULT CURRENT_TIMESTAMP`| **Mai referenziata** in alcuna query o interfaccia | **❌ Colonna Inutilizzata** |
| **`ricetta_riga`** | `id_ricetta_riga`| `integer NOT NULL PK (seq)` | PK | **Attiva** |
| | `id_ricetta` | `integer FK(ricetta)` | Associazione alla ricetta | **Attiva** |
| | `id_articolo_ingrediente`| `integer FK(articolo)` | Identifica l'ingrediente da prelevare | **Attiva** |
| | `ordine_etichetta` | `integer NOT NULL` | Ordinamento ingredienti nell'etichetta e nella vista | **Attiva** |
| **`lotto_preparato`** | `id_lotto_preparato` | `integer NOT NULL PK (seq)` | PK, passato alla stampa etichetta e all'HACCP | **Attiva** |
| | `id_sessione` | `integer FK(sessione_lavorazione)`| Collega la sessione di lavorazione | **Attiva** |
| | `id_articolo` | `integer FK(articolo)` | Articolo preparato prodotto | **Attiva** |
| | `id_ricetta` | `integer FK(ricetta)` | Ricetta utilizzata | **Attiva** |
| | `codice_lotto_interno`| `varchar(100) UNIQUE NOT NULL` | Codice tracciabilità interno generato (timestamp) | **Attiva** |
| | `data_lavorazione` | `timestamp DEFAULT CURRENT_TIMESTAMP`| Data e ora produzione, filtro Excel | **Attiva** |
| | `data_scadenza_preparato`| `date NOT NULL` | Scadenza calcolata (+3gg), etichetta, Excel | **Attiva** |
| **`composizione_lavorazione`** | `id_composizione` | `integer NOT NULL PK (seq)` | PK | **Attiva** |
| | `id_lotto_preparato`| `integer FK(lotto_preparato)` | Lotto preparato di destinazione | **Attiva** |
| | `id_lotto_madre` | `integer FK(lotto_madre)` | Lotto fornitore di origine dell'ingrediente | **Attiva** |
| | `note_associazione` | `varchar(255)` | Note tracciabilità (es. "Assegnazione automatica banco") | **Attiva** |

### 5.2. Viste SQL
- **`public.vw_etichetta_preparato`**:
  - **Definizione:**
    ```sql
    CREATE VIEW public.vw_etichetta_preparato AS
     SELECT lp.id_lotto_preparato,
        lp.codice_lotto_interno,
        ing.denominazione AS ingrediente,
        ing.allergeni,
        rr.ordine_etichetta
       FROM (((public.lotto_preparato lp
         JOIN public.ricetta r ON ((lp.id_ricetta = r.id_ricetta)))
         JOIN public.ricetta_riga rr ON ((r.id_ricetta = rr.id_ricetta)))
         JOIN public.articolo ing ON ((rr.id_articolo_ingrediente = ing.id_articolo)))
      ORDER BY lp.id_lotto_preparato, rr.ordine_etichetta;
    ```
  - **Utilizzo:** Utilizzata attivamente in `app.py:370` all'interno della rotta `/stampa_etichetta/<int:id_lotto_preparato>`.
  - **Stato:** **Attiva**.

### 5.3. Indici Secondari
1. `idx_articolo_tipo` ON `public.articolo (tipo_categoria)`: **Attivo** (supporta i filtri su catalogo e carico).
2. `idx_ricetta_attiva` UNIQUE ON `public.ricetta (id_articolo_preparato)` WHERE `(attiva = true)`: **Attivo** (garantisce l'unicità della ricetta attiva per preparato).

---

## 6. Analisi Dettagliata Dead Code, Oggetti Inutilizzati e Anomalie

### 6.1. Anomalie a Livello Database

#### 1. Colonna Zombie / Inattiva: `LOTTO_MADRE.flg_lotto_del_giorno`
- **Descrizione:** Campo booleano impostato con default `false` nello schema (`database.sql:94`).
- **Occorrenze nel codice:**
  - `app.py:84`: `SELECT ... flg_lotto_del_giorno FROM LOTTO_MADRE ...` (query export Excel)
  - `app.py:324`: `WHERE id_articolo = %s AND (flg_lotto_del_giorno = TRUE OR data_scadenza >= CURRENT_DATE) ORDER BY flg_lotto_del_giorno DESC, data_carico DESC LIMIT 1`
- **Problema / Giustificazione:** Non esiste alcun meccanismo (né form HTML in `carico.html`, né parametro nella rotta `/salva_carico`, né job batch o script ausiliario) per impostare questo flag a `TRUE`. Di conseguenza, il flag vale sempre `false` per ogni riga inserita dall'applicazione, rendendo la clausola `flg_lotto_del_giorno = TRUE` e l'ordinamento prioritario `ORDER BY flg_lotto_del_giorno DESC` un ramo logico permanentemente inerte.
- **Raccomandazione:** Aggiungere un checkbox nel form di carico/magazzino per valorizzarlo, oppure rimuovere il flag e la relativa logica se non necessaria.

#### 2. Colonne Definite e Mai Referenziate: `RICETTA.versione` e `RICETTA.data_creazione`
- **Descrizione:**
  - `RICETTA.versione` (`database.sql:122`): `versione integer DEFAULT 1`
  - `RICETTA.data_creazione` (`database.sql:124`): `data_creazione timestamp DEFAULT CURRENT_TIMESTAMP`
- **Occorrenze nel codice:** Zero occorrenze in `app.py`, nei template o nelle viste SQL.
- **Giustificazione:** La query in `produci_preparato` (`app.py:286`) seleziona unicamente `id_ricetta` filtrando per `id_articolo_preparato` e `attiva = TRUE`. I campi `versione` e `data_creazione` non vengono mai letti, incrementati, visualizzati o esportati.
- **Raccomandazione:** Mantenere se previsti per futura gestione del versioning ricette da interfaccia admin, oppure documentarne lo stato inattivo.

---

### 6.2. Anomalie a Livello Backend Python

#### 1. Import Inutilizzato / Ridondante in `app.py:4`
- **Codice:** `import psycopg2`
- **Occorrenze:** L'applicazione fa uso esclusivamente di `from psycopg2.pool import SimpleConnectionPool` (riga 5) e `from psycopg2.extras import RealDictCursor` (riga 6). Nessuna chiamata diretta a `psycopg2.*` è presente in `app.py`.
- **Giustificazione:** Import di primo livello superfluo.
- **Raccomandazione:** Rimuovere `import psycopg2` per pulizia del namespace.

#### 2. Blocco Condizionale Vuoto (`Dead Else`) in `app.py:334-336`
- **Codice:**
  ```python
  if lotto_madre:
      cursor.execute("""
          INSERT INTO COMPOSIZIONE_LAVORAZIONE (id_lotto_preparato, id_lotto_madre, note_associazione)
          VALUES (%s, %s, %s)
      """, (id_lotto_preparato, lotto_madre['id_lotto_madre'], "Assegnazione automatica banco"))
  else:
      # Registra tracciabilità mancante/vuota se l'ingrediente manca dal magazzino
      pass 
  ```
- **Problema / Giustificazione:** Se un ingrediente della ricetta non ha giacenze valide in `LOTTO_MADRE`, il sistema silenziosamente non crea alcuna riga in `COMPOSIZIONE_LAVORAZIONE` senza emettere log di warning o avvisi all'operatore, compromettendo parzialmente la completezza della tracciabilità HACCP per quel preparato.
- **Raccomandazione:** Aggiungere un log (`app.logger.warning(...)`) o registrare un'associazione esplicita con nota "Lotto fornitore non reperito in magazzino".

#### 3. Gestione e Creazione Ridondante delle Sessioni di Lavorazione (`app.py:303`)
- **Codice:**
  ```python
  # 3. Creazione o recupero sessione lavorazione (usiamo una sessione generica del giorno o ne creiamo una)
  cursor.execute("INSERT INTO SESSIONE_LAVORAZIONE (operatore) VALUES ('Operatore Banco') RETURNING id_sessione")
  id_sessione = cursor.fetchone()['id_sessione']
  ```
- **Problema / Giustificazione:** Nonostante il commento indichi *"o recupero sessione lavorazione"*, il codice crea una *nuova* riga in `SESSIONE_LAVORAZIONE` ad ogni click di produzione di un preparato. Quando l'operatore preme "Chiudi Sessione" (`/chiudi_sessione`), la query chiude tutte le sessioni aperte in blocco (`UPDATE SESSIONE_LAVORAZIONE SET data_fine = CURRENT_TIMESTAMP, stato_sessione = 'Chiusa' WHERE stato_sessione = 'Aperta'`).
- **Raccomandazione:** Implementare il recupero dell'eventuale sessione già aperta nel giorno prima di crearne una nuova, oppure documentare tale comportamento per l'architettura.

---

### 6.3. Discrepanza Documentazione vs Codice su Export Excel

- **Documentazione (`README.md:73, 77`):** Afferma che il file Excel viene rigenerato automaticamente ad ogni operazione di carico o produzione.
- **Implementazione Reale (`app.py:146-166`):** `salva_carico` e `produci_preparato` non invocano `aggiorna_file_excel()`. La funzione `aggiorna_file_excel()` viene chiamata esclusivamente on-demand all'accesso dell'endpoint `/download_excel`.
- **Valutazione:** L'implementazione attuale è architetturalmente preferibile poiché evita I/O disco sincrono pesante su ogni transazione web, ma evidenzia una discrepanza con la documentazione utente.

---

### 6.4. Codice Frontend Scaffolding Estraneo (React/Vite)

- **Contesto:** Il repository include i file `src/App.tsx`, `src/main.tsx`, `src/index.css`, `package.json`, `vite.config.ts`, `tsconfig.json`.
- **Valutazione:** Come confermato da `README.md:13` e `src/App.tsx:28-30`, si tratta di un'interfaccia di sola presentazione generata dall'ambiente AI Studio per riassumere l'architettura. Non comunica con il backend Flask né con il database PostgreSQL.
- **Dipendenze NPM inutilizzate:** `@google/genai`, `express`, `motion`, `lucide-react`, `dotenv`, `@types/express`.

---

## 7. Matrice di Tracciabilità Incrociata (Cross-Reference Matrix)

| Oggetto Database | Tabelle Coinvolte | Letti da (Rotte / Funzioni) | Scritti da (Rotte / Funzioni) | Template / UI Coinvolti | Note Stato |
|---|---|---|---|---|---|
| `ARTICOLO` | `articolo` | `/`, `/carico`, `/produci_preparato`, `/stampa_etichetta`, `/stampa_etichetta_taglio`, `aggiorna_file_excel` | Nessuna rotta (DML iniziale) | `index.html`, `carico.html`, `magazzino.html`, `etichetta.html`, `etichetta_taglio.html` | Attivo al 100% |
| `SESSIONE_LAVORAZIONE` | `sessione_lavorazione` | `aggiorna_file_excel` (tramite FK) | `/produci_preparato`, `/chiudi_sessione` | `footer.html` (chiusura sessione) | Attivo |
| `LOTTO_MADRE` | `lotto_madre` | `/`, `/magazzino`, `/produci_preparato`, `/stampa_etichetta_taglio`, `aggiorna_file_excel` | `/salva_carico` | `index.html`, `magazzino.html`, `etichetta_taglio.html`, `carico.html` | Attivo (tranne `flg_lotto_del_giorno`) |
| `RICETTA` | `ricetta` | `/produci_preparato`, `vw_etichetta_preparato` | Nessuna rotta (DML iniziale) | Nessuno diretto | Attivo (tranne `versione`, `data_creazione`) |
| `RICETTA_RIGA` | `ricetta_riga` | `/produci_preparato`, `vw_etichetta_preparato` | Nessuna rotta (DML iniziale) | `etichetta.html` (tramite vista) | Attivo al 100% |
| `LOTTO_PREPARATO` | `lotto_preparato` | `/stampa_etichetta`, `aggiorna_file_excel`, `vw_etichetta_preparato` | `/produci_preparato` | `etichetta.html` | Attivo al 100% |
| `COMPOSIZIONE_LAVORAZIONE` | `composizione_lavorazione`| `aggiorna_file_excel` | `/produci_preparato` | Nessuno diretto (report HACCP Excel) | Attivo al 100% |
| `VW_ETICHETTA_PREPARATO` | (Vista) | `/stampa_etichetta` | N/A (Vista SQL) | `etichetta.html` | Attivo al 100% |

---

## 8. Conclusioni dell'Indagine

1. **Stato del Backend Flask:** L'applicazione Flask in `app.py` è concisa, compatta e coesa. Non esistono rotte orfane o endpoint abbandonati. Tutte le 10 rotte sono direttamente collegate al flusso operativo del banco macelleria.
2. **Stato del Database PostgreSQL:** Lo schema in `database.sql` è ben normalizzato e supporta fedelmente la tracciabilità HACCP. Le uniche porzioni di codice DB inattive sono:
   - Il flag `LOTTO_MADRE.flg_lotto_del_giorno` (mai scritto a TRUE).
   - I campi `RICETTA.versione` e `RICETTA.data_creazione` (mai letti dal backend).
3. **Pulizia e Manutenzione:** La rimozione dell'import ridondante `import psycopg2` e la gestione del ramo `else: pass` in produzione preparati rappresentano i miglioramenti primari a livello di codice Python.
