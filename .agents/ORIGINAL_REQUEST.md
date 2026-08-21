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
