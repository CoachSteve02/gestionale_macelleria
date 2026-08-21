# Rapporto di Revisione Critica e Validazione Backend & Database

**Data revisione:** 2026-08-20  
**Revisore:** Reviewer & Adversarial Critic Subagent (`reviewer_backend`)  
**Oggetto della revisione:** Indagine condotta da `explorer_backend_survey` (`backend_survey.md`) e codice sorgente (`app.py`, `database.sql`, template Jinja2, configurazioni)  
**Modalità:** Strict Read-Only Verification & Adversarial Stress-Testing  

---

## 1. Review Summary & Verdict

### **VERDICT: APPROVE**

**Giudizio complessivo:**  
L'indagine svolta dall'Explorer Subagent (`backend_survey.md`) è **estremamente accurata, esaustiva e supportata al 100% dall'evidenza empirica nel codice**.  
Tutte le affermazioni relative a rotte attive, oggetti DB utilizzati, colonne orfane/zombie, import ridondanti e lacune logiche sono state verificate e confermate in modo indipendente tramite ispezione riga per riga. Non sono stati riscontrati falsi positivi né elementi di codice morto non identificati nell'ambito Backend/Database.

---

## 2. Sintesi delle Evidenze e Validazione Puntuale

| # | Elemento / Finding | Diagnosi Explorer | Verifica Indipendente Reviewer | Esito Verifica | Gravità |
|---|---|---|---|---|---|
| 1 | **Rotte Flask (10 rotte + 1 context processor)** | Tutte attive e collegate ai template Jinja2 o JS | Tracciate tutte le 10 rotte e il context processor: 0 endpoint orfani | **CONFERMATO (PASS)** | Info |
| 2 | **`LOTTO_MADRE.flg_lotto_del_giorno`** | Colonna Zombie / Dead Write (letta ma mai impostata a `TRUE`) | Verificato in `app.py:84, 324` e `app.py:245-252` (`salva_carico` non la scrive; form HTML non ha campo). Valore sempre `false`. | **CONFERMATO (PASS)** | **Major** (Logica) |
| 3 | **`RICETTA.versione`** | Colonna DDL mai referenziata da Python o viste | Verificato `database.sql:122` vs `app.py` (0 occorrenze) e template (0 occorrenze) | **CONFERMATO (PASS)** | **Minor** (DB Schema) |
| 4 | **`RICETTA.data_creazione`** | Colonna DDL mai referenziata da Python o viste | Verificato `database.sql:124` vs `app.py` (0 occorrenze) e template (0 occorrenze) | **CONFERMATO (PASS)** | **Minor** (DB Schema) |
| 5 | **`import psycopg2` in `app.py:4`** | Import di primo livello ridondante / inutilizzato | Verificato: usati solo `SimpleConnectionPool` e `RealDictCursor`. Nessuna chiamata `psycopg2.*`. | **CONFERMATO (PASS)** | **Minor** (Code Quality) |
| 6 | **`else: pass` in `app.py:334-336`** | Ramo condizionale vuoto / fallimento silenzioso tracciabilità | Verificato: se ingrediente assente in `LOTTO_MADRE`, l'associazione viene saltata senza log o avvisi | **CONFERMATO (PASS)** | **Major** (HACCP Traceability) |
| 7 | **Creazione Sessione in `app.py:303`** | `INSERT` non condizionale ad ogni click di produzione | Verificato: nuova riga `SESSIONE_LAVORAZIONE` ad ogni click; chiusura di massa in `/chiudi_sessione` | **CONFERMATO (PASS)** | **Minor** (Design / Data bloat) |
| 8 | **Discrepanza Doc Excel (`README.md:73`)** | Scrittura su ogni modifica dichiarata vs on-demand reale | Verificato: `salva_carico` e `produci_preparato` non chiamano `aggiorna_file_excel()`; chiamata solo in `/download_excel` | **CONFERMATO (PASS)** | **Minor** (Documentation) |
| 9 | **Scaffolding React/Vite (`src/`, `package.json`, ecc.)** | Residuo di presentazione AI Studio | Verificato: disconnesso da Flask/Postgres | **CONFERMATO (PASS)** | **Info / Scaffolding** |

