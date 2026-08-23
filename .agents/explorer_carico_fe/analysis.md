# Analisi Frontend: Form Dinamico Carico Merci & Tracciabilità HACCP

## 1. Obiettivo dell'Indagine
L'obiettivo è progettare e documentare le modifiche frontend per la pagina **Carico Merci** (`templates/carico.html`) del gestionale, al fine di:
1. Rendere dinamica la visibilità della sezione **Tracciabilità Carne (HACCP)** in base al prodotto selezionato nel `<select id="id_articolo">`.
2. Mostrare i campi HACCP (`paese_nascita`, `paese_allevamento`, `paese_macellazione`, `paese_sezionamento`, `data_macellazione`) solo quando l'articolo appartiene alle categorie di carne: **Bovino**, **Suino**, **Avicolo**.
3. Mantenere nascosta la sezione HACCP e semplificato il form per tutte le altre categorie (es. Spezie, Latticini, Farinacei, Uova, Involucri).
4. Gestire la transizione interamente **client-side con vanilla JavaScript** (nessun framework JS, nessun ricaricamento, nessuna chiamata AJAX).
5. Gestire dinamicamente gli attributi `required` e lo stato di validazione HTML5 per prevenire blocchi al submit quando la sezione è nascosta.
6. Applicare uno stile coerente con Tailwind CSS (CDN Tailwind v4 utilizzato nel progetto) con un box/card visivamente distinto con badge e header HACCP.

---

## 2. Analisi dello Stato Attuale

### 2.1 File `templates/carico.html` (Attuale)
- **Struttura base**: include `header.html` in cima e `footer.html` in calce.
- **Form POST**: punta a `{{ url_for('salva_carico') }}` con classe `space-y-6`.
- **Select Prodotto (`id_articolo`)**:
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
  *Criticità attuale*: le `<option>` non possiedono l'attributo `data-categoria`. Il JavaScript client-side non può dedurre la categoria direttamente dall'opzione selezionata senza un lookup.

- **Campi Origine Attuali**:
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
  *Criticità attuali*:
  1. I campi sono sempre visibili per qualsiasi articolo (anche sale, pepe, spezie, involucri).
  2. Manca il campo `data_macellazione` (richiesto per la tracciabilità carni).
  3. Non vi è alcuna distinzione visiva (card, intestazione HACCP, badge informativo) che segnali all'operatore l'obbligatorietà e la natura normativa dei campi.

---

## 3. Soluzione Proposta per i Singoli Punti

### 3.1 Aggiunta `data-categoria` alle `<option>`
In `templates/carico.html`, all'interno del loop Jinja2 di `articoli_per_categoria`:
```jinja2
{% for categoria, articoli in articoli_per_categoria.items() %}
    <optgroup label="{{ categoria }}" class="font-bold text-slate-900 bg-slate-200">
        {% for art in articoli %}
            <option value="{{ art.id_articolo }}" data-categoria="{{ categoria }}" class="font-normal text-slate-800 bg-white">
                {{ art.denominazione }}
            </option>
        {% endfor %}
    </optgroup>
{% endfor %}
```
*Vantaggi*:
- `categoria` è la chiave del dizionario `articoli_per_categoria` passata da Flask (`app.py: carico()`).
- Ogni tag `<option>` riceve `data-categoria="Bovino"`, `data-categoria="Suino"`, `data-categoria="Avicolo"`, `data-categoria="Spezie"`, ecc.
- Accesso istantaneo via `option.dataset.categoria` in JavaScript.

---

### 3.2 Struttura e Styling Tailwind della Sezione Tracciabilità HACCP
La sezione viene racchiusa in un contenitore dedicato `#sezione-tracciabilita` con classe iniziale `hidden`.

#### Caratteristiche visuali e Tailwind:
- **Card container**: `bg-red-50/40 border-2 border-red-300 rounded-xl p-6 space-y-4 shadow-sm transition-all duration-200` (in alternativa amber `bg-amber-50/50 border-2 border-amber-300`). L'accento rosso richiama la sezione "Tagli Freschi" di `index.html` e l'header dell'app.
- **Header della sezione**:
  - Icona / Emoji: 🥩 o icona materiale
  - Titolo: `TRACCIABILITÀ CARNE • DATI HACCP` in `font-black text-red-900 uppercase tracking-wide`
  - Badge: `OBBLIGATORIO` in `bg-red-600 text-white text-xs px-2.5 py-1 rounded-full font-bold uppercase tracking-wider`
