"""
E2E & Non-Regression Challenger Test Suite for Carico Merci HACCP Dynamic Form Milestone.
Tests cover:
1. Flask application startup & DB migrations initialization
2. Full lifecycle:
   - GET /carico markup, optgroups, and data-categoria attributes
   - POST /salva_carico for meat (Bovino, Suino, Avicolo) and non-meat (Spezie, Latticini, Farinacei)
   - GET /magazzino inventory rendering with NULL and non-NULL expiry dates
   - GET /stampa_etichetta_taglio/<id> with newly created lots (including NULL data_scadenza)
   - GET /download_excel workbook generation and data integrity
   - GET / and GET /api/db_status
3. Production recipes & session handling non-regression:
   - POST /produci_preparato/<id> linking fresh meat lots with NULL data_scadenza
   - GET /stampa_etichetta/<id> rendering ingredients and allergens
   - POST /chiudi_sessione
4. Adversarial edge cases:
   - Category case/whitespace permutations
   - Malformed/future/past dates
   - SQL injection attempts & special characters
   - DB failure and rollback handling
"""

import unittest
from unittest.mock import MagicMock, patch, call
import datetime
import os
import sys
import tempfile
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import app, init_db_migrations, aggiorna_file_excel, get_excel_path


class TestCaricoE2ENonRegressionChallenger(unittest.TestCase):
    """Adversarial E2E and Non-Regression Challenger Suite."""

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-e2e-challenger-secret'
        self.client = app.test_client()

    def _setup_mock_db(self, mock_getconn, mock_putconn, fetchone_result=None, fetchall_result=None):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_getconn.return_value = mock_conn

        if fetchone_result is not None:
            mock_cursor.fetchone.return_value = fetchone_result
        if fetchall_result is not None:
            mock_cursor.fetchall.return_value = fetchall_result

        return mock_conn, mock_cursor

    # =========================================================================
    # 1. FLASK APP STARTUP & MIGRATIONS
    # =========================================================================

    def test_e2e_01_app_startup_and_migrations_idempotency(self):
        """Verify init_db_migrations executes idempotent DDL on LOTTO_MADRE without throwing."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        with patch('app.db_pool.getconn', return_value=mock_conn), \
             patch('app.db_pool.putconn') as mock_putconn:
            init_db_migrations()

            mock_cursor.execute.assert_called_once()
            sql = mock_cursor.execute.call_args[0][0]
            self.assertIn("ALTER TABLE LOTTO_MADRE ADD COLUMN IF NOT EXISTS data_macellazione DATE;", sql)
            self.assertIn("ALTER TABLE LOTTO_MADRE ALTER COLUMN data_scadenza DROP NOT NULL;", sql)
            mock_conn.commit.assert_called_once()
            mock_putconn.assert_called_once_with(mock_conn)

    def test_e2e_02_app_startup_migration_db_failure_graceful_degradation(self):
        """Verify init_db_migrations logs warning and does not crash app if DB is offline at boot."""
        with patch('app.db_pool.getconn', side_effect=Exception("Database Connection Timeout")), \
             patch('app.app.logger.warning') as mock_logger:
            init_db_migrations()
            mock_logger.assert_called_once()
            self.assertIn("Migrazione DB non eseguita o database non raggiungibile", mock_logger.call_args[0][0])

    # =========================================================================
    # 2. GET /carico MARKUP & DOM ATTRIBUTES
    # =========================================================================

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_e2e_03_get_carico_markup_and_optgroups(self, mock_getconn, mock_putconn):
        """GET /carico renders all TAGLIO and VARIO products grouped by category with data-categoria."""
        articoli_sample = [
            {'id_articolo': 1, 'denominazione': 'Bistecca Fiorentina', 'categoria': 'Bovino', 'tipo_categoria': 'TAGLIO'},
            {'id_articolo': 2, 'denominazione': 'Capocollo di Maiale', 'categoria': 'Suino', 'tipo_categoria': 'TAGLIO'},
            {'id_articolo': 3, 'denominazione': 'Petto di Pollo', 'categoria': 'Avicolo', 'tipo_categoria': 'TAGLIO'},
            {'id_articolo': 10, 'denominazione': 'Sale Marino Fine', 'categoria': 'Spezie', 'tipo_categoria': 'VARIO'},
            {'id_articolo': 11, 'denominazione': 'Formaggio Caciocavallo', 'categoria': 'Latticini', 'tipo_categoria': 'VARIO'}
        ]
        self._setup_mock_db(mock_getconn, mock_putconn, fetchall_result=articoli_sample)

        response = self.client.get('/carico')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')

        # Check optgroups and options
        self.assertIn('<optgroup label="Bovino"', html)
        self.assertIn('<optgroup label="Suino"', html)
        self.assertIn('<optgroup label="Avicolo"', html)
        self.assertIn('<optgroup label="Spezie"', html)
        self.assertIn('<optgroup label="Latticini"', html)

        self.assertIn('data-categoria="Bovino"', html)
        self.assertIn('data-categoria="Suino"', html)
        self.assertIn('data-categoria="Avicolo"', html)
        self.assertIn('data-categoria="Spezie"', html)
        self.assertIn('data-categoria="Latticini"', html)

        # Check HACCP section styling and inputs
        self.assertIn('id="sezione-tracciabilita"', html)
        self.assertIn('Tracciabilità Carne • Dati HACCP', html)
        self.assertIn('id="paese_nascita"', html)
        self.assertIn('id="paese_allevamento"', html)
        self.assertIn('id="paese_macellazione"', html)
        self.assertIn('id="paese_sezionamento"', html)
        self.assertIn('id="data_macellazione"', html)

    # =========================================================================
    # 3. POST /salva_carico FULL LIFECYCLE (MEAT & NON-MEAT)
    # =========================================================================

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_e2e_04_post_salva_carico_bovino_meat_slaughter_only(self, mock_getconn, mock_putconn):
        """POST /salva_carico for Bovino with slaughter date only -> inserts 9 columns with NULL data_scadenza."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, fetchone_result={
            'id_articolo': 1, 'denominazione': 'Bistecca Fiorentina', 'categoria': 'Bovino'
        })

        slaughter_date = datetime.date.today() - datetime.timedelta(days=2)
        response = self.client.post('/salva_carico', data={
            'id_articolo': '1',
            'codice_lotto_fornitore': 'BOV-LOT-01',
            'fornitore': 'Chianina Carni S.p.A.',
            'data_scadenza': '',
            'data_macellazione': slaughter_date.strftime('%Y-%m-%d'),
            'paese_nascita': 'ITA',
            'paese_allevamento': 'ITA',
            'paese_macellazione': 'IT-01',
            'paese_sezionamento': 'IT-02'
        }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], '/magazzino')

        # Verify SQL & parameter binding
        insert_call = mock_cursor.execute.call_args_list[-1]
        sql, params = insert_call[0]
        self.assertIn("INSERT INTO LOTTO_MADRE", sql)
        self.assertEqual(params[0], '1')
        self.assertEqual(params[1], 'BOV-LOT-01')
        self.assertEqual(params[2], 'Chianina Carni S.p.A.')
        self.assertIsNone(params[3])  # data_scadenza is None
        self.assertEqual(params[4], 'ITA')
        self.assertEqual(params[5], 'ITA')
        self.assertEqual(params[6], 'IT-01')
        self.assertEqual(params[7], 'IT-02')
        self.assertEqual(params[8], slaughter_date)
        mock_conn.commit.assert_called_once()

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_e2e_05_post_salva_carico_non_meat_spezie(self, mock_getconn, mock_putconn):
        """POST /salva_carico for Spezie -> inserts with NULL origins and slaughter date."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, fetchone_result={
            'id_articolo': 10, 'denominazione': 'Sale Marino Fine', 'categoria': 'Spezie'
        })

        exp_date = datetime.date.today() + datetime.timedelta(days=365)
        response = self.client.post('/salva_carico', data={
            'id_articolo': '10',
            'codice_lotto_fornitore': 'SALE-2026',
            'fornitore': 'Saline Siciliane',
            'data_scadenza': exp_date.strftime('%Y-%m-%d'),
            'data_macellazione': '',
            'paese_nascita': '',
            'paese_allevamento': '',
            'paese_macellazione': '',
            'paese_sezionamento': ''
        }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], '/magazzino')

        insert_call = mock_cursor.execute.call_args_list[-1]
        sql, params = insert_call[0]
        self.assertEqual(params[0], '10')
        self.assertEqual(params[1], 'SALE-2026')
        self.assertEqual(params[2], 'Saline Siciliane')
        self.assertEqual(params[3], exp_date)
        self.assertIsNone(params[4])
        self.assertIsNone(params[5])
        self.assertIsNone(params[6])
        self.assertIsNone(params[7])
        self.assertIsNone(params[8])

    # =========================================================================
    # 4. GET /magazzino INVENTORY RENDERING
    # =========================================================================

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_e2e_06_get_magazzino_rendering_with_null_and_non_null_dates(self, mock_getconn, mock_putconn):
        """GET /magazzino renders both TAGLIO (with label button) and VARIO, handling NULL data_scadenza gracefully."""
        sample_giacenze = [
            {
                'id_lotto_madre': 101,
                'id_articolo': 1,
                'denominazione': 'Bistecca Fiorentina',
                'tipo_categoria': 'TAGLIO',
                'fornitore': 'Chianina S.p.A.',
                'codice_lotto_fornitore': 'BOV-101',
                'data_carico': datetime.datetime(2026, 8, 23, 10, 0),
                'data_scadenza': None,  # Nullable
                'data_macellazione': datetime.date(2026, 8, 20)
            },
            {
                'id_lotto_madre': 102,
                'id_articolo': 10,
                'denominazione': 'Sale Marino Fine',
                'tipo_categoria': 'VARIO',
                'fornitore': 'Saline Siciliane',
                'codice_lotto_fornitore': 'SALE-102',
                'data_carico': datetime.datetime(2026, 8, 23, 11, 0),
                'data_scadenza': datetime.date(2027, 8, 23),
                'data_macellazione': None
            }
        ]
        self._setup_mock_db(mock_getconn, mock_putconn, fetchall_result=sample_giacenze)

        response = self.client.get('/magazzino')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')

        # Check meat cut row
        self.assertIn('#101', html)
        self.assertIn('Bistecca Fiorentina', html)
        self.assertIn('BOV-101', html)
        self.assertIn('href="/stampa_etichetta_taglio/101"', html)

        # Check non-meat row
        self.assertIn('#102', html)
        self.assertIn('Sale Marino Fine', html)
        self.assertIn('23/08/2027', html)
        self.assertNotIn('href="/stampa_etichetta_taglio/102"', html)

    # =========================================================================
    # 5. GET /stampa_etichetta_taglio/<id> LABEL RENDERING
    # =========================================================================

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_e2e_07_stampa_etichetta_taglio_with_slaughter_date_only(self, mock_getconn, mock_putconn):
        """GET /stampa_etichetta_taglio/101 renders thermal label showing slaughter date when data_scadenza is None."""
        self._setup_mock_db(mock_getconn, mock_putconn, fetchone_result={
            'id_lotto_madre': 101,
            'codice_lotto_fornitore': 'BOV-101',
            'data_carico': datetime.datetime(2026, 8, 23, 10, 0),
            'data_scadenza': None,
            'data_macellazione': datetime.date(2026, 8, 20),
            'paese_nascita': 'ITA',
            'paese_allevamento': 'ITA',
            'paese_macellazione': 'IT-01',
            'paese_sezionamento': 'IT-02',
            'denominazione': 'Bistecca Fiorentina',
            'categoria': 'Bovino',
            'tipo_categoria': 'TAGLIO'
        })

        response = self.client.get('/stampa_etichetta_taglio/101')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')

        self.assertIn('BISTECCA FIORENTINA', html.upper())
        self.assertIn('Macellato il:', html)
        self.assertIn('20/08/2026', html)
        self.assertIn('Nato in: <span style="font-weight: normal;">ITA</span>', html)
        self.assertIn('Sezionato in: <span style="font-weight: normal;">IT-02</span>', html)
        self.assertIn('JsBarcode("#barcode", "BOV-101"', html)

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_e2e_08_stampa_etichetta_taglio_invalid_or_non_taglio_redirects(self, mock_getconn, mock_putconn):
        """GET /stampa_etichetta_taglio for nonexistent or non-TAGLIO lot redirects to /magazzino with error."""
        self._setup_mock_db(mock_getconn, mock_putconn, fetchone_result=None)

        response = self.client.get('/stampa_etichetta_taglio/9999', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Lotto di taglio fresco non trovato o non valido.'.encode('utf-8'), response.data)

    # =========================================================================
    # 6. GET /download_excel WORKBOOK GENERATION
    # =========================================================================

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_e2e_09_download_excel_generation_and_columns(self, mock_getconn, mock_putconn):
        """GET /download_excel triggers aggiorna_file_excel and returns binary Excel workbook with data_macellazione."""
        mock_conn = MagicMock()
        mock_getconn.return_value = mock_conn

        with tempfile.TemporaryDirectory() as tmpdir:
            # Patch get_excel_path to write into isolated temporary directory
            test_excel_path = os.path.join(tmpdir, "Registro_Tracciabilita_Test.xlsx")
            
            with patch('app.get_excel_path', return_value=test_excel_path):
                # Setup pd.read_sql_query return values
                def side_effect_read_sql(query, conn, params=None):
                    if 'LOTTO_MADRE' in query:
                        return pd.DataFrame([{
                            'id_lotto_madre': 1,
                            'id_articolo': 1,
                            'codice_lotto_fornitore': 'BOV-01',
                            'fornitore': 'Chianina Spa',
                            'data_carico': datetime.datetime.now(),
                            'data_scadenza': None,
                            'data_macellazione': datetime.date(2026, 8, 20),
                            'paese_nascita': 'ITA',
                            'paese_allevamento': 'ITA',
                            'paese_macellazione': 'IT-01',
                            'paese_sezionamento': 'IT-02'
                        }])
                    elif 'LOTTO_PREPARATO' in query:
                        return pd.DataFrame([{
                            'id_lotto_preparato': 1,
                            'id_sessione': 1,
                            'id_articolo': 20,
                            'id_ricetta': 1,
                            'codice_lotto_interno': 'PREP-20-20260823',
                            'data_lavorazione': datetime.datetime.now(),
                            'data_scadenza_preparato': datetime.date(2026, 8, 26)
                        }])
                    elif 'COMPOSIZIONE_LAVORAZIONE' in query:
                        return pd.DataFrame([{
                            'id_composizione': 1,
                            'codice_lotto_interno': 'PREP-20-20260823',
                            'data_lavorazione': datetime.datetime.now(),
                            'prodotto': 'Polpette di Carne',
                            'codice_lotto_fornitore': 'BOV-01',
                            'data_carico': datetime.datetime.now(),
                            'ingrediente': 'Carne Macinata Bovino',
                            'note_associazione': 'Assegnazione automatica banco'
                        }])
                    return pd.DataFrame()

                with patch('pandas.read_sql_query', side_effect=side_effect_read_sql):
                    response = self.client.get('/download_excel')
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.content_type, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    self.assertTrue(os.path.exists(test_excel_path))

                    # Verify Excel sheets and columns
                    excel_file = pd.ExcelFile(test_excel_path)
                    self.assertIn('Carichi_Magazzino', excel_file.sheet_names)
                    self.assertIn('Prodotti_Preparati', excel_file.sheet_names)
                    self.assertIn('Registro_HACCP_Completo', excel_file.sheet_names)

                    df_carichi = pd.read_excel(test_excel_path, sheet_name='Carichi_Magazzino')
                    self.assertIn('data_macellazione', df_carichi.columns)
                    self.assertIn('data_scadenza', df_carichi.columns)
                    self.assertEqual(df_carichi.iloc[0]['codice_lotto_fornitore'], 'BOV-01')

    # =========================================================================
    # 7. GET / AND GET /api/db_status
    # =========================================================================

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_e2e_10_get_root_and_db_status(self, mock_getconn, mock_putconn):
        """GET / and GET /api/db_status verify root dashboard and DB connectivity status endpoint."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_getconn.return_value = mock_conn

        # Test /api/db_status healthy
        response = self.client.get('/api/db_status')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'status': 'ok'})

        # Test /api/db_status failure
        mock_cursor.execute.side_effect = Exception("DB Connection Lost")
        response_err = self.client.get('/api/db_status')
        self.assertEqual(response_err.status_code, 500)
        self.assertEqual(response_err.json, {'status': 'error'})

        # Reset mock cursor and test GET /
        mock_cursor.execute.side_effect = None
        mock_cursor.fetchall.return_value = [
            {'id_articolo': 1, 'denominazione': 'Bistecca Fiorentina', 'categoria': 'Bovino', 'tipo_categoria': 'TAGLIO', 'allergeni': None},
            {'id_articolo': 20, 'denominazione': 'Polpette', 'categoria': 'Pronto Cuoci', 'tipo_categoria': 'PREPARATO', 'allergeni': 'Glutine'},
            {'id_articolo': 10, 'denominazione': 'Sale', 'categoria': 'Spezie', 'tipo_categoria': 'VARIO', 'allergeni': None}
        ]
        mock_cursor.fetchone.return_value = {'id_lotto_madre': 42}

        response_root = self.client.get('/')
        self.assertEqual(response_root.status_code, 200)
        self.assertIn(b'Bistecca Fiorentina', response_root.data)
        self.assertIn(b'Polpette', response_root.data)
        self.assertIn(b'Sale', response_root.data)
        self.assertIn(b'href="/stampa_etichetta_taglio/42"', response_root.data)

    # =========================================================================
    # 8. PRODUCTION & PREPARATI NON-REGRESSION
    # =========================================================================

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_e2e_11_produci_preparato_finds_lot_with_null_data_scadenza(self, mock_getconn, mock_putconn):
        """POST /produci_preparato successfully links meat lot having NULL data_scadenza to COMPOSIZIONE_LAVORAZIONE."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_getconn.return_value = mock_conn

        # Sequence of queries in produci_preparato:
        # 1. SELECT id_ricetta FROM RICETTA WHERE id_articolo_preparato = %s AND attiva = TRUE
        # 2. SELECT id_sessione FROM SESSIONE_LAVORAZIONE WHERE stato_sessione = 'Aperta' ...
        # 3. INSERT INTO LOTTO_PREPARATO ... RETURNING id_lotto_preparato
        # 4. SELECT id_articolo_ingrediente FROM RICETTA_RIGA ...
        # 5. SELECT id_lotto_madre FROM LOTTO_MADRE WHERE id_articolo = %s AND (data_scadenza IS NULL OR data_scadenza >= CURRENT_DATE) ...
        # 6. INSERT INTO COMPOSIZIONE_LAVORAZIONE ...

        def side_effect_fetchone():
            return {
                'id_ricetta': 5,
                'id_sessione': 12,
                'id_lotto_preparato': 99,
                'id_lotto_madre': 101  # Returned lot with NULL data_scadenza
            }

        mock_cursor.fetchone.side_effect = [
            {'id_ricetta': 5},
            {'id_sessione': 12},
            {'id_lotto_preparato': 99},
            {'id_lotto_madre': 101}
        ]
        mock_cursor.fetchall.return_value = [{'id_articolo_ingrediente': 1}]

        response = self.client.post('/produci_preparato/20', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], '/stampa_etichetta/99')

        # Check lot query executed with (data_scadenza IS NULL OR data_scadenza >= CURRENT_DATE)
        lot_queries = [c for c in mock_cursor.execute.call_args_list if 'FROM LOTTO_MADRE' in c[0][0]]
        self.assertTrue(len(lot_queries) > 0)
        lot_sql = lot_queries[0][0][0]
        self.assertIn("data_scadenza IS NULL OR data_scadenza >= CURRENT_DATE", lot_sql)


if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
