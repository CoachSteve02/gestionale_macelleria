"""
Comprehensive Stress & Boundary Test Suite for Carico Merci Dynamic HACCP Form.
Empirical validation of all edge cases, date boundaries, category permutations,
string sanitization, SQL transaction rollback, and non-regression behaviors.
"""

import unittest
from unittest.mock import MagicMock, patch
import datetime
import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import app, init_db_migrations


class TestCaricoStressAndBoundary(unittest.TestCase):
    """Exhaustive boundary, stress, and edge-case test suite for /salva_carico and related routes."""

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-stress-secret'
        self.client = app.test_client()

    def _setup_mock_db(self, mock_getconn, mock_putconn, articolo_row=None):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_getconn.return_value = mock_conn
        
        if articolo_row is not None:
            mock_cursor.fetchone.return_value = articolo_row
            
        return mock_conn, mock_cursor

    # =========================================================================
    # CATEGORY 1: MEAT ARTICLES - COUNTRY FIELD PERMUTATIONS (0, 1, 2, 3, 4)
    # =========================================================================

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_tc_str_01_meat_missing_all_4_countries(self, mock_getconn, mock_putconn):
        """TC-STR-01: Meat article (Bovino) with 0 country fields -> rejected with flash error."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 1, 'denominazione': 'Carne Macinata Bovino', 'categoria': 'Bovino'
        })

        response = self.client.post('/salva_carico', data={
            'id_articolo': '1',
            'codice_lotto_fornitore': 'L-100',
            'fornitore': 'Fornitore Carni',
            'data_scadenza': (datetime.date.today() + datetime.timedelta(days=10)).strftime('%Y-%m-%d'),
            'paese_nascita': '',
            'paese_allevamento': '',
            'paese_macellazione': '',
            'paese_sezionamento': ''
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Per le categorie carni (Bovino, Suino, Avicolo) tutti i campi di origine'.encode('utf-8'), response.data)
        # Verify no insert executed on mock_cursor
        insert_calls = [c for c in mock_cursor.execute.call_args_list if 'INSERT INTO LOTTO_MADRE' in c[0][0]]
        self.assertEqual(len(insert_calls), 0)

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_tc_str_02_meat_missing_1_country_sezionamento(self, mock_getconn, mock_putconn):
        """TC-STR-02: Meat article (Suino) missing 1 country (paese_sezionamento) -> rejected."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 2, 'denominazione': 'Capocollo di Maiale', 'categoria': 'Suino'
        })

        response = self.client.post('/salva_carico', data={
            'id_articolo': '2',
            'codice_lotto_fornitore': 'L-101',
            'fornitore': 'Fornitore Suino',
            'data_scadenza': (datetime.date.today() + datetime.timedelta(days=10)).strftime('%Y-%m-%d'),
            'paese_nascita': 'ITA',
            'paese_allevamento': 'ITA',
            'paese_macellazione': 'ITA',
            'paese_sezionamento': ''
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Per le categorie carni (Bovino, Suino, Avicolo) tutti i campi di origine'.encode('utf-8'), response.data)

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_tc_str_03_meat_missing_2_countries_macellazione_sezionamento(self, mock_getconn, mock_putconn):
        """TC-STR-03: Meat article (Avicolo) missing 2 countries -> rejected."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 3, 'denominazione': 'Petto di Pollo', 'categoria': 'Avicolo'
        })

        response = self.client.post('/salva_carico', data={
            'id_articolo': '3',
            'codice_lotto_fornitore': 'L-102',
            'fornitore': 'Avicola Nazionale',
            'data_scadenza': (datetime.date.today() + datetime.timedelta(days=5)).strftime('%Y-%m-%d'),
            'paese_nascita': 'ITA',
            'paese_allevamento': 'ITA',
            'paese_macellazione': '',
            'paese_sezionamento': ''
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Per le categorie carni (Bovino, Suino, Avicolo) tutti i campi di origine'.encode('utf-8'), response.data)

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_tc_str_04_meat_missing_3_countries_only_nascita(self, mock_getconn, mock_putconn):
        """TC-STR-04: Meat article (Bovino) with only 1 country (missing 3) -> rejected."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 1, 'denominazione': 'Carne Macinata Bovino', 'categoria': 'Bovino'
        })

        response = self.client.post('/salva_carico', data={
            'id_articolo': '1',
            'codice_lotto_fornitore': 'L-103',
            'fornitore': 'Fornitore Bovino',
            'data_scadenza': (datetime.date.today() + datetime.timedelta(days=5)).strftime('%Y-%m-%d'),
            'paese_nascita': 'ITA',
            'paese_allevamento': '',
            'paese_macellazione': '',
            'paese_sezionamento': ''
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Per le categorie carni (Bovino, Suino, Avicolo) tutti i campi di origine'.encode('utf-8'), response.data)

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_tc_str_05_meat_whitespace_only_country_fields(self, mock_getconn, mock_putconn):
        """TC-STR-05: Meat article with whitespace-only country strings -> stripped and rejected."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 1, 'denominazione': 'Carne Macinata Bovino', 'categoria': 'Bovino'
        })

        response = self.client.post('/salva_carico', data={
            'id_articolo': '1',
            'codice_lotto_fornitore': 'L-104',
            'fornitore': 'Fornitore Bovino',
            'data_scadenza': (datetime.date.today() + datetime.timedelta(days=5)).strftime('%Y-%m-%d'),
            'paese_nascita': '   ',
            'paese_allevamento': '\t',
            'paese_macellazione': '  \n  ',
            'paese_sezionamento': 'ITA'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Per le categorie carni (Bovino, Suino, Avicolo) tutti i campi di origine'.encode('utf-8'), response.data)

    # =========================================================================
    # CATEGORY 2: MEAT ARTICLES - DATE COMBINATIONS (NONE, SLAUGHTER ONLY, EXP ONLY, BOTH)
    # =========================================================================

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_tc_str_06_meat_missing_both_dates(self, mock_getconn, mock_putconn):
        """TC-STR-06: Meat article with all 4 countries but no dates at all -> rejected."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 1, 'denominazione': 'Bistecca Fiorentina', 'categoria': 'Bovino'
        })

        response = self.client.post('/salva_carico', data={
            'id_articolo': '1',
            'codice_lotto_fornitore': 'L-105',
            'fornitore': 'Fornitore Chianina',
            'data_scadenza': '',
            'data_macellazione': '',
            'paese_nascita': 'ITA',
            'paese_allevamento': 'ITA',
            'paese_macellazione': 'ITA',
            'paese_sezionamento': 'ITA'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Per le categorie carni è obbligatorio inserire almeno una data tra Data Macellazione e Data Scadenza.'.encode('utf-8'), response.data)

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_tc_str_07_meat_with_slaughter_date_only_success(self, mock_getconn, mock_putconn):
        """TC-STR-07: Meat with valid 4 countries and slaughter date only (no expiration) -> success."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 1, 'denominazione': 'Bistecca Fiorentina', 'categoria': 'Bovino'
        })

        slaughter_date = datetime.date.today() - datetime.timedelta(days=3)
        response = self.client.post('/salva_carico', data={
            'id_articolo': '1',
            'codice_lotto_fornitore': 'L-106',
            'fornitore': 'Chianina Alta Qualita',
            'data_scadenza': '',
            'data_macellazione': slaughter_date.strftime('%Y-%m-%d'),
            'paese_nascita': 'ITA',
            'paese_allevamento': 'ITA',
            'paese_macellazione': 'IT-123',
            'paese_sezionamento': 'IT-456'
        }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], '/magazzino')

        # Check parameter binding
        insert_call = mock_cursor.execute.call_args_list[-1]
        sql, params = insert_call[0]
        self.assertIn('INSERT INTO LOTTO_MADRE', sql)
        self.assertEqual(params[0], '1')
        self.assertEqual(params[1], 'L-106')
        self.assertEqual(params[2], 'Chianina Alta Qualita')
        self.assertIsNone(params[3])  # data_scadenza is None
        self.assertEqual(params[4], 'ITA')
        self.assertEqual(params[5], 'ITA')
        self.assertEqual(params[6], 'IT-123')
        self.assertEqual(params[7], 'IT-456')
        self.assertEqual(params[8], slaughter_date)
        mock_conn.commit.assert_called_once()

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_tc_str_08_meat_with_expiration_date_only_success(self, mock_getconn, mock_putconn):
        """TC-STR-08: Meat with valid 4 countries and expiration date only (no slaughter date) -> success."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 2, 'denominazione': 'Capocollo di Maiale', 'categoria': 'Suino'
        })

        exp_date = datetime.date.today() + datetime.timedelta(days=14)
        response = self.client.post('/salva_carico', data={
            'id_articolo': '2',
            'codice_lotto_fornitore': 'L-107',
            'fornitore': 'Suini Padani',
            'data_scadenza': exp_date.strftime('%Y-%m-%d'),
            'data_macellazione': '',
            'paese_nascita': 'ITA',
            'paese_allevamento': 'ITA',
            'paese_macellazione': 'IT-333',
            'paese_sezionamento': 'IT-444'
        }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], '/magazzino')

        insert_call = mock_cursor.execute.call_args_list[-1]
        sql, params = insert_call[0]
        self.assertEqual(params[3], exp_date)
        self.assertIsNone(params[8])  # data_macellazione is None

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_tc_str_09_meat_with_both_dates_success(self, mock_getconn, mock_putconn):
        """TC-STR-09: Meat with valid 4 countries and both dates present and valid -> success."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 3, 'denominazione': 'Petto di Pollo', 'categoria': 'Avicolo'
        })

        slaughter_date = datetime.date.today() - datetime.timedelta(days=1)
        exp_date = datetime.date.today() + datetime.timedelta(days=6)
        response = self.client.post('/salva_carico', data={
            'id_articolo': '3',
            'codice_lotto_fornitore': 'L-108',
            'fornitore': 'Avicola Veneta',
            'data_scadenza': exp_date.strftime('%Y-%m-%d'),
            'data_macellazione': slaughter_date.strftime('%Y-%m-%d'),
            'paese_nascita': 'ITA',
            'paese_allevamento': 'ITA',
            'paese_macellazione': 'IT-001',
            'paese_sezionamento': 'IT-002'
        }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], '/magazzino')

        insert_call = mock_cursor.execute.call_args_list[-1]
        sql, params = insert_call[0]
        self.assertEqual(params[3], exp_date)
        self.assertEqual(params[8], slaughter_date)

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_tc_str_10_category_case_insensitivity_and_trimming(self, mock_getconn, mock_putconn):
        """TC-STR-10: Categoria formatted with mixed case and spaces '  BOVINO  ' handled as meat."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 1, 'denominazione': 'Costata di Manzo', 'categoria': '  BOVINO  '
        })

        # Missing origin fields should fail because it is recognized as Bovino
        response = self.client.post('/salva_carico', data={
            'id_articolo': '1',
            'codice_lotto_fornitore': 'L-109',
            'fornitore': 'Allevamento',
            'data_scadenza': (datetime.date.today() + datetime.timedelta(days=10)).strftime('%Y-%m-%d'),
            'paese_nascita': '',
            'paese_allevamento': '',
            'paese_macellazione': '',
            'paese_sezionamento': ''
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Per le categorie carni (Bovino, Suino, Avicolo) tutti i campi di origine'.encode('utf-8'), response.data)

    # =========================================================================
    # CATEGORY 3: NON-MEAT ARTICLES - SANITIZATION & MANDATORY SCADENZA
    # =========================================================================

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_tc_str_11_non_meat_spezie_clean_insert(self, mock_getconn, mock_putconn):
        """TC-STR-11: Non-meat (Spezie) with valid expiration inserts NULLs for origin and slaughter date."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 10, 'denominazione': 'Sale Marino Fine', 'categoria': 'Spezie'
        })

        exp_date = datetime.date.today() + datetime.timedelta(days=300)
        response = self.client.post('/salva_carico', data={
            'id_articolo': '10',
            'codice_lotto_fornitore': 'SALE-01',
            'fornitore': 'Saline Spa',
            'data_scadenza': exp_date.strftime('%Y-%m-%d'),
            'data_macellazione': '',
            'paese_nascita': '',
            'paese_allevamento': '',
            'paese_macellazione': '',
            'paese_sezionamento': ''
        }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        insert_call = mock_cursor.execute.call_args_list[-1]
        sql, params = insert_call[0]
        self.assertIsNone(params[4])  # paese_nascita
        self.assertIsNone(params[5])  # paese_allevamento
        self.assertIsNone(params[6])  # paese_macellazione
        self.assertIsNone(params[7])  # paese_sezionamento
        self.assertIsNone(params[8])  # data_macellazione

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_tc_str_12_non_meat_latticini_with_rogue_meat_data_sanitized_to_null(self, mock_getconn, mock_putconn):
        """TC-STR-12: Non-meat (Latticini) submitted with rogue origin countries and slaughter date is sanitized to NULL."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 11, 'denominazione': 'Formaggio Caciocavallo', 'categoria': 'Latticini'
        })

        exp_date = datetime.date.today() + datetime.timedelta(days=60)
        response = self.client.post('/salva_carico', data={
            'id_articolo': '11',
            'codice_lotto_fornitore': 'FORM-02',
            'fornitore': 'Caseificio Lucano',
            'data_scadenza': exp_date.strftime('%Y-%m-%d'),
            'data_macellazione': (datetime.date.today() - datetime.timedelta(days=5)).strftime('%Y-%m-%d'),
            'paese_nascita': 'FRA',
            'paese_allevamento': 'FRA',
            'paese_macellazione': 'FRA',
            'paese_sezionamento': 'FRA'
        }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        insert_call = mock_cursor.execute.call_args_list[-1]
        sql, params = insert_call[0]
        self.assertEqual(params[3], exp_date)
        self.assertIsNone(params[4], "paese_nascita must be sanitized to NULL for Latticini")
        self.assertIsNone(params[5], "paese_allevamento must be sanitized to NULL for Latticini")
        self.assertIsNone(params[6], "paese_macellazione must be sanitized to NULL for Latticini")
        self.assertIsNone(params[7], "paese_sezionamento must be sanitized to NULL for Latticini")
        self.assertIsNone(params[8], "data_macellazione must be sanitized to NULL for Latticini")

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_tc_str_13_non_meat_missing_expiration_fails(self, mock_getconn, mock_putconn):
        """TC-STR-13: Non-meat (Farinacei) missing data_scadenza is rejected."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 12, 'denominazione': 'Pane Grattugiato', 'categoria': 'Farinacei'
        })

        response = self.client.post('/salva_carico', data={
            'id_articolo': '12',
            'codice_lotto_fornitore': 'PANE-01',
            'fornitore': 'Molino Rossi',
            'data_scadenza': '',
            'data_macellazione': ''
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('I campi obbligatori (Prodotto, Lotto, Fornitore, Scadenza) non sono stati compilati.'.encode('utf-8'), response.data)

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_tc_str_14_non_meat_only_slaughter_date_fails(self, mock_getconn, mock_putconn):
        """TC-STR-14: Non-meat (Uova) providing only slaughter date (without data_scadenza) fails."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 13, 'denominazione': 'Uova Fresche', 'categoria': 'Uova'
        })

        slaughter_date = datetime.date.today() - datetime.timedelta(days=1)
        response = self.client.post('/salva_carico', data={
            'id_articolo': '13',
            'codice_lotto_fornitore': 'UOVA-01',
            'fornitore': 'Allevamento Galline',
            'data_scadenza': '',
            'data_macellazione': slaughter_date.strftime('%Y-%m-%d'),
            'paese_nascita': 'ITA',
            'paese_allevamento': 'ITA',
            'paese_macellazione': 'ITA',
            'paese_sezionamento': 'ITA'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        # Non-meat requires data_scadenza
        self.assertIn('I campi obbligatori (Prodotto, Lotto, Fornitore, Scadenza) non sono stati compilati.'.encode('utf-8'), response.data)

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_tc_str_15_unknown_category_treated_as_non_meat(self, mock_getconn, mock_putconn):
        """TC-STR-15: Article with unknown category (e.g. 'Involucri' or None) follows non-meat workflow."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 14, 'denominazione': 'Budello Naturale', 'categoria': 'Involucri'
        })

        exp_date = datetime.date.today() + datetime.timedelta(days=180)
        response = self.client.post('/salva_carico', data={
            'id_articolo': '14',
            'codice_lotto_fornitore': 'BUD-01',
            'fornitore': 'Budelli Naturali Spa',
            'data_scadenza': exp_date.strftime('%Y-%m-%d'),
            'data_macellazione': '',
            'paese_nascita': '',
            'paese_allevamento': '',
            'paese_macellazione': '',
            'paese_sezionamento': ''
        }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        insert_call = mock_cursor.execute.call_args_list[-1]
        sql, params = insert_call[0]
        self.assertEqual(params[3], exp_date)
        self.assertIsNone(params[4])
        self.assertIsNone(params[8])

    # =========================================================================
    # CATEGORY 4: DATE BOUNDARIES & ANOMALIES
    # =========================================================================

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_tc_str_16_slaughter_date_today_is_valid(self, mock_getconn, mock_putconn):
        """TC-STR-16: Slaughter date equal to today (datetime.date.today()) is valid (not in future)."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 1, 'denominazione': 'Carne Macinata Bovino', 'categoria': 'Bovino'
        })

        today_str = datetime.date.today().strftime('%Y-%m-%d')
        response = self.client.post('/salva_carico', data={
            'id_articolo': '1',
            'codice_lotto_fornitore': 'L-TODAY',
            'fornitore': 'Macelli Riuniti',
            'data_macellazione': today_str,
            'paese_nascita': 'ITA',
            'paese_allevamento': 'ITA',
            'paese_macellazione': 'ITA',
            'paese_sezionamento': 'ITA'
        }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_tc_str_17_slaughter_date_tomorrow_rejected(self, mock_getconn, mock_putconn):
        """TC-STR-17: Slaughter date tomorrow (+1 day) is rejected with error."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 1, 'denominazione': 'Carne Macinata Bovino', 'categoria': 'Bovino'
        })

        tomorrow_str = (datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        response = self.client.post('/salva_carico', data={
            'id_articolo': '1',
            'codice_lotto_fornitore': 'L-TOMORROW',
            'fornitore': 'Macelli Riuniti',
            'data_macellazione': tomorrow_str,
            'paese_nascita': 'ITA',
            'paese_allevamento': 'ITA',
            'paese_macellazione': 'ITA',
            'paese_sezionamento': 'ITA'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('La data di macellazione non può essere nel futuro.'.encode('utf-8'), response.data)

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_tc_str_18_expiration_date_today_is_valid(self, mock_getconn, mock_putconn):
        """TC-STR-18: Expiration date equal to today is valid (exp < today is False)."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 10, 'denominazione': 'Sale', 'categoria': 'Spezie'
        })

        today_str = datetime.date.today().strftime('%Y-%m-%d')
        response = self.client.post('/salva_carico', data={
            'id_articolo': '10',
            'codice_lotto_fornitore': 'SALE-TODAY',
            'fornitore': 'Saline',
            'data_scadenza': today_str
        }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_tc_str_19_expiration_date_yesterday_rejected(self, mock_getconn, mock_putconn):
        """TC-STR-19: Expiration date yesterday (-1 day) is rejected with error."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 10, 'denominazione': 'Sale', 'categoria': 'Spezie'
        })

        yesterday_str = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        response = self.client.post('/salva_carico', data={
            'id_articolo': '10',
            'codice_lotto_fornitore': 'SALE-PAST',
            'fornitore': 'Saline',
            'data_scadenza': yesterday_str
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('La data di scadenza non può essere nel passato.'.encode('utf-8'), response.data)

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_tc_str_20_malformed_slaughter_date_rejected(self, mock_getconn, mock_putconn):
        """TC-STR-20: Malformed slaughter date string returns format error."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 1, 'denominazione': 'Carne Macinata Bovino', 'categoria': 'Bovino'
        })

        response = self.client.post('/salva_carico', data={
            'id_articolo': '1',
            'codice_lotto_fornitore': 'L-BAD-DATE',
            'fornitore': 'Fornitore',
            'data_macellazione': '2026-02-31',  # Invalid date
            'paese_nascita': 'ITA',
            'paese_allevamento': 'ITA',
            'paese_macellazione': 'ITA',
            'paese_sezionamento': 'ITA'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Formato data di macellazione non valido.'.encode('utf-8'), response.data)

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_tc_str_21_malformed_expiration_date_rejected(self, mock_getconn, mock_putconn):
        """TC-STR-21: Malformed expiration date string returns format error."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 10, 'denominazione': 'Sale', 'categoria': 'Spezie'
        })

        response = self.client.post('/salva_carico', data={
            'id_articolo': '10',
            'codice_lotto_fornitore': 'SALE-01',
            'fornitore': 'Saline',
            'data_scadenza': 'invalid-date-string'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Formato data di scadenza non valido.'.encode('utf-8'), response.data)

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_tc_str_22_same_day_slaughter_and_expiration_is_valid(self, mock_getconn, mock_putconn):
        """TC-STR-22: data_macellazione == data_scadenza == today is valid."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 1, 'denominazione': 'Carne Macinata Bovino', 'categoria': 'Bovino'
        })

        today_str = datetime.date.today().strftime('%Y-%m-%d')
        response = self.client.post('/salva_carico', data={
            'id_articolo': '1',
            'codice_lotto_fornitore': 'L-SAME',
            'fornitore': 'Fornitore',
            'data_macellazione': today_str,
            'data_scadenza': today_str,
            'paese_nascita': 'ITA',
            'paese_allevamento': 'ITA',
            'paese_macellazione': 'ITA',
            'paese_sezionamento': 'ITA'
        }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)

    # =========================================================================
    # CATEGORY 5: STRING SANITIZATION & SPECIAL CHARACTERS
    # =========================================================================

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_tc_str_23_unicode_and_apostrophes_in_fornitore(self, mock_getconn, mock_putconn):
        """TC-STR-23: Accented characters, quotes, and unicode in fornitore & lotto handled safely."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 1, 'denominazione': 'Carne Macinata Bovino', 'categoria': 'Bovino'
        })

        fornitore_str = "Soc. Agr. L'Antica Cascina S.r.l. & C. «Qualità» 🥩"
        lotto_str = "LOT-2026/08-A#1"
        today_str = datetime.date.today().strftime('%Y-%m-%d')

        response = self.client.post('/salva_carico', data={
            'id_articolo': '1',
            'codice_lotto_fornitore': lotto_str,
            'fornitore': fornitore_str,
            'data_macellazione': today_str,
            'paese_nascita': 'FR / ITA',
            'paese_allevamento': 'IT-PIEM-001',
            'paese_macellazione': 'IT-CE-123',
            'paese_sezionamento': 'IT-CE-456'
        }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        insert_call = mock_cursor.execute.call_args_list[-1]
        sql, params = insert_call[0]
        self.assertEqual(params[1], lotto_str)
        self.assertEqual(params[2], fornitore_str)
        self.assertEqual(params[4], 'FR / ITA')
        self.assertEqual(params[5], 'IT-PIEM-001')
        self.assertEqual(params[6], 'IT-CE-123')
        self.assertEqual(params[7], 'IT-CE-456')

    # =========================================================================
    # CATEGORY 6: TRANSACTION ROLLBACK AND ERROR RECOVERY
    # =========================================================================

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_tc_str_24_database_exception_triggers_rollback(self, mock_getconn, mock_putconn):
        """TC-STR-24: Database execution error triggers rollback and user flash message."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_getconn.return_value = mock_conn

        # Step 1: Article query succeeds
        mock_cursor.fetchone.return_value = {
            'id_articolo': 1, 'denominazione': 'Carne Macinata Bovino', 'categoria': 'Bovino'
        }

        # Step 2: Insert statement raises an Exception (e.g. DB connection dropped, constraint fail)
        def side_effect_execute(sql, params=None):
            if 'INSERT INTO LOTTO_MADRE' in sql:
                raise RuntimeError("Simulated Database Connection Failure / Constraint Error")

        mock_cursor.execute.side_effect = side_effect_execute

        today_str = datetime.date.today().strftime('%Y-%m-%d')
        response = self.client.post('/salva_carico', data={
            'id_articolo': '1',
            'codice_lotto_fornitore': 'L-ERR',
            'fornitore': 'Fornitore Test',
            'data_macellazione': today_str,
            'paese_nascita': 'ITA',
            'paese_allevamento': 'ITA',
            'paese_macellazione': 'ITA',
            'paese_sezionamento': 'ITA'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Errore durante il salvataggio. Controllare i dati inseriti.'.encode('utf-8'), response.data)
        mock_conn.rollback.assert_called_once()
        mock_putconn.assert_called_once_with(mock_conn)

    # =========================================================================
    # CATEGORY 7: THERMAL LABEL ROUTE NON-REGRESSION
    # =========================================================================

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_tc_str_25_thermal_label_bovino_missing_origin_guard(self, mock_getconn, mock_putconn):
        """TC-STR-25: Thermal label for Bovino with missing origin fields blocks print and redirects to magazzino."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_getconn.return_value = mock_conn

        mock_cursor.fetchone.return_value = {
            'id_lotto_madre': 50,
            'codice_lotto_fornitore': 'TAG-50',
            'data_carico': datetime.datetime.now(),
            'data_scadenza': datetime.date.today() + datetime.timedelta(days=5),
            'data_macellazione': datetime.date.today(),
            'paese_nascita': 'ITA',
            'paese_allevamento': None,  # Missing
            'paese_macellazione': 'ITA',
            'paese_sezionamento': None,  # Missing
            'denominazione': 'Fiorentina di Scottona',
            'categoria': 'Bovino',
            'tipo_categoria': 'TAGLIO'
        }

        response = self.client.get('/stampa_etichetta_taglio/50', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Dati di tracciabilità mancanti per questo lotto bovino'.encode('utf-8'), response.data)


if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