---

## 3. Analisi Dettagliata per Singola Categoria

### 3.1. Verifica Completa Rotte Flask (`app.py`)

Tutte le 10 regole di routing e l'unico context processor sono stati esaminati per verificare che non esistano endpoint morti o abbandonati:

1. **`@app.context_processor def inject_excel_filename` (`app.py:26-31`)**:
   - *Invocazione:* Automatica all'atto di rendering di ogni template Jinja2.
   - *Utilizzo:* `templates/footer.html:9` (`{{ excel_filename }}`).
   - *Stato:* **Attivo al 100%**.
2. **`GET /` (`index`, `app.py:167-194`)**:
   - *Utilizzo:* `templates/header.html:32`, `templates/etichetta.html:167`, redirect in `app.py:163, 291, 345, 365, 462`.
   - *Stato:* **Attivo al 100%**.
3. **`GET /carico` (`carico`, `app.py:195-214`)**:
   - *Utilizzo:* `templates/header.html:39`, redirect in `app.py:228, 235, 239, 260`.
   - *Stato:* **Attivo al 100%**.
4. **`POST /salva_carico` (`salva_carico`, `app.py:215-263`)**:
   - *Utilizzo:* Form action in `templates/carico.html:13`.
   - *Stato:* **Attivo al 100%**.
5. **`GET /magazzino` (`magazzino`, `app.py:264-279`)**:
   - *Utilizzo:* `templates/header.html:46`, `templates/etichetta_taglio.html:165, 199`, redirect in `app.py:255, 411, 428`.
   - *Stato:* **Attivo al 100%**.
6. **`POST /produci_preparato/<int:id_articolo>` (`produci_preparato`, `app.py:280-348`)**:
   - *Utilizzo:* Form action con pulsante 1-Click in `templates/index.html:41`.
   - *Stato:* **Attivo al 100%**.
7. **`GET /stampa_etichetta/<int:id_lotto_preparato>` (`stampa_etichetta`, `app.py:349-391`)**:
   - *Utilizzo:* Redirect post-produzione da `app.py:340`.
   - *Stato:* **Attivo al 100%**.
8. **`GET /stampa_etichetta_taglio/<int:id_lotto_madre>` (`stampa_etichetta_taglio`, `app.py:392-433`)**:
   - *Utilizzo:* Link in `templates/index.html:19` e `templates/magazzino.html:44`.
   - *Stato:* **Attivo al 100%**.
9. **`POST /chiudi_sessione` (`chiudi_sessione`, `app.py:434-463`)**:
   - *Utilizzo:* Form action con conferma in `templates/footer.html:13`.
   - *Stato:* **Attivo al 100%**.
10. **`GET /api/db_status` (`db_status`, `app.py:464-477`)**:
    - *Utilizzo:* Polling AJAX a intervalli di 30s da `static/js/status_monitor.js:2`.
    - *Stato:* **Attivo al 100%**.
11. **`GET /download_excel` (`download_excel`, `app.py:146-166`)**:
    - *Utilizzo:* Link download nel footer in `templates/footer.html:7`.
    - *Stato:* **Attivo al 100%**.

---

### 3.2. Verifica Schema Database (`database.sql`)

L'intero DDL PostgreSQL è stato confrontato con tutte le query in `app.py` e le viste:

- **Tabelle (7/7 attive):** `articolo`, `sessione_lavorazione`, `lotto_madre`, `ricetta`, `ricetta_riga`, `lotto_preparato`, `composizione_lavorazione`.
- **Sequenze (7/7 attive):** Una sequenza per ogni PK di tabella.
- **Indici (2/2 attivi):** 
  - `idx_articolo_tipo` ON `articolo(tipo_categoria)` -> Utilizzato nei filtri catalogo/carico.
  - `idx_ricetta_attiva` UNIQUE ON `ricetta(id_articolo_preparato) WHERE attiva = true` -> Garantisce consistenza di business.
