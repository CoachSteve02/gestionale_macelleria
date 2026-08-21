# Indagine Architetturale Frontend & Template (Dead Code Analysis)

**Progetto:** Gestionale Macelleria (HACCP)  
**Data Analisi:** 2026-08-20  
**Autore:** Explorer Subagent (Frontend & Template Architecture)  
**Stato:** Completato — Sola Lettura (Nessun file modificato)

---

## 1. Executive Summary

L'analisi dell'architettura frontend e delle risorse statiche del repository **Gestionale Macelleria** ha rivelato una chiara separazione tra l'**applicazione reale di produzione** (interamente basata su **Python/Flask, Jinja2, PostgreSQL e Vanilla JS**) e un **artefatto di scaffolding React/Vite** (`src/`, `package.json`, `tsconfig.json`, `vite.config.ts`) generato come ambiente di avvio iniziale da Google AI Studio ma completamente disconnesso ed inerte.

Tutti i **7 template HTML** presenti in `templates/` e l'unico script in `static/js/status_monitor.js` sono **attivi e correttamente collegati** agli endpoint Flask. Tuttavia, sono state identificate diverse anomalie minori a livello di template (variabili Jinja impostate ma non consumate, barra di ricerca visibile su pagine prive di elementi filtrabili) e una rilevante quantità di **codice morto e dipendenze fantasma** nel layer Node.js/React.

---

## 2. Architettura Frontend: Confronto dei Due Layer

```
┌────────────────────────────────────────────────────────────────────────────┐
│                       GESTIONALE MACELLERIA REPOSITORY                     │
└─────────────────────────────────────┬──────────────────────────────────────┘
                                      │
        ┌─────────────────────────────┴─────────────────────────────┐
        ▼                                                           ▼
┌───────────────────────────────┐           ┌───────────────────────────────┐
│     PRODUZIONE REALE          │           │   ARTEFATTO SCAFFOLDING       │
│  (Flask + Jinja2 + JS)        │           │    (React 19 + Vite 6)        │
├───────────────────────────────┤           ├───────────────────────────────┤
│ • templates/ (7 file)         │           │ • src/ (3 file: App, main,    │
│ • static/js/status_monitor.js │           │   index.css)                  │
│ • CDN Tailwind v4 & JsBarcode │           │ • package.json                │
│ • Connesso a DB PostgreSQL    │           │ • vite.config.ts              │
│ • Stato: 100% OPERATIVO       │           │ • tsconfig.json               │
│                               │           │ • metadata.json               │
│                               │           │ • Stato: MORTO / DISCONNESSO  │
│                               │           │   (Nessun index.html root,    │
│                               │           │    non servito da Flask)      │
└───────────────────────────────┘           └───────────────────────────────┘
```

---

## 3. Mappatura Dettagliata Template Jinja2 (`templates/`)

Tutti i file `.html` presenti nella directory `templates/` sono stati analizzati ed incrociati con le definizioni delle rotte in `app.py`.

### 3.1 Inventario e Matrice di Rendering

| File Template | Render Point (Python / Jinja) | Endpoint Flask / Metodo | Variabili di Contesto Iniettate | Variabili Effettivamente Usate | Stato |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `templates/index.html` | `app.py:191` (`render_template`) | `GET /` (`index`) | `catalogo` (dict: TAGLIO, PREPARATO, VARIO), `excel_filename` (context processor) | `catalogo`, `excel_filename` (in footer) | **Attivo** |
| `templates/carico.html` | `app.py:211` (`render_template`) | `GET /carico` (`carico`) | `articoli_per_categoria`, `excel_filename` | `articoli_per_categoria`, `excel_filename` | **Attivo** (con variabili Jinja inutilizzate) |
| `templates/magazzino.html` | `app.py:276` (`render_template`) | `GET /magazzino` (`magazzino`) | `giacenze`, `excel_filename` | `giacenze`, `excel_filename` | **Attivo** (con variabili Jinja inutilizzate) |
| `templates/etichetta.html` | `app.py:385` (`render_template`) | `GET /stampa_etichetta/<id>` (`stampa_etichetta`) | `preparato`, `ingredienti`, `allergeni` | `preparato`, `ingredienti`, `allergeni` | **Attivo** |
| `templates/etichetta_taglio.html` | `app.py:430` (`render_template`) | `GET /stampa_etichetta_taglio/<id>` (`stampa_etichetta_taglio`) | `taglio` | `taglio` | **Attivo** |
| `templates/header.html` | Incluso via `{% include %}` | N/A (Index, Carico, Magazzino) | `request.endpoint`, flashed messages | `request.endpoint`, `get_flashed_messages()` | **Attivo** (Incluso in 3 template) |
| `templates/footer.html` | Incluso via `{% include %}` | N/A (Index, Carico, Magazzino) | `excel_filename` | `excel_filename` | **Attivo** (Incluso in 3 template) |

