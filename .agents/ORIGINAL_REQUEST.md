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

