import os
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictCursor
import pandas as pd
from dotenv import load_dotenv
import threading
import tempfile

# Mappa dei mesi in italiano per il nome file
MESI_ITALIANI = {
    1: 'Gennaio',  2: 'Febbraio', 3: 'Marzo',    4: 'Aprile',
    5: 'Maggio',   6: 'Giugno',   7: 'Luglio',   8: 'Agosto',
    9: 'Settembre',10: 'Ottobre', 11: 'Novembre', 12: 'Dicembre'
}
# Lock globale per serializzare eventuali scritture concorrenti sul file Excel
_excel_write_lock = threading.Lock()

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super_secret_key_macelleria') 
#'super_secret_key_macelleria' va impostata in .env per sicurezza questa è una versione valida per la fase di testing
@app.context_processor
def inject_excel_filename():
    """Inietta il nome del file Excel mensile corrente in tutti i template."""
    now = datetime.datetime.now()
    nome_file = f"Registro_Tracciabilita_{MESI_ITALIANI[now.month]}_{now.year}.xlsx"
    return {'excel_filename': nome_file}

# Connection pooling setup
db_pool = SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/gestionale_macelleria_dev')
)

def get_db_connection():
    conn = db_pool.getconn()
    return conn

def get_excel_path(anno: int = None, mese: int = None) -> str:
    """
    Restituisce il percorso assoluto del file Excel mensile HACCP.
    La cartella 'tracciabilità negozio' viene creata automaticamente sul Desktop.
    """
    now = datetime.datetime.now()
    anno = anno or now.year
    mese = mese or now.month
    nome_mese = MESI_ITALIANI[mese]

    # Cartella dedicata sul Desktop dell'utente corrente (Windows e Linux/macOS)
    cartella = os.path.join(
        os.path.expanduser("~"),  # → C:/Users/<utente> su Windows
        "Desktop",
        "tracciabilità negozio"
    )
    os.makedirs(cartella, exist_ok=True)  # crea la cartella se non esiste; no errore se già c'è

    nome_file = f"Registro_Tracciabilita_{nome_mese}_{anno}.xlsx"
    return os.path.join(cartella, nome_file)