### 3.2 Analisi Dettagliata per Singolo Template

#### A. `templates/index.html` (77 righe)
- **Scopo:** Dashboard principale touch screen (Vetrina banco e produzione preparati 1-click).
- **Inclusioni:** `{% include 'header.html' %}` (linea 1), `{% include 'footer.html' %}` (linea 77).
- **Sezioni:**
  1. *Tagli Freschi* (righe 6–31): Itera `catalogo.TAGLIO`. Se presente `id_ultimo_lotto_madre` (calcolato in `app.py:182-189`), espone il link di stampa etichetta rapida `url_for('stampa_etichetta_taglio', id_lotto_madre=item.id_ultimo_lotto_madre)`.
  2. *Preparati (1-Click)* (righe 34–49): Itera `catalogo.PREPARATO`. Form POST verso `url_for('produci_preparato', id_articolo=item.id_articolo)`.
  3. *Vari / Ingredienti* (righe 52–73): Itera `catalogo.VARIO`, evidenzia la presenza di allergeni.
- **Supporto Ricerca:** Ogni card include la classe `.product-item` e l'attributo `data-name="{{ item.denominazione | lower | e }}"`, filtrato dallo script in `footer.html`.

#### B. `templates/carico.html` (78 righe)
- **Scopo:** Form di registrazione lotti fornitore in ingresso (Poka-Yoke).
- **Inclusioni:** `{% include 'header.html' %}` (linea 4), `{% include 'footer.html' %}` (linea 78).
- **Form Action:** POST verso `url_for('salva_carico')`.
- **Campi gestiti:** `id_articolo`, `codice_lotto_fornitore`, `fornitore`, `data_scadenza`, `paese_nascita`, `paese_allevamento`, `paese_macellazione`, `paese_sezionamento`.
- **Anomalie Jinja identificate:**
  - `righe 1-3`:
    ```jinja2
    {% set active_page = 'carico' %}
    {% set show_search = false %}
    {% set page_title = 'Carico Merce - Gestionale Macelleria' %}
    ```
    Queste 3 variabili locali vengono dichiarate ma **mai utilizzate**:
    - `active_page` è ignorata perché `header.html` determina la classe attiva tramite `request.endpoint == 'carico'` (header.html:41).
    - `show_search` è ignorata perché `header.html` renderizza la barra di ricerca in modo incondizionato (header.html:66-69).
    - `page_title` è ignorata perché `header.html` hardcoda `<title>Gestionale Macelleria</title>` (header.html:6).

#### C. `templates/magazzino.html` (65 righe)
- **Scopo:** Visualizzazione tabellare delle giacenze dei lotti madre con filtro stato e azione di ristampa etichetta per tagli freschi.
- **Inclusioni:** `{% include 'header.html' %}` (linea 4), `{% include 'footer.html' %}` (linea 62).
- **Tabella:** Itera `giacenze`, mostra fornitore, codice lotto, data carico, data scadenza. Se `tipo_categoria == 'TAGLIO'`, genera link a `stampa_etichetta_taglio`.
- **Anomalie Jinja identificate:**
  - `righe 1-3`:
    ```jinja2
    {% set active_page = 'magazzino' %}
    {% set show_search = false %}  {# o true, a seconda del contenuto #}
    {% set page_title = 'Magazzino - Gestionale Macelleria' %}
    ```
    Stesse variabili orfane di `carico.html`. Inoltre le righe della tabella in `magazzino.html` non possiedono la classe `.product-item`, rendendo la barra di ricerca inefficace in questa vista.

#### D. `templates/etichetta.html` (189 righe)
- **Scopo:** Layout di stampa termica (72mm/80mm) per preparati (es. Hamburger, Polpette).
- **Struttura:** Standalone (non include header/footer).
- **Librerie esterne:** JsBarcode 3.11.5 da CDN (`https://cdn.jsdelivr.net/npm/jsbarcode@3.11.5/dist/JsBarcode.all.min.js`).
- **Funzionalità:** Genera codice a barre CODE128 per `preparato.codice_lotto_interno`, formatta la lista ingredienti e il box allergeni in grassetto, attiva la stampa automatica `window.print()` dopo 500ms dal caricamento. Include pulsante di ritorno a `/`.

