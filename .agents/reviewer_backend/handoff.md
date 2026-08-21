# Handoff Report — Backend & Database Dead Code Review

**Data:** 2026-08-20  
**Agente:** Reviewer & Adversarial Critic (`reviewer_backend`)  
**Parent Task ID:** `417b37a5-594d-4b26-8aae-a3a1bc58b9a5`  
**Tipo Handoff:** Hard Handoff (Task completato al 100%)  
**Verdict:** **APPROVE**  

---

## 1. Observation

Sono stati analizzati ed esaminati riga per riga i seguenti file e componenti:
- `app.py` (480 righe, 10 rotte HTTP, 1 context processor, 4 helper functions).
- `database.sql` (270 righe, 7 tabelle, 7 sequenze, 2 indici, 1 vista SQL).
- I template Jinja2: `templates/header.html`, `templates/footer.html`, `templates/index.html`, `templates/carico.html`, `templates/magazzino.html`, `templates/etichetta.html`, `templates/etichetta_taglio.html`.
- Script frontend: `static/js/status_monitor.js`.
- Configurazione e doc: `package.json`, `README.md`.

Evidenze testuali dirette osservate:
1. **`app.py:4`**: `import psycopg2` è importato ma mai usato come modulo qualificato (`psycopg2.*`). Vengono usati solo i simboli importati alle righe 5-6 (`SimpleConnectionPool`, `RealDictCursor`).
2. **`database.sql:93`**: `flg_lotto_del_giorno boolean DEFAULT false`.
   - In `app.py:84`: `SELECT ... flg_lotto_del_giorno FROM LOTTO_MADRE ...`
   - In `app.py:324-325`: `WHERE id_articolo = %s AND (flg_lotto_del_giorno = TRUE OR data_scadenza >= CURRENT_DATE) ORDER BY flg_lotto_del_giorno DESC, data_carico DESC LIMIT 1`
   - In `app.py:245-252` (`salva_carico`): la query `INSERT INTO LOTTO_MADRE` omette completamente `flg_lotto_del_giorno`.
   - In `templates/carico.html:13-73`: nessun input checkbox/campo per `flg_lotto_del_giorno`.
3. **`database.sql:122`**: `versione integer DEFAULT 1`.
   - Zero occorrenze in `app.py`, template o viste SQL.
4. **`database.sql:124`**: `data_creazione timestamp DEFAULT CURRENT_TIMESTAMP`.
   - Zero occorrenze in `app.py`, template o viste SQL.
5. **`app.py:334-336`**:
   ```python
   else:
       # Registra tracciabilità mancante/vuota se l'ingrediente manca dal magazzino
       pass 
   ```
6. **`app.py:303`**:
   ```python
   # 3. Creazione o recupero sessione lavorazione (usiamo una sessione generica del giorno o ne creiamo una)
   cursor.execute("INSERT INTO SESSIONE_LAVORAZIONE (operatore) VALUES ('Operatore Banco') RETURNING id_sessione")
   ```
7. **Rotte ed Endpoint (`app.py`)**:
   - `inject_excel_filename` (`app.py:26`) -> usato in `templates/footer.html:9`
   - `/download_excel` (`app.py:146`) -> usato in `templates/footer.html:7`
   - `/` (`app.py:167`) -> usato in `templates/header.html:32`, `templates/etichetta.html:167`
   - `/carico` (`app.py:195`) -> usato in `templates/header.html:39`
   - `/salva_carico` (`app.py:215`) -> usato in `templates/carico.html:13`
   - `/magazzino` (`app.py:264`) -> usato in `templates/header.html:46`, `templates/etichetta_taglio.html:165`
   - `/produci_preparato/<int:id_articolo>` (`app.py:280`) -> usato in `templates/index.html:41`
   - `/stampa_etichetta/<int:id_lotto_preparato>` (`app.py:349`) -> redirect in `app.py:340`
   - `/stampa_etichetta_taglio/<int:id_lotto_madre>` (`app.py:392`) -> usato in `templates/index.html:19`, `templates/magazzino.html:44`
   - `/chiudi_sessione` (`app.py:434`) -> usato in `templates/footer.html:13`
   - `/api/db_status` (`app.py:464`) -> chiamato da `static/js/status_monitor.js:2`

---

## 2. Logic Chain

1. Dall'osservazione 7, tutte le 10 rotte e il context processor sono referenziati nei file template o JS; pertanto, **non esistono rotte orfane** nel backend.
2. Dall'osservazione 2, poiché `flg_lotto_del_giorno` non viene mai scritto a `TRUE` da alcuna rotta o form, tutte le righe mantengono il default `false`. Di conseguenza, il filtro `flg_lotto_del_giorno = TRUE` e l'ordinamento `ORDER BY flg_lotto_del_giorno DESC` in `app.py:324-325` costituiscono una **funzionalità zombie / dead write**.
3. Dalle osservazioni 3 e 4, `RICETTA.versione` e `RICETTA.data_creazione` non compaiono in alcuna query SELECT, INSERT, UPDATE, JOIN o nella vista `vw_etichetta_preparato`; pertanto sono **colonne DB morte / inutilizzate**.
4. Dall'osservazione 1, `import psycopg2` non ha chiamate corrispondenti nel modulo; pertanto è un **import ridondante**.
5. Dall'osservazione 5, il blocco `else: pass` non gestisce l'assenza del lotto ingrediente, producendo silenziosamente buchi di tracciabilità nel foglio Excel HACCP.
6. Dall'osservazione 6, l'assenza di un controllo preventivo di sessione aperta genera record ridondanti in `SESSIONE_LAVORAZIONE` ad ogni produzione.
7. Tutti i rilievi presentati da `explorer_backend_survey` (`backend_survey.md`) sono conformi alle osservazioni e alla catena logica senza omissioni o falsi positivi.

---

## 3. Caveats

- Nessuna modifica al codice sorgente è stata effettuata (vincolo di sola lettura rispettato).
- L'analisi del frontend React (`src/`) è stata limitata a confermare che non è collegato al backend Flask (compito delegato specificamente all'Explorer/Reviewer Frontend).
- Nessun altro caveat identificato.

---

## 4. Conclusion

**Verdict: APPROVE**  
Il report dell'Explorer per il backend e database è promosso a pieni voti. I risultati sono pronti per essere aggregati dal Writer nel report finale `dead_code_report.md`.

---

## 5. Verification Method

Per verificare in modo indipendente:
1. Verificare l'assenza di riferimenti a `RICETTA.versione`:
   - Ispezionare `app.py` per il pattern `versione` -> 0 occorrenze nelle query SQL.
2. Verificare l'assenza di scrittura di `flg_lotto_del_giorno`:
   - Ispezionare `salva_carico` (`app.py:245-253`) e `templates/carico.html` -> il campo non compare nella lista parametri né nel form.
3. Verificare tutte le rotte:
   - Ispezionare `app.py` per `@app.route` e `@app.context_processor` e verificare le corrispondenze nei template Jinja2.