def aggiorna_file_excel():
    """
    Genera (o sovrascrive) il registro mensile HACCP per il mese corrente.
    Filtra i dati per mese/anno corrente — non esporta l'intera storia del DB.
    Usa un lock di thread e scrittura atomica su file temporaneo per sicurezza.
    """
    now = datetime.datetime.now()
    anno, mese = now.year, now.month

    # Intervallo [inizio_mese, fine_mese) per filtro TIMESTAMP preciso
    inizio_mese = datetime.datetime(anno, mese, 1)
    fine_mese = (
        datetime.datetime(anno + 1, 1, 1) if mese == 12
        else datetime.datetime(anno, mese + 1, 1)
    )

    query_carichi = """
        SELECT id_lotto_madre, id_articolo, codice_lotto_fornitore, fornitore,
               data_carico, data_scadenza, paese_nascita, paese_allevamento,
               paese_macellazione, paese_sezionamento
        FROM LOTTO_MADRE
        WHERE data_carico >= %s AND data_carico < %s
        ORDER BY data_carico DESC
    """

    query_preparati = """
        SELECT id_lotto_preparato, id_sessione, id_articolo, id_ricetta,
               codice_lotto_interno, data_lavorazione, data_scadenza_preparato
        FROM LOTTO_PREPARATO
        WHERE data_lavorazione >= %s AND data_lavorazione < %s
        ORDER BY data_lavorazione DESC
    """

    query_haccp = """
        SELECT cp.id_composizione, lp.codice_lotto_interno, lp.data_lavorazione,
               a_prep.denominazione AS prodotto, lm.codice_lotto_fornitore,
               lm.data_carico, a_ing.denominazione AS ingrediente, cp.note_associazione
        FROM COMPOSIZIONE_LAVORAZIONE cp
        JOIN LOTTO_PREPARATO lp  ON cp.id_lotto_preparato = lp.id_lotto_preparato
        JOIN ARTICOLO a_prep     ON lp.id_articolo        = a_prep.id_articolo
        JOIN LOTTO_MADRE lm      ON cp.id_lotto_madre     = lm.id_lotto_madre
        JOIN ARTICOLO a_ing      ON lm.id_articolo        = a_ing.id_articolo
        WHERE lp.data_lavorazione >= %s AND lp.data_lavorazione < %s
        ORDER BY lp.data_lavorazione DESC, cp.id_composizione
    """

    percorso_finale = get_excel_path(anno, mese)
    cartella = os.path.dirname(percorso_finale)
    conn = get_db_connection()

    try:
        with _excel_write_lock:
            # 1. Leggi tutti i DataFrame PRIMA di scrivere su disco
            df_carichi   = pd.read_sql_query(query_carichi,   conn, params=(inizio_mese, fine_mese))
            df_preparati = pd.read_sql_query(query_preparati, conn, params=(inizio_mese, fine_mese))
            df_haccp     = pd.read_sql_query(query_haccp,     conn, params=(inizio_mese, fine_mese))

            # 2. Scrivi su file temporaneo (stesso filesystem → os.replace è atomico)
            fd, percorso_tmp = tempfile.mkstemp(dir=cartella, suffix='.xlsx')
            os.close(fd)

            try:
                with pd.ExcelWriter(percorso_tmp, engine='openpyxl') as writer:
                    df_carichi.to_excel(writer,   sheet_name='Carichi_Magazzino',      index=False)
                    df_preparati.to_excel(writer, sheet_name='Prodotti_Preparati',      index=False)
                    df_haccp.to_excel(writer,     sheet_name='Registro_HACCP_Completo', index=False)

                # 3. Rinomina atomica: il file finale viene sostituito solo se la scrittura è riuscita
                os.replace(percorso_tmp, percorso_finale)
                app.logger.info(f"File Excel mensile aggiornato: {percorso_finale}")

            except Exception:
                if os.path.exists(percorso_tmp):
                    os.remove(percorso_tmp)  # pulizia del temporaneo in caso di errore
                raise

    except Exception as e:
        app.logger.error(f"Errore aggiornamento Excel: {e}", exc_info=True)
    finally:
        db_pool.putconn(conn)

@app.route('/download_excel')
def download_excel():
    """
    Genera on-demand e scarica il registro mensile HACCP.
    È la singola fonte di verità per la generazione del file Excel.
    """
    aggiorna_file_excel()  # Genera sempre fresco al momento del download

    percorso = get_excel_path()
    now = datetime.datetime.now()
    nome_download = f"Registro_Tracciabilita_{MESI_ITALIANI[now.month]}_{now.year}.xlsx"

    if not os.path.isfile(percorso):
        flash(
            'Impossibile generare il file Excel. Verificare la connessione al database.',
            'error'
        )
        return redirect(url_for('index'))

    return send_file(percorso, as_attachment=True, download_name=nome_download)
    
@app.route('/')
def index():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM ARTICOLO ORDER BY denominazione;")
            articoli = cursor.fetchall()

            catalogo = {'PREPARATO': [], 'TAGLIO': [], 'VARIO': []}
            for articolo in articoli:
                if articolo['tipo_categoria'] in catalogo:
                    catalogo[articolo['tipo_categoria']].append(articolo)

            # Per ogni taglio, recupera l'ultimo lotto madre caricato (serve per il pulsante di stampa rapida)
            for taglio in catalogo['TAGLIO']:
                cursor.execute("""
                    SELECT id_lotto_madre FROM LOTTO_MADRE
                    WHERE id_articolo = %s
                    ORDER BY data_carico DESC
                    LIMIT 1
                """, (taglio['id_articolo'],))
                ultimo_lotto = cursor.fetchone()
                taglio['id_ultimo_lotto_madre'] = ultimo_lotto['id_lotto_madre'] if ultimo_lotto else None

        return render_template('index.html', catalogo=catalogo)
    finally:
        db_pool.putconn(conn)

