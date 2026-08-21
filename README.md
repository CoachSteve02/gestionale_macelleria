# Gestionale Macelleria (HACCP)

Sistema di tracciabilità alimentare HACCP e gestione magazzino per macelleria, con export automatico su Excel e stampa etichette termiche.

## Stack tecnologico

- **Backend:** Python 3 / Flask
- **Database:** PostgreSQL
- **Template engine:** Jinja2 (HTML server-side, ottimizzato per touch screen da banco)
- **Export dati:** Pandas + openpyxl (genera `Registro_Tracciabilita_Macelleria.xlsx`)
- **Etichette:** stampa termica via browser, codici a barre generati con JsBarcode

> Nota: questo repository include anche una piccola app React/Vite (`src/`) generata automaticamente da Google AI Studio come ambiente di sviluppo iniziale. **Non è l'applicazione reale**: mostra solo una pagina riassuntiva dell'architettura Flask. L'app vera è quella descritta di seguito.

## Struttura del progetto

```
app.py                     # Backend Flask: tutte le rotte e la logica applicativa
database.sql                # Schema PostgreSQL + dati iniziali (articoli, ricette, ecc.)
templates/
  index.html                 # Vetrina / produzione preparati
  carico.html                 # Form di carico merce
  magazzino.html               # Elenco giacenze lotti
  etichetta.html                 # Etichetta stampabile per i preparati
  etichetta_taglio.html           # Etichetta stampabile per i tagli freschi
```

## Prerequisiti

- Python 3.10+
- PostgreSQL 13+ installato e in esecuzione
- `pip`

## Installazione e avvio locale

1. **Clona il repository e crea un ambiente virtuale (consigliato):**
   ```bash
   python -m venv venv
   source venv/bin/activate   # su Windows: venv\Scripts\activate
   ```

2. **Installa le dipendenze Python:**
   ```bash
   pip install flask psycopg2-binary pandas openpyxl python-dotenv
   ```

3. **Crea il database e inizializza lo schema:**
   ```bash
   createdb gestionale_macelleria_dev
   psql -d gestionale_macelleria_dev -f database.sql
   ```

4. **Configura le variabili d'ambiente** creando un file `.env` nella root del progetto:
   ```
   DATABASE_URL=postgresql://<utente>:<password>@localhost:5432/gestionale_macelleria_dev
   SECRET_KEY=una_chiave_segreta_a_scelta
   ```

5. **Avvia il backend:**
   ```bash
   python app.py
   ```

6. Apri il browser su [http://localhost:5000](http://localhost:5000)

## Funzionalità principali

- **Vetrina/Produzione**: catalogo prodotti diviso in Tagli freschi, Preparati (1-click) e Vari, con ricerca rapida.
- **Carico merce**: registrazione dei lotti fornitore in ingresso, con validazione dei campi obbligatori (Poka-Yoke) e tracciamento del paese di nascita/allevamento/macellazione/sezionamento.
- **Produzione preparati**: un click genera automaticamente il lotto interno, associa i lotti fornitore usati per ogni ingrediente della ricetta (tracciabilità HACCP) e reindirizza alla stampa etichetta.
- **Magazzino**: elenco di tutte le giacenze con stato e azioni rapide.
- **Etichette**: stampa termica con codice a barre, ingredienti in ordine di quantità e allergeni evidenziati.
- **Export Excel automatico**: ad ogni operazione di carico o produzione, viene rigenerato `Registro_Tracciabilita_Macelleria.xlsx` con tre fogli (carichi, preparati, registro HACCP completo).

## Note

- Il file Excel viene sovrascritto interamente ad ogni operazione di scrittura, non aggiornato in modo incrementale.
- L'operatore di sessione è attualmente fisso ("Operatore Banco"); non è presente un sistema di login/autenticazione multi-operatore.