#### E. `templates/etichetta_taglio.html` (204 righe)
- **Scopo:** Layout di stampa termica per tagli freschi (tracciabilità obbligatoria carni bovine: Nato, Allevato, Macellato, Sezionato).
- **Struttura:** Standalone.
- **Librerie esterne:** JsBarcode 3.11.5 da CDN.
- **Funzionalità:** Genera codice a barre CODE128 per `taglio.codice_lotto_fornitore`. Attende il caricamento dei font tramite `document.fonts.ready` prima di invocare `window.print()`, e reindirizza automaticamente a `/magazzino` tramite `window.onafterprint` (righe 198–200). Include pulsante di ritorno a `/magazzino`.

#### F. `templates/header.html` (70 righe)
- **Scopo:** Componente comune di intestazione, navigazione tab e messaggistica flash.
- **Risorse CDN:**
  - Tailwind CSS Browser compiler: `https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4` (linea 7)
  - Google Fonts (Material Symbols Outlined): `https://fonts.googleapis.com/css2?...` (linea 8)
- **Navigazione:** 3 tab verso `url_for('index')`, `url_for('carico')`, `url_for('magazzino')`.
- **Search Bar:** Input `#searchInput` presente alle righe 66–69.

#### G. `templates/footer.html` (42 righe)
- **Scopo:** Componente comune di piè di pagina, pulsante download Excel, chiusura sessione e logiche JS di ricerca e monitoraggio DB.
- **Elementi:**
  - Indicatore di stato DB (`#db-status-dot`, `#db-status-text`).
  - Link per download file Excel mensile: `url_for('download_excel')` con binding dinamico su `{{ excel_filename }}`.
  - Form POST per chiusura sessione di lavorazione: `url_for('chiudi_sessione')`.
  - Script inline per ricerca client-side (righe 21–39): filtra elementi con selettore `.product-item` confrontando l'attributo `data-name`.
  - Inclusione script esterno: `<script src="{{ url_for('static', filename='js/status_monitor.js') }}" defer></script>` (linea 40).

---

## 4. Risorse Statiche e Script Client-Side (`static/`)

### 4.1 Script `static/js/status_monitor.js` (30 righe)
- **Scopo:** Monitoraggio asincrono dello stato di connessione al database PostgreSQL.
- **Implementazione:**
  - Esegue una chiamata `fetch('/api/db_status')` al caricamento (`DOMContentLoaded`) e poi ogni 30.000 ms (`setInterval`).
  - In caso di successo (`response.ok`), colora il dot di verde (`bg-green-500 animate-pulse`) e imposta il testo `SINCRO DB: ATTIVA`.
  - In caso di errore o rifiuto della promessa (catch), colora il dot di rosso (`bg-red-500`) e imposta `SINCRO DB: OFFLINE`.
- **Integrazione:** Incluso in `templates/footer.html` linea 40.
- **Endpoint Backend:** Corrisponde alla rotta Flask `@app.route('/api/db_status')` in `app.py:464-476`.
- **Valutazione:** **Attivo e perfettamente funzionante.**

### 4.2 Risorse Statiche Esterne (CDN)
Non ci sono file CSS o immagini locali salvati in `static/`. Tutta la grafica è gestita tramite CDN:
1. `@tailwindcss/browser@4` (CDN jsDelivr)
2. `Material Symbols Outlined` (Google Fonts CDN)
3. `JsBarcode.all.min.js` (CDN jsDelivr)

---

## 5. Analisi Scaffolding React/Vite e Node.js (`src/`, `package.json`, etc.)

Come confermato da `README.md` (riga 13), l'intero stack React/TypeScript è un residuo dello scaffold iniziale di Google AI Studio.

### 5.1 Inventario File React in `src/`

| File | Righe | Descrizione / Contenuto | Utilizzo nel Gestionale |
| :--- | :--- | :--- | :--- |
| `src/main.tsx` | 11 | Entry point React: renderizza `<App />` nell'elemento `#root` con `createRoot`. | **Inutilizzato / Morto** |
| `src/App.tsx` | 83 | Componente React che mostra una card statica riassuntiva ("Architettura Python/Flask completata con successo!"). | **Inutilizzato / Morto** |
| `src/index.css` | 2 | Direttiva `@import "tailwindcss";`. | **Inutilizzato / Morto** |