@app.route('/carico')
def carico():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM ARTICOLO WHERE tipo_categoria IN ('TAGLIO', 'VARIO') ORDER BY categoria, denominazione;")
            articoli = cursor.fetchall()
            
            # Raggruppa per categoria per optgroup
            articoli_per_categoria = {}
            for art in articoli:
                cat = art['categoria']
                if cat not in articoli_per_categoria:
                    articoli_per_categoria[cat] = []
                articoli_per_categoria[cat].append(art)
                
        return render_template('carico.html', articoli_per_categoria=articoli_per_categoria)
    finally:
        db_pool.putconn(conn)

@app.route('/salva_carico', methods=['POST'])
def salva_carico():
    id_articolo = request.form.get('id_articolo')
    codice_lotto_fornitore = request.form.get('codice_lotto_fornitore')
    fornitore = request.form.get('fornitore')
    data_scadenza = request.form.get('data_scadenza')
    paese_nascita = request.form.get('paese_nascita')
    paese_allevamento = request.form.get('paese_allevamento')
    paese_macellazione = request.form.get('paese_macellazione')
    paese_sezionamento = request.form.get('paese_sezionamento')

    if not all([id_articolo, codice_lotto_fornitore, fornitore, data_scadenza]):
        flash('I campi obbligatori (Prodotto, Lotto, Fornitore, Scadenza) non sono stati compilati.', 'error')
        return redirect(url_for('carico'))

    # Validazione formato e data di scadenza
    try:
        data_scad_parsed = datetime.datetime.strptime(data_scadenza, '%Y-%m-%d').date()
    except ValueError:
        flash('Formato data di scadenza non valido.', 'error')
        return redirect(url_for('carico'))

    if data_scad_parsed < datetime.date.today():
        flash('La data di scadenza non può essere nel passato.', 'error')
        return redirect(url_for('carico'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO LOTTO_MADRE (
                    id_articolo, codice_lotto_fornitore, fornitore, data_scadenza, 
                    paese_nascita, paese_allevamento, paese_macellazione, paese_sezionamento
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                id_articolo, codice_lotto_fornitore, fornitore, data_scad_parsed, 
                paese_nascita, paese_allevamento, paese_macellazione, paese_sezionamento
            ))
        conn.commit()
        flash('Carico merce registrato con successo.', 'success')
        return redirect(url_for('magazzino'))
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Errore salva_carico (id_articolo={id_articolo}): {e}", exc_info=True)
        flash('Errore durante il salvataggio. Controllare i dati inseriti.', 'error')
        return redirect(url_for('carico'))
    finally:
        db_pool.putconn(conn)

@app.route('/magazzino')
def magazzino():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT lm.*, a.denominazione, a.tipo_categoria 
                FROM LOTTO_MADRE lm
                JOIN ARTICOLO a ON lm.id_articolo = a.id_articolo
                ORDER BY lm.data_carico DESC
            """)
            giacenze = cursor.fetchall()
        return render_template('magazzino.html', giacenze=giacenze)
    finally:
        db_pool.putconn(conn)

@app.route('/produci_preparato/<int:id_articolo>', methods=['POST'])
def produci_preparato(id_articolo):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 1. Trova ricetta attiva
            cursor.execute("SELECT id_ricetta FROM RICETTA WHERE id_articolo_preparato = %s AND attiva = TRUE", (id_articolo,))
            ricetta = cursor.fetchone()
            
            if not ricetta:
                flash('Nessuna ricetta attiva trovata per questo preparato.', 'error')
                return redirect(url_for('index'))
                
            id_ricetta = ricetta['id_ricetta']
            
            # 2. Genera codice lotto interno (es: PREP-ID-YYYYMMDDHHMMSS)
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            codice_lotto_interno = f"PREP-{id_articolo}-{timestamp}"
            
            # Calcolo scadenza (es. +3 giorni per i preparati freschi)
            scadenza = datetime.datetime.now().date() + datetime.timedelta(days=3)
            
            # 3. Creazione o recupero sessione lavorazione
            cursor.execute("SELECT id_sessione FROM SESSIONE_LAVORAZIONE WHERE stato_sessione = 'Aperta' ORDER BY data_ora_inizio DESC LIMIT 1")
            sessione_attiva = cursor.fetchone()
            
            if sessione_attiva:
                id_sessione = sessione_attiva['id_sessione']
            else:
                cursor.execute("INSERT INTO SESSIONE_LAVORAZIONE (operatore) VALUES ('Operatore Banco') RETURNING id_sessione")
                id_sessione = cursor.fetchone()['id_sessione']
            
            # 4. Inserimento in LOTTO_PREPARATO
            cursor.execute("""
                INSERT INTO LOTTO_PREPARATO (id_sessione, id_articolo, id_ricetta, codice_lotto_interno, data_scadenza_preparato)
                VALUES (%s, %s, %s, %s, %s) RETURNING id_lotto_preparato
            """, (id_sessione, id_articolo, id_ricetta, codice_lotto_interno, scadenza))
            id_lotto_preparato = cursor.fetchone()['id_lotto_preparato']
            
            # 5. Trova ingredienti per la ricetta
            cursor.execute("SELECT id_articolo_ingrediente FROM RICETTA_RIGA WHERE id_ricetta = %s", (id_ricetta,))
            ingredienti = cursor.fetchall()
            
            # 6. Associa i lotti madre per ciascun ingrediente (Tracciabilità)
            for ing in ingredienti:
                id_ing = ing['id_articolo_ingrediente']
                
                # Cerca lotto madre: prima quelli del giorno, poi i più recenti caricati in generale
                cursor.execute("""
                    SELECT id_lotto_madre FROM LOTTO_MADRE 
                    WHERE id_articolo = %s AND data_scadenza >= CURRENT_DATE
                    ORDER BY data_carico DESC LIMIT 1
                """, (id_ing,))
                lotto_madre = cursor.fetchone()
                
                if lotto_madre:
                    cursor.execute("""
                        INSERT INTO COMPOSIZIONE_LAVORAZIONE (id_lotto_preparato, id_lotto_madre, note_associazione)
                        VALUES (%s, %s, %s)
                    """, (id_lotto_preparato, lotto_madre['id_lotto_madre'], "Assegnazione automatica banco"))
                else:
                    # Registra tracciabilità mancante se l'ingrediente manca dal magazzino
                    app.logger.warning(f"Lotto madre mancante per l'ingrediente ID {id_ing} nel preparato {id_lotto_preparato}")
                    cursor.execute("""
                        INSERT INTO COMPOSIZIONE_LAVORAZIONE (id_lotto_preparato, id_lotto_madre, note_associazione)
                        VALUES (%s, NULL, %s)
                    """, (id_lotto_preparato, f"Allerta HACCP: lotto mancante per ingrediente {id_ing}"))
            
            conn.commit()
            flash(f'Preparato prodotto con successo. Lotto: {codice_lotto_interno}', 'success')
            return redirect(url_for('stampa_etichetta', id_lotto_preparato=id_lotto_preparato))
            
    except Exception as e:
        conn.rollback()
        flash(f"Errore durante la produzione: {e}", 'error')
        return redirect(url_for('index'))
    finally:
        db_pool.putconn(conn)

@app.route('/stampa_etichetta/<int:id_lotto_preparato>')
def stampa_etichetta(id_lotto_preparato):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Recupera dati preparato
            cursor.execute("""
                SELECT lp.id_lotto_preparato, lp.codice_lotto_interno, lp.data_lavorazione, lp.data_scadenza_preparato, a.denominazione
                FROM LOTTO_PREPARATO lp
                JOIN ARTICOLO a ON lp.id_articolo = a.id_articolo
                WHERE lp.id_lotto_preparato = %s
            """, (id_lotto_preparato,))
            preparato = cursor.fetchone()
            
            if not preparato:
                flash('Lotto non trovato.', 'error')
                return redirect(url_for('index'))
                
            # Recupera ingredienti e allergeni dalla vista
            cursor.execute("""
                SELECT ingrediente, allergeni 
                FROM VW_ETICHETTA_PREPARATO 
                WHERE id_lotto_preparato = %s
                ORDER BY ordine_etichetta
            """, (id_lotto_preparato,))
            ingredienti = cursor.fetchall()
            
            # Formatta ingredienti e aggrega allergeni
            lista_ingredienti = []
            allergeni_set = set()
            for ing in ingredienti:
                lista_ingredienti.append(ing['ingrediente'])
                if ing['allergeni']:
                    for al in ing['allergeni'].split(','):
                        allergeni_set.add(al.strip().upper())
            
        return render_template('etichetta.html', 
                               preparato=preparato, 
                               ingredienti=", ".join(lista_ingredienti),
                               allergeni=list(allergeni_set))
    finally:
        db_pool.putconn(conn)

@app.route('/stampa_etichetta_taglio/<int:id_lotto_madre>')
def stampa_etichetta_taglio(id_lotto_madre):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Recupera dati lotto di origine (taglio)
            cursor.execute("""
                SELECT 
                    lm.id_lotto_madre, lm.codice_lotto_fornitore, lm.data_carico, lm.data_scadenza,
                    lm.paese_nascita, lm.paese_allevamento, lm.paese_macellazione, lm.paese_sezionamento,
                    a.denominazione, a.categoria, a.tipo_categoria
                FROM LOTTO_MADRE lm
                JOIN ARTICOLO a ON lm.id_articolo = a.id_articolo
                WHERE lm.id_lotto_madre = %s AND a.tipo_categoria = 'TAGLIO'
            """, (id_lotto_madre,))
            taglio = cursor.fetchone()

            if not taglio:
                flash('Lotto di taglio fresco non trovato o non valido.', 'error')
                return redirect(url_for('magazzino'))

            # Controllo conformità HACCP per tagli bovini: i 4 campi origine sono obbligatori
            if taglio['categoria'] == 'Bovino':
                campi_obbligatori = {
                    'Nato in': taglio['paese_nascita'],
                    'Allevato in': taglio['paese_allevamento'],
                    'Macellato in': taglio['paese_macellazione'],
                    'Sezionato in': taglio['paese_sezionamento'],
                }
                mancanti = [nome for nome, valore in campi_obbligatori.items() if not valore]
                if mancanti:
                    flash(
                        f"Dati di tracciabilità mancanti per questo lotto bovino: {', '.join(mancanti)}. "
                        "Impossibile stampare l'etichetta. Completare i dati in Carico Merce.",
                        'error'
                    )
                    return redirect(url_for('magazzino'))

        return render_template('etichetta_taglio.html', taglio=taglio)
    finally:
        db_pool.putconn(conn)
        
@app.route('/chiudi_sessione', methods=['POST'])
def chiudi_sessione():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE SESSIONE_LAVORAZIONE 
                SET data_fine = CURRENT_TIMESTAMP,
                    stato_sessione = 'Chiusa'
                WHERE stato_sessione = 'Aperta';
            """)
            righe_aggiornate = cursor.rowcount  # numero di sessioni effettivamente chiuse

        conn.commit()

        if righe_aggiornate == 0:
            # Nessuna sessione era aperta (doppio click, o nessuna produzione del giorno)
            flash('Nessuna sessione attiva da chiudere.', 'warning')
        else:
            flash(f'Sessione chiusa con successo ({righe_aggiornate} sessione/i).', 'success')

    except Exception as e:
        conn.rollback()
        app.logger.error(f"Errore chiusura sessione: {e}", exc_info=True)
        flash('Errore durante la chiusura della sessione.', 'error')
    finally:
        db_pool.putconn(conn)
        
    return redirect(url_for('index'))

@app.route('/api/db_status')
def db_status():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1;")
        return jsonify({"status": "ok"})
    except Exception:
        return jsonify({"status": "error"}), 500
    finally:
        if conn:
            db_pool.putconn(conn)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)
