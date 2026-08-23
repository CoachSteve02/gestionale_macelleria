# Original User Request

## Initial Request — 2026-08-20T20:00:40Z

# Teamwork Project Prompt

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview
> Requested team: Usa il team completo

L'obiettivo è eseguire un'analisi profonda e suddivisa del repository "Gestionale_Macelleria" per identificare file inutilizzati, codice morto e funzionalità obsolete. Il risultato finale deve essere esclusivamente un report dettagliato per la revisione manuale (non eliminare alcun file).

Working directory: C:\Users\david\Desktop\Gestionale_Macelleria
Integrity mode: demo

## Requirements

### R1. Analisi Backend e Database
Analizzare l'applicazione Flask (`app.py`), script accessori e lo schema del database (`database.sql`). Identificare endpoint non richiamati dal frontend, funzioni Python mai utilizzate e tabelle/colonne senza query associate.

### R2. Analisi Frontend e Asset Statici
Analizzare i template Jinja2 (`templates/`), i file React/TypeScript (`src/`) e le risorse statiche (`static/`). Identificare componenti non importati, template orfani e asset (immagini, stili) mai inclusi o serviti. Utilizzare i file di configurazione delle dipendenze (es. `package.json`) per guidare l'indagine.

### R3. Creazione del Report Finale
Generare un report Markdown strutturato (`dead_code_report.md` nella cartella artefatti). Il documento deve categorizzare il codice/file inutilizzati per area (Backend, DB, Frontend, Configurazione) e fornire una chiara giustificazione per l'inserimento di ciascun elemento.

## Acceptance Criteria

### Analisi Completa
- [ ] Il report finale `dead_code_report.md` è stato generato e salvato correttamente.
- [ ] Il report divide chiaramente i risultati tra Frontend, Backend, Database e Asset.
- [ ] Per ogni file o porzione di codice segnalata come "inutilizzata", il report riporta la giustificazione (es. "Nessuna occorrenza trovata nel repository tramite ricerca testuale").
- [ ] Nessun file o porzione di codice è stato eliminato o alterato nel repository originale durante l'analisi.

## Follow-up — 2026-08-22T15:47:20Z

This is a single self-contained fix; keep it small and focused.

Applicare le modifiche residue al repository "Gestionale_Macelleria" identificate dal Dead Code Report. La maggior parte dei fix è già stata applicata manualmente dall'utente. Rimangono 3 interventi precisi e circoscritti su file specifici.

Working directory: C:\Users\david\Desktop\Gestionale_Macelleria
Integrity mode: development

## Contesto

Il repository ha già ricevuto i seguenti fix (NON toccare):
- `import psycopg2` rimosso da `app.py`
- Fix tracciabilità HACCP (`else: pass` → `app.logger.warning` + INSERT NULL)
- Fix sessione lavorazione multipla (ora riusa quella aperta)
- Barra ricerca in `header.html` scoperta a `{% if request.endpoint == 'index' %}`
- `requirements.txt` creato
- `.gitignore` aggiornato con pattern Python
- Directory `src/` eliminata

## Requirements

### R1. Creare `.env.example`
Creare il file `.env.example` nella root del repository. Il file deve contenere un template con le variabili `DATABASE_URL` e `SECRET_KEY`, con valori di esempio non reali e commenti esplicativi in italiano.