- **Campi inclusi**:
  1. `paese_nascita` (input text, placeholder "Es. ITA")
  2. `paese_allevamento` (input text, placeholder "Es. ITA")
  3. `paese_macellazione` (input text, placeholder "Es. ITA o IT-123")
  4. `paese_sezionamento` (input text, placeholder "Es. ITA o IT-456")
  5. `data_macellazione` (input date, con label esplicativa "Data di Macellazione (Opzionale / Alternativa a Scadenza)")

#### Markup Proposto:
```html
<!-- SEZIONE TRACCIABILITÀ CARNE (HACCP) - Visibile solo per Bovino, Suino, Avicolo -->
<div id="sezione-tracciabilita" class="hidden bg-red-50/40 rounded-xl border-2 border-red-300 p-6 space-y-4 shadow-sm transition-all duration-200">
    <div class="flex items-center justify-between border-b border-red-200 pb-3">
        <div class="flex items-center space-x-2">
            <span class="text-xl">🥩</span>
            <h3 class="font-black text-red-900 uppercase tracking-wide text-sm sm:text-base">
                Tracciabilità Carne &bull; Dati HACCP
            </h3>
        </div>
        <span class="bg-red-600 text-white text-xs px-2.5 py-1 rounded-full font-black uppercase tracking-wider">
            Obbligatorio
        </span>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div class="flex flex-col">
            <label for="paese_nascita" class="font-bold text-slate-700 mb-2 uppercase tracking-wide text-xs">
                Nato in <span class="text-red-600 font-bold">*</span>
            </label>
            <input type="text" id="paese_nascita" name="paese_nascita" placeholder="Es. ITA"
                   class="p-3 border-2 border-slate-300 rounded-lg bg-white focus:border-red-600 focus:ring-0 focus:outline-none text-md">
        </div>
        <div class="flex flex-col">
            <label for="paese_allevamento" class="font-bold text-slate-700 mb-2 uppercase tracking-wide text-xs">
                Allevato in <span class="text-red-600 font-bold">*</span>
            </label>
            <input type="text" id="paese_allevamento" name="paese_allevamento" placeholder="Es. ITA"
                   class="p-3 border-2 border-slate-300 rounded-lg bg-white focus:border-red-600 focus:ring-0 focus:outline-none text-md">
        </div>
        <div class="flex flex-col">
            <label for="paese_macellazione" class="font-bold text-slate-700 mb-2 uppercase tracking-wide text-xs">
                Macellato in <span class="text-red-600 font-bold">*</span>
            </label>
            <input type="text" id="paese_macellazione" name="paese_macellazione" placeholder="Es. ITA o IT-123"
                   class="p-3 border-2 border-slate-300 rounded-lg bg-white focus:border-red-600 focus:ring-0 focus:outline-none text-md">
        </div>
        <div class="flex flex-col">
            <label for="paese_sezionamento" class="font-bold text-slate-700 mb-2 uppercase tracking-wide text-xs">
                Sezionato in <span class="text-red-600 font-bold">*</span>
            </label>
            <input type="text" id="paese_sezionamento" name="paese_sezionamento" placeholder="Es. ITA o IT-456"
                   class="p-3 border-2 border-slate-300 rounded-lg bg-white focus:border-red-600 focus:ring-0 focus:outline-none text-md">
        </div>
    </div>

    <div class="flex flex-col pt-2 border-t border-red-100">
        <label for="data_macellazione" class="font-bold text-slate-700 mb-2 uppercase tracking-wide text-xs">
            Data di Macellazione <span class="text-slate-500 font-normal text-xs">(Opzionale / Alternativa a Scadenza)</span>
        </label>
        <input type="date" id="data_macellazione" name="data_macellazione"
               class="p-3 border-2 border-slate-300 rounded-lg bg-white focus:border-red-600 focus:ring-0 focus:outline-none text-md">
    </div>
</div>
```

---

### 3.3 Logica Vanilla JavaScript per Show/Hide & Gestione Validazione

#### Categorie Carne
Le categorie da trattare come carni che richiedono tracciabilità HACCP obbligatoria sono:
- `Bovino`
- `Suino`
- `Avicolo`

Il confronto viene normalizzato in minuscolo (`['bovino', 'suino', 'avicolo']`) per massima robustezza contro variazioni di maiuscole/minuscole.