- **Viste (1/1 attiva):** `vw_etichetta_preparato` -> Utilizzata in `app.py:370` per l'estrazione degli ingredienti ordinati e allergeni dell'etichetta.
- **Colonne orfane / non utilizzate (2 confermate):**
  1. `ricetta.versione` (`database.sql:122`): nessun riferimento nel backend né nelle viste.
  2. `ricetta.data_creazione` (`database.sql:124`): nessun riferimento nel backend né nelle viste.
- **Colonne Zombie / Dead-Write (1 confermata):**
  1. `lotto_madre.flg_lotto_del_giorno` (`database.sql:93`): letta in due query (`app.py:84, 324`), ma **nessuna query o interfaccia utente la scrive mai a TRUE**.

---

### 3.3. Stress-Test Avversariale e Failure Modes

In qualità di Adversarial Critic, sono stati analizzati i seguenti scenari limite e rischi applicativi:

#### Fallimento 1: Ramo `else: pass` in `produci_preparato` (`app.py:334-336`)
- **Scenario:** L'operatore produce "Salsiccia Fresca", la cui ricetta include come ingredienti "Carne Suina" e "Spezie/Sale". Nel magazzino non è mai stato caricato il lotto madre delle Spezie (o è scaduto).
- **Comportamento Attuale:** `lotto_madre` risulta `None`. Il blocco esegue `pass`. Il lotto preparato viene creato con successo e l'etichetta viene stampata.
- **Impatto HACCP:** Nel foglio Excel `Registro_HACCP_Completo` (generato tramite `INNER JOIN COMPOSIZIONE_LAVORAZIONE`), l'ingrediente "Spezie" non compare affatto. L'ispettore sanitario che consulta il registro Excel vedrà un preparato parzialmente privo dei lotti madre di origine per alcuni ingredienti, senza alcuna indicazione di anomalia.
- **Mitigazione:** Registrare una riga con `note_associazione = 'LOTTO NON REPERITO / ASSENTE'` oppure loggare un warning/errore bloccante.

#### Fallimento 2: Concorrenza su `download_excel` e `_excel_write_lock` (`app.py:116`)
- **Scenario:** Due operatori cliccano simultaneamente su "Download Excel".
- **Analisi:** Il lock `_excel_write_lock` serializza correttamente la generazione del file. Il file temporaneo `tempfile.mkstemp` nella medesima cartella e la successiva `os.replace` garantiscono atomicità della sostituzione sul file system. Non si verificano corruzioni del file Excel. (Punto di forza del design attuale).

#### Fallimento 3: Moltiplicazione delle righe in `SESSIONE_LAVORAZIONE` (`app.py:303`)
- **Scenario:** 50 preparati prodotti in una giornata di lavoro.
- **Analisi:** Il database memorizza 50 record distinti in `SESSIONE_LAVORAZIONE` tutti con stato `'Aperta'` e operatore `'Operatore Banco'`. Alla chiusura, una singola `UPDATE` aggiorna tutte le 50 righe.
- **Impatto:** Spreco di righe e ID di sequenza nella tabella sessioni, disallineamento concettuale tra "sessione di lavoro del giorno" e "singola transazione di produzione".

---

## 4. Conclusioni e Raccomandazioni per il Report Finale

1. **Integrità del Survey Upstream:** Nessuna violazione di integrità rilevata. L'Explorer Subagent ha eseguito un'analisi onesta, rigorosa e precisa.
2. **Elementi da includere nella sezione Backend / DB del report finale `dead_code_report.md`:**
   - `LOTTO_MADRE.flg_lotto_del_giorno` (Colonna Zombie - Dead Write)
   - `RICETTA.versione` (Colonna DDL orfana)
   - `RICETTA.data_creazione` (Colonna DDL orfana)
   - `import psycopg2` in `app.py:4` (Import ridondante)
   - `app.py:334-336` (Ramo `else: pass` - logica di fallback mancante)
   - `app.py:303` (Creazione ridondante di sessioni)
   - Discrepanza documentazione vs codice sulla generazione Excel (`README.md:73`)
   - Scaffolding React/Vite estraneo (`src/`, `package.json`)
