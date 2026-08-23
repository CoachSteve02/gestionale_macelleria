# Handoff Report: Frontend Dynamic Form Carico Merci (HACCP)

## 1. Observation
1. **`templates/carico.html` (Lines 14-23)**:
   ```jinja2
   <select id="id_articolo" name="id_articolo" required class="p-4 border-2 border-slate-300 rounded-lg bg-slate-50 focus:border-slate-800 focus:ring-0 focus:outline-none text-lg">
       <option value="" disabled selected>-- Seleziona un prodotto --</option>
       {% for categoria, articoli in articoli_per_categoria.items() %}
           <optgroup label="{{ categoria }}" class="font-bold text-slate-900 bg-slate-200">
               {% for art in articoli %}
                   <option value="{{ art.id_articolo }}" class="font-normal text-slate-800 bg-white">{{ art.denominazione }}</option>
               {% endfor %}
           </optgroup>
       {% endfor %}
   </select>
   ```
   *Osservazione*: Le opzioni `<option>` non possiedono attributi per la categoria (`data-categoria`). La categoria è tuttavia disponibile nel ciclo Jinja2 come chiave `categoria` del dizionario `articoli_per_categoria` (e in `art.categoria`).

2. **`templates/carico.html` (Lines 45-62)**:
   ```html
   <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
       <div class="flex flex-col">
           <label for="paese_nascita" ...>Nato in</label>
           <input type="text" id="paese_nascita" name="paese_nascita" placeholder="Es. ITA" ...>
       </div>
       <div class="flex flex-col">
           <label for="paese_allevamento" ...>Allevato in</label>
           <input type="text" id="paese_allevamento" name="paese_allevamento" placeholder="Es. ITA" ...>
       </div>
       <div class="flex flex-col">
           <label for="paese_macellazione" ...>Macellato in</label>
           <input type="text" id="paese_macellazione" name="paese_macellazione" placeholder="Es. ITA o IT-123" ...>
       </div>
       <div class="flex flex-col">
           <label for="paese_sezionamento" ...>Sezionato in</label>
           <input type="text" id="paese_sezionamento" name="paese_sezionamento" placeholder="Es. ITA o IT-456" ...>
       </div>
   </div>
   ```
   *Osservazione*:
   - I 4 campi di origine non sono racchiusi in una card visivamente identificabile.
   - Non esiste il campo `data_macellazione`.
   - Sono sempre visibili indistintamente sia per i tagli di carne sia per articoli vari come il sale o il pepe.

3. **`templates/header.html` (Line 7)**:
   Carica Tailwind CSS via CDN `@tailwindcss/browser@4`. Non vi sono framework come React o Vue sul frontend dell'applicazione; tutti i comportamenti interattivi utilizzano vanilla JavaScript (es. barra di ricerca in `templates/footer.html:21-39` e sincronizzazione in `static/js/status_monitor.js`).

4. **Requisiti di Dominio (`ORIGINAL_REQUEST.md`)**:
   - Categorie carne con tracciabilità obbligatoria: **Bovino**, **Suino**, **Avicolo**.
   - Tutte le altre categorie: form semplificato con sezione HACCP nascosta.
   - Funzionamento 100% client-side senza ricaricamento pagina né chiamate AJAX.

---

## 2. Logic Chain
1. **Identificazione Categoria lato Client**:
   - Aggiungendo `data-categoria="{{ categoria }}"` ad ogni tag `<option>` nel template Jinja2, l'informazione sulla categoria dell'articolo è incorporata nel DOM al rendering iniziale.
   - All'evento di selezione (`change` su `#id_articolo`), il JavaScript legge `select.options[select.selectedIndex].dataset.categoria` in tempo $O(1)$ senza necessità di chiamate di rete.

2. **Dinamica di Visibilità e Stile HACCP**:
   - La sezione di tracciabilità viene inserita in un contenitore `#sezione-tracciabilita` con classe iniziale `hidden`.
   - Il contenitore riceve uno stile Tailwind coerente con la palette del progetto: bordo e sfondo rosso/ambra (`bg-red-50/40 border-2 border-red-300 rounded-xl p-6`), icona 🥩, intestazione chiara `TRACCIABILITÀ CARNE • DATI HACCP` e badge visivo `OBBLIGATORIO`.
   - All'interno del contenitore sono disposti in griglia i 4 campi paese (`paese_nascita`, `paese_allevamento`, `paese_macellazione`, `paese_sezionamento`) e il nuovo campo data (`data_macellazione`).