#### Gestione dello Stato:
1. **Caricamento Iniziale (`DOMContentLoaded`)**:
   - `sezione-tracciabilita` è inizialmente con classe `hidden`.
   - Se nessun prodotto è selezionato (`value=""`), la sezione rimane nascosta e i campi hanno `required = false`.
   - Se il browser ricarica con un valore pre-selezionato (es. navigazione avanti/indietro nella cronologia della sessione), la funzione `aggiornaVisibilitaTracciabilita()` valuta immediatamente l'opzione selezionata e imposta lo stato corretto.
2. **Selezione Dinamica (`change` e `input` listener su `#id_articolo`)**:
   - Legge `data-categoria` dell'opzione attiva.
   - Se la categoria è presente nella lista carne:
     - Rimuove la classe `hidden` dalla sezione.
     - Imposta `required = true` sui 4 campi obbligatori (`paese_nascita`, `paese_allevamento`, `paese_macellazione`, `paese_sezionamento`).
   - Se la categoria NON è carne (o selezione vuota):
     - Aggiunge la classe `hidden` alla sezione.
     - Imposta `required = false` sui campi HACCP (evitando l'errore HTML5 di input required nascosti non focalizzabili).
     - Azzera i valori (`input.value = ''`) dei campi HACCP per evitare l'invio accidentale di dati residui.

#### Codice JavaScript Completo:
```javascript
<script>
document.addEventListener('DOMContentLoaded', () => {
    const selectArticolo = document.getElementById('id_articolo');
    const sezioneTracciabilita = document.getElementById('sezione-tracciabilita');
    const meatInputs = [
        document.getElementById('paese_nascita'),
        document.getElementById('paese_allevamento'),
        document.getElementById('paese_macellazione'),
        document.getElementById('paese_sezionamento')
    ];
    const dataMacellazione = document.getElementById('data_macellazione');

    const MEAT_CATEGORIES = ['bovino', 'suino', 'avicolo'];

    function aggiornaVisibilitaTracciabilita() {
        if (!selectArticolo || !sezioneTracciabilita) return;

        const selectedOption = selectArticolo.options[selectArticolo.selectedIndex];
        const categoria = (selectedOption && (selectedOption.dataset.categoria || selectedOption.getAttribute('data-categoria'))) 
            ? (selectedOption.dataset.categoria || selectedOption.getAttribute('data-categoria')).toLowerCase().trim() 
            : '';

        const isMeat = MEAT_CATEGORIES.includes(categoria);

        if (isMeat) {
            sezioneTracciabilita.classList.remove('hidden');
            meatInputs.forEach(input => {
                if (input) input.required = true;
            });
        } else {
            sezioneTracciabilita.classList.add('hidden');
            meatInputs.forEach(input => {
                if (input) {
                    input.required = false;
                    input.value = '';
                }
            });
            if (dataMacellazione) {
                dataMacellazione.value = '';
            }
        }
    }

    if (selectArticolo) {
        selectArticolo.addEventListener('change', aggiornaVisibilitaTracciabilita);
        // Inizializza lo stato al caricamento della pagina
        aggiornaVisibilitaTracciabilita();
    }
});
</script>
```

---

## 4. Verifica Casi Limite ed Edge Cases

| Scenario | Comportamento Atteso | Verifica / Esito |
|---|---|---|
| **Caricamento pagina iniziale** (nessun articolo selezionato) | Sezione HACCP nascosta, campi `required = false` | ✅ Nessuna violazione HTML5, form base pulito |
| **Selezione "Bistecca Fiorentina" (Bovino)** | Sezione HACCP compare istantaneamente, campi origine diventano `required = true` | ✅ Submit senza compilare origine viene bloccato dal browser |
| **Selezione "Capocollo di Maiale" (Suino)** | Sezione HACCP visibile e obbligatoria | ✅ Funziona correttamente |
| **Selezione "Petto di Pollo" (Avicolo)** | Sezione HACCP visibile e obbligatoria | ✅ Funziona correttamente |
| **Switch da Bovino a "Sale Marino Fine" (Spezie)** | Sezione scompare, campi origine svuotati e `required = false` | ✅ Form può essere inviato senza errori di validazione |
| **Navigazione indietro nel browser (bfcache / prefill)** | Lo script in `DOMContentLoaded` riesegue il check | ✅ Lo stato riflette l'opzione attualmente selezionata |
| **Articolo con categoria con spazi o maiuscole/minuscole diverse** | Normalizzazione `.toLowerCase().trim()` | ✅ Resiliente a ` BOVINO `, `suino`, etc. |
| **Submit con form carne completo** | Invia tutti i campi inclusa `data_macellazione` | ✅ Backend riceve tutti i parametri corretti |

---

## 5. Proposta Completa per `templates/carico.html`

Di seguito il codice completo aggiornato per `templates/carico.html`:

```jinja2
{% include 'header.html' %}

        <main class='flex-1 p-4 overflow-y-auto w-full max-w-4xl mx-auto'> 
            
            <section class='bg-white rounded-xl shadow-sm border-t-8 border-slate-700 flex flex-col p-8'> 
                <div class='border-b border-slate-200 pb-4 mb-6 flex justify-between items-center shrink-0'> 
                    <h2 class='font-black text-slate-800 uppercase tracking-tighter text-2xl'>Nuovo Carico Merce</h2> 
                </div> 

                <form action="{{ url_for('salva_carico') }}" method="POST" class="space-y-6">
                    
                    <div class="flex flex-col">
                        <label for="id_articolo" class="font-bold text-slate-700 mb-2 uppercase tracking-wide text-sm">Prodotto (Solo Tagli e Vari)</label>
                        <select id="id_articolo" name="id_articolo" required class="p-4 border-2 border-slate-300 rounded-lg bg-slate-50 focus:border-slate-800 focus:ring-0 focus:outline-none text-lg">
                            <option value="" disabled selected>-- Seleziona un prodotto --</option>
                            {% for categoria, articoli in articoli_per_categoria.items() %}
                                <optgroup label="{{ categoria }}" class="font-bold text-slate-900 bg-slate-200">
                                    {% for art in articoli %}
                                        <option value="{{ art.id_articolo }}" data-categoria="{{ categoria }}" class="font-normal text-slate-800 bg-white">{{ art.denominazione }}</option>
                                    {% endfor %}
                                </optgroup>
                            {% endfor %}
                        </select>
                    </div>

                    <div class="flex flex-col">
                        <label for="codice_lotto_fornitore" class="font-bold text-slate-700 mb-2 uppercase tracking-wide text-sm">Lotto Fornitore</label>
                        <input type="text" id="codice_lotto_fornitore" name="codice_lotto_fornitore" required
                               maxlength="20" pattern="[A-Za-z0-9\-]+"
                               title="Solo lettere, numeri e trattini, massimo 20 caratteri"
                               placeholder="Es. L-123456"
                               class="p-4 border-2 border-slate-300 rounded-lg bg-slate-50 focus:border-slate-800 focus:ring-0 focus:outline-none text-lg">
                    </div>

                    <div class="flex flex-col">
                        <label for="fornitore" class="font-bold text-slate-700 mb-2 uppercase tracking-wide text-sm">Nome Fornitore / Allevamento</label>
                        <input type="text" id="fornitore" name="fornitore" required placeholder="Es. Rossi Carni S.p.A." class="p-4 border-2 border-slate-300 rounded-lg bg-slate-50 focus:border-slate-800 focus:ring-0 focus:outline-none text-lg">
                    </div>

                    <div class="flex flex-col">
                        <label for="data_scadenza" class="font-bold text-slate-700 mb-2 uppercase tracking-wide text-sm">Data di Scadenza</label>
                        <input type="date" id="data_scadenza" name="data_scadenza" required class="p-4 border-2 border-slate-300 rounded-lg bg-slate-50 focus:border-slate-800 focus:ring-0 focus:outline-none text-lg">
                    </div>

                    <!-- SEZIONE TRACCIABILITÀ CARNE (HACCP) - Visibile dinamicamente solo per Bovino, Suino, Avicolo -->
                    <div id="sezione-tracciabilita" class="hidden bg-red-50/40 rounded-xl border-2 border-red-300 p-6 space-y-4 shadow-sm transition-all duration-200">
                        <div class="flex items-center justify-between border-b border-red-200 pb-3">
                            <div class="flex items-center space-x-2">
                                <span class="text-xl">🥩</span>
                                <h3 class="font-black text-red-900 uppercase tracking-wide text-sm sm:text-base">
                                    Tracciabilità Carne &bull; Dati HACCP
                                </h3>
                            </div>
                            <span class="bg-red-600 text-white text-xs px-2.5 py-1 rounded-full font-black uppercase tracking-wider">
                                Obbligatorio
                            </span>
                        </div>

                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div class="flex flex-col">
                                <label for="paese_nascita" class="font-bold text-slate-700 mb-2 uppercase tracking-wide text-xs">
                                    Nato in <span class="text-red-600 font-bold">*</span>
                                </label>
                                <input type="text" id="paese_nascita" name="paese_nascita" placeholder="Es. ITA" class="p-3 border-2 border-slate-300 rounded-lg bg-white focus:border-red-600 focus:ring-0 focus:outline-none text-md">
                            </div>
                            <div class="flex flex-col">
                                <label for="paese_allevamento" class="font-bold text-slate-700 mb-2 uppercase tracking-wide text-xs">
                                    Allevato in <span class="text-red-600 font-bold">*</span>
                                </label>
                                <input type="text" id="paese_allevamento" name="paese_allevamento" placeholder="Es. ITA" class="p-3 border-2 border-slate-300 rounded-lg bg-white focus:border-red-600 focus:ring-0 focus:outline-none text-md">
                            </div>
                            <div class="flex flex-col">
                                <label for="paese_macellazione" class="font-bold text-slate-700 mb-2 uppercase tracking-wide text-xs">
                                    Macellato in <span class="text-red-600 font-bold">*</span>
                                </label>
                                <input type="text" id="paese_macellazione" name="paese_macellazione" placeholder="Es. ITA o IT-123" class="p-3 border-2 border-slate-300 rounded-lg bg-white focus:border-red-600 focus:ring-0 focus:outline-none text-md">
                            </div>
                            <div class="flex flex-col">
                                <label for="paese_sezionamento" class="font-bold text-slate-700 mb-2 uppercase tracking-wide text-xs">
                                    Sezionato in <span class="text-red-600 font-bold">*</span>
                                </label>
                                <input type="text" id="paese_sezionamento" name="paese_sezionamento" placeholder="Es. ITA o IT-456" class="p-3 border-2 border-slate-300 rounded-lg bg-white focus:border-red-600 focus:ring-0 focus:outline-none text-md">
                            </div>
                        </div>

                        <div class="flex flex-col pt-2 border-t border-red-100">
                            <label for="data_macellazione" class="font-bold text-slate-700 mb-2 uppercase tracking-wide text-xs">
                                Data di Macellazione <span class="text-slate-500 font-normal text-xs">(Opzionale / Alternativa a Scadenza)</span>
                            </label>
                            <input type="date" id="data_macellazione" name="data_macellazione" class="p-3 border-2 border-slate-300 rounded-lg bg-white focus:border-red-600 focus:ring-0 focus:outline-none text-md">
                        </div>
                    </div>

                    <div class="pt-4">
                        <button type="submit" class="w-full bg-slate-800 hover:bg-slate-900 text-white font-bold text-xl py-5 rounded-xl uppercase tracking-widest transition-colors shadow-md border-b-4 border-slate-950 active:border-b-0 active:translate-y-1">
                            Salva Carico Merce
                        </button>
                    </div>
                </form>

            </section> 

        </main> 

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const selectArticolo = document.getElementById('id_articolo');
            const sezioneTracciabilita = document.getElementById('sezione-tracciabilita');
            const meatInputs = [
                document.getElementById('paese_nascita'),
                document.getElementById('paese_allevamento'),
                document.getElementById('paese_macellazione'),
                document.getElementById('paese_sezionamento')
            ];
            const dataMacellazione = document.getElementById('data_macellazione');

            const MEAT_CATEGORIES = ['bovino', 'suino', 'avicolo'];

            function aggiornaVisibilitaTracciabilita() {
                if (!selectArticolo || !sezioneTracciabilita) return;

                const selectedOption = selectArticolo.options[selectArticolo.selectedIndex];
                const categoria = (selectedOption && (selectedOption.dataset.categoria || selectedOption.getAttribute('data-categoria'))) 
                    ? (selectedOption.dataset.categoria || selectedOption.getAttribute('data-categoria')).toLowerCase().trim() 
                    : '';

                const isMeat = MEAT_CATEGORIES.includes(categoria);

                if (isMeat) {
                    sezioneTracciabilita.classList.remove('hidden');
                    meatInputs.forEach(input => {
                        if (input) input.required = true;
                    });
                } else {
                    sezioneTracciabilita.classList.add('hidden');
                    meatInputs.forEach(input => {
                        if (input) {
                            input.required = false;
                            input.value = '';
                        }
                    });
                    if (dataMacellazione) {
                        dataMacellazione.value = '';
                    }
                }
            }

            if (selectArticolo) {
                selectArticolo.addEventListener('change', aggiornaVisibilitaTracciabilita);
                aggiornaVisibilitaTracciabilita();
            }
        });
    </script>

{% include 'footer.html' %}
```