### 5.2 Assenza del File `index.html` Root per Vite
Nella root del repository **non è presente alcun `index.html` standard per Vite** (che contenga `<div id="root"></div>` e `<script type="module" src="/src/main.tsx"></script>`). L'unico `index.html` nel progetto si trova in `templates/index.html` ed è un template Jinja2 con tag Flask non parsabili da Vite. Di conseguenza, l'esecuzione di comandi Vite (`npm run dev` o `npm run build`) non troverebbe il file HTML di ingresso atteso nella root.

### 5.3 Configurazione Bundler e Tipizzazione
- `vite.config.ts` (23 righe): Configura i plugin `@vitejs/plugin-react` e `@tailwindcss/vite`, insieme a logiche HMR specifiche per AI Studio. Non utilizzato in produzione.
- `tsconfig.json` (27 righe): Configurazione TypeScript per JSX React. Non utilizzato in produzione.
- `metadata.json` (7 righe): Configurazione metadati per AI Studio.

---

## 6. Analisi Dipendenze Node.js (`package.json`)

Analizzando `package.json` emergono numerose dipendenze orfane mai importate né nel backend né nel frontend React:

| Pacchetto | Tipo | Versione | Utilizzo nel Codice | Diagnosi |
| :--- | :--- | :--- | :--- | :--- |
| `@google/genai` | dependency | `^2.4.0` | **0 occorrenze** in tutto il repository. | **Dipendenza Morta** |
| `express` | dependency | `^4.21.2` | **0 occorrenze** (il backend è Flask in Python). | **Dipendenza Morta** |
| `@types/express` | devDependency | `^4.17.21` | **0 occorrenze**. | **Dipendenza Morta** |
| `dotenv` (npm) | dependency | `^17.2.3` | **0 occorrenze** nei file JS/TS (il backend usa `python-dotenv`). | **Dipendenza Morta** |
| `tsx` | devDependency | `^4.21.0` | **0 occorrenze** (nessuno script TS da eseguire su Node). | **Dipendenza Morta** |
| `lucide-react` | dependency | `^0.546.0` | Usato solo in `src/App.tsx` (card descrittiva). | Morto se `src/` viene rimosso |
| `motion` | dependency | `^12.23.24` | Usato solo in `src/App.tsx`. | Morto se `src/` viene rimosso |
| `react` / `react-dom` | dependency | `^19.0.1` | Usato solo in `src/main.tsx` e `src/App.tsx`. | Morto se `src/` viene rimosso |
| `@tailwindcss/vite` | dependency | `^4.1.14` | Configurato in `vite.config.ts`. | Morto se `src/` viene rimosso |
| `@vitejs/plugin-react`| dependency | `^5.0.4` | Configurato in `vite.config.ts`. | Morto se `src/` viene rimosso |
| `vite` | dependency / dev | `^6.2.3` | Bundler non impiegato a runtime. | Morto se `src/` viene rimosso |
| `autoprefixer` | devDependency | `^10.4.21` | Ridondante con Tailwind v4. | Morto |

### 6.1 Script NPM con Riferimenti a File Inesistenti
Nel `package.json`:
- `"clean": "rm -rf dist server.js"` (riga 10): fa riferimento a `server.js`, file **inesistente** nel repository.

---

## 7. Catalogo Completo Codice Morto & Inconsistenze (Dead Code Findings)