3. **Gestione della Validazione e Sicurezza Client-Side**:
   - In HTML5, se un elemento `<input>` con attributo `required` si trova all'interno di un genitore con `display: none` (`hidden`), l'invio del form genera un errore di validazione bloccante ("An invalid form control is not focusable").
   - Quando la categoria selezionata è **Bovino**, **Suino** o **Avicolo**:
     - Viene rimossa la classe `hidden` da `#sezione-tracciabilita`.
     - Viene impostato programmaticamente `required = true` sui campi paese (`paese_nascita`, `paese_allevamento`, `paese_macellazione`, `paese_sezionamento`).
   - Quando la categoria selezionata **NON è carne** (o selezione vuota):
     - Viene aggiunta la classe `hidden` a `#sezione-tracciabilita`.
     - Viene impostato `required = false` sui campi paese.
     - I valori dei campi (`value = ''`) vengono resettati per evitare invii spuri al backend.
   - All'avvio (`DOMContentLoaded`), la funzione di aggiornamento viene eseguita una prima volta per gestire correttamente sia lo stato iniziale (nessuna selezione) sia eventuali ripristini da cache del browser.

---

## 3. Caveats
- **Validazione Client vs Backend**: La validazione JavaScript e gli attributi HTML5 `required` offrono un feedback immediato all'operatore (UX), ma il backend (`salva_carico` in `app.py`) deve comunque applicare la validazione server-side interrogando la tabella `ARTICOLO` dal DB, come richiesto in R3.
- **Formato Categorie**: Il controllo JavaScript normalizza la stringa della categoria con `.toLowerCase().trim()` per gestire in modo trasparente variazioni minime di casing, purché i valori di base rimangano "Bovino", "Suino", "Avicolo".
- **Browser Scripting**: Nel raro caso di JavaScript disabilitato nel browser, il form manterrà la classe `hidden` statica. Dato che l'applicazione è un gestionale web interno per uso banco/cassa con browser moderno (come confermato dall'uso di Tailwind Browser CDN), vanilla JS è pienamente supportato.

---

## 4. Conclusion
Il piano di intervento frontend è completamente definito e pronto per l'implementazione:
1. Modificare `templates/carico.html` aggiungendo `data-categoria="{{ categoria }}"` alle `<option>`.
2. Sostituire la griglia dei paesi esistente con la card `#sezione-tracciabilita` completa di header HACCP, badge, campi paese e input `data_macellazione`.
3. Includere in `templates/carico.html` il blocco `<script>` con la logica vanilla JS per il toggle reattivo della visibilità e degli attributi `required`.

Il codice proposto in `analysis.md` rispetta al 100% i requisiti R1, R4 e tutti gli Acceptance Criteria frontend.

---

## 5. Verification Method
Per verificare in modo indipendente le modifiche proposte:
1. **Ispezione Visiva del DOM**:
   - Aprire la pagina `/carico` nel browser.
   - Ispezionare il `<select id="id_articolo">` e verificare che ogni `<option>` abbia l'attributo `data-categoria="NomeCategoria"`.
2. **Test di Comportamento Funzionale**:
   - Al caricamento: la sezione `#sezione-tracciabilita` deve essere invisibile (`display: none` / classe `hidden`).
   - Selezionare "Carne Macinata Bovino" o "Bistecca Fiorentina" (Bovino): la card rossa HACCP compare immediatamente senza flash o ricaricamento.
   - Tentare il submit lasciando i campi paese vuoti: il browser blocca l'invio indicando che i campi paese sono obbligatori.
   - Selezionare "Sale Marino Fine" (Spezie): la card scompare immediatamente, i campi paese vengono svuotati.
   - Compilare i campi base (Lotto Fornitore, Fornitore, Scadenza) e cliccare "Salva Carico Merce": il form viene inviato con successo senza errori di validazione sui campi nascosti.
3. **Invalidation Conditions**:
   - Se selezionando una carne la sezione non appare -> verificare il matching di `data-categoria`.
   - Se il submit di un articolo vario fallisce per input non focalizzabile -> verificare la rimozione di `required` quando la sezione è `hidden`.