### R2. Correggere `database.sql` — Allineamento con lo schema reale
Il file `database.sql` contiene ancora riferimenti a colonne che non esistono più nel database reale (già migrate da `pg_dump`). Occorre allinearlo allo schema attuale rimuovendo/correggendo:
1. Il DML alla riga 147-149 usa `flg_lotto_del_giorno` nel INSERT INTO LOTTO_MADRE. Questa colonna è stata rimossa dal database reale. Il DML va adattato di conseguenza (rimuovendo la colonna dall'INSERT e usando un valore di fallback sicuro per `codice_lotto_fornitore` che rispetti la regex `^[A-Za-z0-9\-]+$`, quindi senza underscore).
2. I DML INSERT INTO RICETTA (righe 118, 126, 134, 140) passano esplicitamente il campo `versione` che è stato rimosso dal database reale. Questi DML vanno semplificati rimuovendo `versione` e il suo valore dalla lista delle colonne.

### R3. Aggiornare `README.md` — Sezione generazione Excel
La documentazione esistente afferma che il file Excel HACCP viene rigenerato automaticamente ad ogni carico merce e ad ogni produzione. Questo comportamento è stato rimosso: ora l'Excel viene generato solo on-demand al click del pulsante di download. Aggiornare la sezione pertinente del README per riflettere il comportamento reale.

## Acceptance Criteria

### File e modifiche
- [ ] Il file `.env.example` esiste nella root del progetto con le variabili `DATABASE_URL` e `SECRET_KEY`.
- [ ] `database.sql` non contiene più riferimenti alla colonna `flg_lotto_del_giorno` nei DML.
- [ ] `database.sql` non contiene più il campo `versione` negli INSERT INTO RICETTA.
- [ ] Il valore `'LOTTO_DEFAULT'` (con underscore) nei DML di `database.sql` è stato sostituito con un valore compatibile con la regex `^[A-Za-z0-9\-]+$` (es. `'LOTTO-DEFAULT'`).
- [ ] Il `README.md` descrive correttamente la generazione on-demand dell'Excel.

### Integrità
- [ ] Nessun altro file del repository è stato modificato oltre a quelli elencati nei requirement.
- [ ] `app.py` non è stato toccato.

## Follow-up — 2026-08-23T10:57:09Z

Rendere dinamica la pagina "Carico Merci" del gestionale da macelleria (Flask 3.0 + PostgreSQL + Jinja2 + Tailwind CSS + vanilla JS). Il form deve mostrare dinamicamente sezioni di campi differenti in base al prodotto selezionato: campi di tracciabilità avanzata obbligatori per le categorie carni (Bovino, Suino, Avicolo), form semplificato per tutte le altre categorie. Il cambio di visibilità deve avvenire lato client (show/hide CSS) senza ricaricamento pagina né chiamate AJAX.

Working directory: c:\Users\david\Desktop\Gestionale_Macelleria
Integrity mode: demo

---

## Context tecnico

- **Stack**: Flask 3.0, PostgreSQL (psycopg2), Jinja2, Tailwind CSS (CDN), vanilla JS (nessun framework JS)
- **Tabella chiave**: `LOTTO_MADRE` — contiene i carichi da fornitore
- **Colonne già presenti** in `LOTTO_MADRE`: `paese_nascita`, `paese_allevamento`, `paese_macellazione`, `paese_sezionamento`
- **Colonna mancante** da aggiungere: `data_macellazione DATE` (nullable)
- **Discriminante categoria**: campo `categoria` (stringa) nella tabella `ARTICOLO`
  - Categorie carne (tracciabilità avanzata): **Bovino, Suino, Avicolo**
  - Tutte le altre categorie: form semplificato (solo Lotto + Fornitore + Scadenza)
- **Route GET** `/carico`: popola il select con articoli `TAGLIO` e `VARIO`, raggruppati per `categoria`
- **Route POST** `/salva_carico`: inserisce in `LOTTO_MADRE`, validazione base attuale
- **File di interesse**: `app.py`, `templates/carico.html`, `database.sql`

---

## Requirements

### R1. Form dinamico lato client
Quando l'utente seleziona un prodotto nel `<select>`, il form mostra o nasconde la sezione "Tracciabilità Carne" in base alla `categoria` del prodotto selezionato. Le categorie carne (Bovino, Suino, Avicolo) mostrano i campi: `paese_nascita`, `paese_allevamento`, `paese_macellazione`, `paese_sezionamento`, `data_macellazione`. Le altre categorie mostrano solo i campi base. Il meccanismo è client-side (show/hide CSS) senza ricaricamento pagina. La `categoria` deve essere accessibile al JavaScript (es. come `data-categoria` sulle `<option>`).

### R2. Migrazione DB e aggiornamento INSERT
Aggiungere la colonna `data_macellazione DATE NULL` alla tabella `LOTTO_MADRE`. Fornire sia lo statement SQL di migrazione (`ALTER TABLE`) sia l'aggiornamento del file `database.sql`. Aggiornare la query INSERT in `salva_carico` per includere questa nuova colonna.

### R3. Validazione condizionale backend
La route `/salva_carico` deve leggere la `categoria` dell'articolo selezionato dal DB e applicare validazione condizionale: se la categoria è Bovino, Suino o Avicolo, i campi `paese_nascita`, `paese_allevamento`, `paese_macellazione` e `paese_sezionamento` sono obbligatori e deve essere presente almeno uno tra `data_macellazione` e `data_scadenza`. Per le altre categorie, questi campi rimangono facoltativi. I messaggi di errore flash esistenti devono essere coerenti con la nuova logica.

### R4. UX e coerenza visuale
La sezione "Tracciabilità Carne" deve avere un'intestazione visiva distinta (es. bordo colorato, label specifica) che indichi all'operatore che sta compilando dati HACCP obbligatori. Il comportamento deve essere coerente con lo stile Tailwind CSS già adottato nel progetto.

---

## Acceptance Criteria

### Comportamento frontend
- [ ] Selezionando un articolo di categoria "Bovino", "Suino" o "Avicolo", la sezione tracciabilità carne appare immediatamente senza ricaricamento pagina
- [ ] Selezionando qualsiasi altro articolo (es. "Spezie", "Latticini"), la sezione tracciabilità carne è nascosta e i suoi campi non vengono inviati come required
- [ ] Il form al caricamento iniziale (nessun prodotto selezionato) non mostra la sezione tracciabilità

### Validazione backend
- [ ] POST con categoria carne e campi paese mancanti → flash error, redirect a `/carico`, nessun inserimento in DB
- [ ] POST con categoria carne e tutti i campi compilati → record inserito correttamente in `LOTTO_MADRE` inclusa `data_macellazione`
- [ ] POST con categoria non-carne e campi paese vuoti → record inserito correttamente (campi nullable salvati come NULL)

### Database
- [ ] La colonna `data_macellazione DATE NULL` esiste in `LOTTO_MADRE` dopo la migrazione
- [ ] Il file `database.sql` riflette lo schema aggiornato (utile per setup da zero)

### Integrità codice
- [ ] Nessuna regressione sulle route esistenti (`/magazzino`, `/etichetta`, `/etichetta_taglio`)
- [ ] L'app Flask si avvia senza errori dopo le modifiche

---

*Nota per il team: non creare test framework da zero. Verificare il funzionamento eseguendo l'app Flask localmente (`python app.py`) e testando manualmente le route GET e POST. Il DB di sviluppo è su PostgreSQL configurato via `.env`.*