Di seguito la tabella riassuntiva di tutti gli elementi identificati come inutilizzati, orfani o ridondanti per la revisione manuale:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                             CATALOGO CODICE MORTO - FRONTEND & TEMPLATE                         │
├────┬─────────────────────────────┬─────────────┬──────────────────┬─────────────────────────────┤
│ ID │ File / Elemento             │ Posizione   │ Categoria        │ Giustificazione             │
├────┼─────────────────────────────┼─────────────┼──────────────────┼─────────────────────────────┤
│ F1 │ src/App.tsx                 │ File intero │ React / UI       │ Mockup statico esplicativo; │
│    │                             │ (83 righe)  │                  │ non servito da Flask.       │
├────┼─────────────────────────────┼─────────────┼──────────────────┼─────────────────────────────┤
│ F2 │ src/main.tsx                │ File intero │ React / Mount    │ Entry point React non       │
│    │                             │ (11 righe)  │                  │ collegato ad alcun HTML.    │
├────┼─────────────────────────────┼─────────────┼──────────────────┼─────────────────────────────┤
│ F3 │ src/index.css               │ File intero │ Stili React      │ CSS Tailwind v4 non servito │
│    │                             │ (2 righe)   │                  │ (HTML usa CDN Tailwind).    │
├────┼─────────────────────────────┼─────────────┼──────────────────┼─────────────────────────────┤
│ F4 │ vite.config.ts              │ File intero │ Config Bundler   │ Configurazione Vite per app │
│    │                             │ (23 righe)  │                  │ React inattiva.             │
├────┼─────────────────────────────┼─────────────┼──────────────────┼─────────────────────────────┤
│ F5 │ tsconfig.json               │ File intero │ Config TS        │ Configurazione TS per React │
│    │                             │ (27 righe)  │                  │ non impiegata in prod.      │
├────┼─────────────────────────────┼─────────────┼──────────────────┼─────────────────────────────┤
│ F6 │ metadata.json               │ File intero │ Metadata         │ Configurazione AI Studio    │
│    │                             │ (7 righe)   │                  │ non usata dall'app Flask.   │
├────┼─────────────────────────────┼─────────────┼──────────────────┼─────────────────────────────┤
│ F7 │ package.json: @google/genai │ Riga 14     │ Dipendenza Node  │ Pacchetto installato ma mai │
│    │                             │             │                  │ importato in nessun file.   │
├────┼─────────────────────────────┼─────────────┼──────────────────┼─────────────────────────────┤
│ F8 │ package.json: express       │ Righe 21,33 │ Dipendenza Node  │ Modulo express e @types     │
│    │                             │             │                  │ mai importati (app è Flask).│
├────┼─────────────────────────────┼─────────────┼──────────────────┼─────────────────────────────┤
│ F9 │ package.json: dotenv        │ Riga 22     │ Dipendenza Node  │ Pacchetto Node mai usato    │
│    │                             │             │                  │ (Python usa python-dotenv). │
├────┼─────────────────────────────┼─────────────┼──────────────────┼─────────────────────────────┤
│ F10│ package.json: script clean  │ Riga 10     │ Script npm       │ Riferimento a server.js     │
│    │                             │             │                  │ che non esiste sul disco.   │
├────┼─────────────────────────────┼─────────────┼──────────────────┼─────────────────────────────┤
│ F11│ templates/carico.html       │ Righe 1–3   │ Variabili Jinja  │ `active_page`, `show_search`│
│    │                             │             │ orfane           │ e `page_title` non lette da │
│    │                             │             │                  │ `header.html`.              │
├────┼─────────────────────────────┼─────────────┼──────────────────┼─────────────────────────────┤
│ F12│ templates/magazzino.html    │ Righe 1–3   │ Variabili Jinja  │ `active_page`, `show_search`│
│    │                             │             │ orfane           │ e `page_title` non lette da │
│    │                             │             │                  │ `header.html`.              │
├────┼─────────────────────────────┼─────────────┼──────────────────┼─────────────────────────────┤
│ F13│ templates/header.html       │ Righe 66–69 │ UI disconnessa   │ Barra di ricerca visibile   │
│    │ (su /carico e /magazzino)   │             │                  │ su pagine senza elementi    │
│    │                             │             │                  │ filtrabili (.product-item). │
└────┴─────────────────────────────┴─────────────┴──────────────────┴─────────────────────────────┘
```

---

## 8. Raccomandazioni per la Pulizia (Actionable Plan)

Qualora il team decida di eseguire un refactoring di pulizia (senza alterare la logica applicativa):

1. **Pulizia Variabili Jinja (`carico.html` e `magazzino.html`):**
   - Rimuovere le direttive `{% set active_page = ... %}`, `{% set show_search = ... %}` e `{% set page_title = ... %}` oppure aggiornare `header.html` per supportare dinamicamente `<title>{{ page_title | default('Gestionale Macelleria') }}</title>` e rendere condizionale la barra di ricerca (`{% if show_search is not defined or show_search %}`).
2. **Ottimizzazione UI Barra di Ricerca (`header.html`):**
   - Mostrare la barra di ricerca solo quando `request.endpoint == 'index'` (dove sono effettivamente presenti i prodotti da filtrare).
3. **Valutazione Rimozione Scaffolding Node/React:**
   - Se il progetto è distribuito come applicazione puramente Python/Flask, valutare l'eliminazione dell'intera cartella `src/`, `vite.config.ts`, `tsconfig.json`, `metadata.json` e `package.json` (oppure la loro archiviazione), riducendo la complessità del repository e azzerando le dipendenze npm non necessarie.
