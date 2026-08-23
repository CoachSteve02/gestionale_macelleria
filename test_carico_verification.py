"""
Automated Verification Test Suite for Gestionale_Macelleria Carico Merci HACCP Dynamic Form Milestone.
Tests cover:
- Database schema and DDL migration correctness
- Frontend Jinja2 template and Vanilla JS DOM logic
- Backend conditional validation matrix for meat (Bovino, Suino, Avicolo) and non-meat
- 9-column INSERT parameter binding and NULL safety
- Non-regression safety on existing routes and queries
"""

import unittest
from unittest.mock import MagicMock, patch
import datetime
import re
import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import app, init_db_migrations


class TestDatabaseSchemaAndMigration(unittest.TestCase):
    """Verifies database.sql schema alignment and DDL migration commands."""

    def test_database_sql_lotto_madre_schema(self):
        """TC-DB-01: Verify database.sql contains data_macellazione and nullable data_scadenza in LOTTO_MADRE."""
        db_sql_path = os.path.join(PROJECT_ROOT, 'database.sql')
        self.assertTrue(os.path.exists(db_sql_path), "database.sql file must exist")
        
        with open(db_sql_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract CREATE TABLE LOTTO_MADRE block
        match = re.search(r'CREATE\s+TABLE\s+LOTTO_MADRE\s*\((.*?)\);', content, re.DOTALL | re.IGNORECASE)
        self.assertIsNotNone(match, "CREATE TABLE LOTTO_MADRE must exist in database.sql")
        table_def = match.group(1)

        # Check data_macellazione exists
        self.assertRegex(table_def, r'data_macellazione\s+DATE', "data_macellazione DATE column must be defined in LOTTO_MADRE")
        
        # Check data_scadenza is NOT NULL free
        self.assertRegex(table_def, r'data_scadenza\s+DATE\s*,', "data_scadenza must be nullable (no NOT NULL) in LOTTO_MADRE")

    def test_init_db_migrations_execution(self):
        """TC-DB-02: Verify init_db_migrations executes the correct idempotent ALTER TABLE statements."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        with patch('app.db_pool.getconn', return_value=mock_conn), \
             patch('app.db_pool.putconn') as mock_putconn:
            init_db_migrations()
            
            mock_cursor.execute.assert_called_once()
            executed_sql = mock_cursor.execute.call_args[0][0]
            self.assertIn("ALTER TABLE LOTTO_MADRE ADD COLUMN IF NOT EXISTS data_macellazione DATE;", executed_sql)
            self.assertIn("ALTER TABLE LOTTO_MADRE ALTER COLUMN data_scadenza DROP NOT NULL;", executed_sql)
            mock_conn.commit.assert_called_once()
            mock_putconn.assert_called_once_with(mock_conn)


class TestFrontendCaricoTemplate(unittest.TestCase):
    """Verifies template markup, attributes, and vanilla JS in templates/carico.html."""

    def setUp(self):
        template_path = os.path.join(PROJECT_ROOT, 'templates', 'carico.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            self.template_content = f.read()

    def test_data_categoria_attribute_present(self):
        """TC-FE-01: Verify option tags include data-categoria attribute in carico.html."""
        self.assertIn('data-categoria="{{ categoria }}"', self.template_content,
                      "Options inside optgroup must have data-categoria attribute")

    def test_haccp_section_and_fields_present(self):
        """TC-FE-02: Verify #sezione-tracciabilita exists with required HACCP styling and inputs."""
        self.assertIn('id="sezione-tracciabilita"', self.template_content)
        self.assertIn('class="hidden', self.template_content, "HACCP section should have 'hidden' class initially")
        self.assertIn('id="paese_nascita"', self.template_content)
        self.assertIn('id="paese_allevamento"', self.template_content)
        self.assertIn('id="paese_macellazione"', self.template_content)
        self.assertIn('id="paese_sezionamento"', self.template_content)
        self.assertIn('id="data_macellazione"', self.template_content)

    def test_vanilla_js_toggle_and_required_logic(self):
        """TC-FE-03: Verify client-side JavaScript handles categories and toggles required state."""
        self.assertIn("const categorieCarne = ['bovino', 'suino', 'avicolo'];", self.template_content)
        self.assertIn("sezioneTracciabilita.classList.remove('hidden');", self.template_content)
        self.assertIn("sezioneTracciabilita.classList.add('hidden');", self.template_content)
        self.assertIn("input.required = true;", self.template_content)
        self.assertIn("input.required = false;", self.template_content)
        self.assertIn("selectArticolo.addEventListener('change'", self.template_content)


class TestBackendSalvaCaricoValidation(unittest.TestCase):
    """Verifies backend conditional validation in /salva_carico for all scenarios."""

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret'
        self.client = app.test_client()

    def _setup_mock_db(self, mock_getconn, mock_putconn, articolo_row=None):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_getconn.return_value = mock_conn
        
        if articolo_row is not None:
            mock_cursor.fetchone.return_value = articolo_row
            
        return mock_conn, mock_cursor

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_missing_common_fields_fails(self, mock_getconn, mock_putconn):
        """TC-BE-01: Missing base mandatory field (e.g. fornitore) redirects with error."""
        response = self.client.post('/salva_carico', data={
            'id_articolo': '1',
            'codice_lotto_fornitore': 'L-1234',
            'fornitore': '',  # missing
            'data_scadenza': '2026-12-31'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('I campi obbligatori (Prodotto, Lotto, Fornitore) devono essere compilati.'.encode('utf-8'), response.data)

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_invalid_or_nonexistent_article_fails(self, mock_getconn, mock_putconn):
        """TC-BE-02: Selected article does not exist in ARTICOLO table."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row=None)

        response = self.client.post('/salva_carico', data={
            'id_articolo': '9999',
            'codice_lotto_fornitore': 'L-1234',
            'fornitore': 'Test Fornitore',
            'data_scadenza': '2026-12-31'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Articolo selezionato non valido o inesistente.'.encode('utf-8'), response.data)

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_meat_missing_country_origins_fails(self, mock_getconn, mock_putconn):
        """TC-BE-03: Meat product (Bovino) submitted without all 4 country fields fails."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 1, 'denominazione': 'Carne Macinata Bovino', 'categoria': 'Bovino'
        })

        response = self.client.post('/salva_carico', data={
            'id_articolo': '1',
            'codice_lotto_fornitore': 'L-1234',
            'fornitore': 'Rossi Carni',
            'data_scadenza': '2026-12-31',
            'paese_nascita': 'ITA',
            'paese_allevamento': 'ITA',
            'paese_macellazione': 'ITA',
            'paese_sezionamento': ''  # missing
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Per le categorie carni (Bovino, Suino, Avicolo) tutti i campi di origine'.encode('utf-8'), response.data)

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_meat_missing_both_dates_fails(self, mock_getconn, mock_putconn):
        """TC-BE-04: Meat product (Suino) submitted without data_macellazione and without data_scadenza fails."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 2, 'denominazione': 'Capocollo di Maiale', 'categoria': 'Suino'
        })

        response = self.client.post('/salva_carico', data={
            'id_articolo': '2',
            'codice_lotto_fornitore': 'L-1234',
            'fornitore': 'Rossi Carni',
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
    def test_future_slaughter_date_fails(self, mock_getconn, mock_putconn):
        """TC-BE-05: data_macellazione in the future is rejected."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 1, 'denominazione': 'Carne Macinata Bovino', 'categoria': 'Bovino'
        })

        future_date = (datetime.date.today() + datetime.timedelta(days=2)).strftime('%Y-%m-%d')
        response = self.client.post('/salva_carico', data={
            'id_articolo': '1',
            'codice_lotto_fornitore': 'L-1234',
            'fornitore': 'Rossi Carni',
            'data_macellazione': future_date,
            'paese_nascita': 'ITA',
            'paese_allevamento': 'ITA',
            'paese_macellazione': 'ITA',
            'paese_sezionamento': 'ITA'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('La data di macellazione non può essere nel futuro.'.encode('utf-8'), response.data)

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_past_expiration_date_fails(self, mock_getconn, mock_putconn):
        """TC-BE-06: data_scadenza in the past is rejected."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 1, 'denominazione': 'Carne Macinata Bovino', 'categoria': 'Bovino'
        })

        past_date = (datetime.date.today() - datetime.timedelta(days=2)).strftime('%Y-%m-%d')
        response = self.client.post('/salva_carico', data={
            'id_articolo': '1',
            'codice_lotto_fornitore': 'L-1234',
            'fornitore': 'Rossi Carni',
            'data_scadenza': past_date,
            'paese_nascita': 'ITA',
            'paese_allevamento': 'ITA',
            'paese_macellazione': 'ITA',
            'paese_sezionamento': 'ITA'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('La data di scadenza non può essere nel passato.'.encode('utf-8'), response.data)

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_expiration_before_slaughter_fails(self, mock_getconn, mock_putconn):
        """TC-BE-07: data_scadenza earlier than data_macellazione is rejected."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 1, 'denominazione': 'Carne Macinata Bovino', 'categoria': 'Bovino'
        })

        slaughter_date = datetime.date.today().strftime('%Y-%m-%d')
        earlier_date = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        response = self.client.post('/salva_carico', data={
            'id_articolo': '1',
            'codice_lotto_fornitore': 'L-1234',
            'fornitore': 'Rossi Carni',
            'data_macellazione': slaughter_date,
            'data_scadenza': earlier_date,
            'paese_nascita': 'ITA',
            'paese_allevamento': 'ITA',
            'paese_macellazione': 'ITA',
            'paese_sezionamento': 'ITA'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        # Should fail either because past or because < slaughter
        self.assertTrue(b'nel passato' in response.data or b'precedente alla data di macellazione' in response.data)

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_meat_with_slaughter_date_only_success(self, mock_getconn, mock_putconn):
        """TC-BE-08: Meat product with all country fields and slaughter date only successfully inserts 9 columns with data_scadenza=None."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 1, 'denominazione': 'Bistecca Fiorentina', 'categoria': 'Bovino'
        })

        today_date = datetime.date.today()
        response = self.client.post('/salva_carico', data={
            'id_articolo': '1',
            'codice_lotto_fornitore': 'BOV-2026-01',
            'fornitore': 'Allevamento Chianina DOC',
            'data_scadenza': '',
            'data_macellazione': today_date.strftime('%Y-%m-%d'),
            'paese_nascita': 'ITA',
            'paese_allevamento': 'ITA',
            'paese_macellazione': 'IT-1234',
            'paese_sezionamento': 'IT-5678'
        }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], '/magazzino')
        
        # Verify INSERT statement and parameter bindings
        insert_call = mock_cursor.execute.call_args_list[-1]
        sql, params = insert_call[0]
        self.assertIn("INSERT INTO LOTTO_MADRE", sql)
        self.assertEqual(params[0], '1')  # id_articolo
        self.assertEqual(params[1], 'BOV-2026-01')  # codice_lotto_fornitore
        self.assertEqual(params[2], 'Allevamento Chianina DOC')  # fornitore
        self.assertIsNone(params[3])  # data_scadenza is None
        self.assertEqual(params[4], 'ITA')  # paese_nascita
        self.assertEqual(params[5], 'ITA')  # paese_allevamento
        self.assertEqual(params[6], 'IT-1234')  # paese_macellazione
        self.assertEqual(params[7], 'IT-5678')  # paese_sezionamento
        self.assertEqual(params[8], today_date)  # data_macellazione parsed date
        mock_conn.commit.assert_called_once()

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_meat_with_both_dates_success(self, mock_getconn, mock_putconn):
        """TC-BE-09: Avicolo meat with all countries and both dates succeeds."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 3, 'denominazione': 'Petto di Pollo', 'categoria': 'Avicolo'
        })

        today_date = datetime.date.today()
        exp_date = today_date + datetime.timedelta(days=7)
        response = self.client.post('/salva_carico', data={
            'id_articolo': '3',
            'codice_lotto_fornitore': 'AVI-999',
            'fornitore': 'Polli Bio S.r.l.',
            'data_macellazione': today_date.strftime('%Y-%m-%d'),
            'data_scadenza': exp_date.strftime('%Y-%m-%d'),
            'paese_nascita': 'ITA',
            'paese_allevamento': 'ITA',
            'paese_macellazione': 'ITA',
            'paese_sezionamento': 'ITA'
        }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], '/magazzino')
        
        insert_call = mock_cursor.execute.call_args_list[-1]
        sql, params = insert_call[0]
        self.assertEqual(params[3], exp_date)
        self.assertEqual(params[8], today_date)

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_non_meat_simplified_form_success(self, mock_getconn, mock_putconn):
        """TC-BE-10: Non-meat product (Spezie / VARIO) with blank origin countries inserts NULLs cleanly."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 10, 'denominazione': 'Sale Marino Fine', 'categoria': 'Spezie'
        })

        exp_date = datetime.date.today() + datetime.timedelta(days=365)
        response = self.client.post('/salva_carico', data={
            'id_articolo': '10',
            'codice_lotto_fornitore': 'SALE-2026',
            'fornitore': 'Saline Italiane',
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
        self.assertEqual(params[2], 'Saline Italiane')
        self.assertEqual(params[3], exp_date)
        self.assertIsNone(params[4])  # paese_nascita NULL
        self.assertIsNone(params[5])  # paese_allevamento NULL
        self.assertIsNone(params[6])  # paese_macellazione NULL
        self.assertIsNone(params[7])  # paese_sezionamento NULL
        self.assertIsNone(params[8])  # data_macellazione NULL
        mock_conn.commit.assert_called_once()

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_non_meat_missing_expiration_date_fails(self, mock_getconn, mock_putconn):
        """TC-BE-11: Non-meat product missing data_scadenza is rejected."""
        mock_conn, mock_cursor = self._setup_mock_db(mock_getconn, mock_putconn, articolo_row={
            'id_articolo': 10, 'denominazione': 'Sale Marino Fine', 'categoria': 'Spezie'
        })

        response = self.client.post('/salva_carico', data={
            'id_articolo': '10',
            'codice_lotto_fornitore': 'SALE-2026',
            'fornitore': 'Saline Italiane',
            'data_scadenza': '',
            'data_macellazione': ''
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('I campi obbligatori (Prodotto, Lotto, Fornitore, Scadenza) non sono stati compilati.'.encode('utf-8'), response.data)


class TestNonRegression(unittest.TestCase):
    """Verifies that non-regression fixes on existing routes and views are effective."""

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret'
        self.client = app.test_client()

    @patch('app.db_pool.putconn')
    @patch('app.db_pool.getconn')
    def test_stampa_etichetta_taglio_with_null_data_scadenza(self, mock_getconn, mock_putconn):
        """TC-REG-01: Thermal label renders cleanly without AttributeError when data_scadenza is None and data_macellazione is present."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_getconn.return_value = mock_conn

        mock_cursor.fetchone.return_value = {
            'id_lotto_madre': 42,
            'codice_lotto_fornitore': 'TAG-42',
            'data_carico': datetime.datetime.now(),
            'data_scadenza': None,  # Nullable
            'data_macellazione': datetime.date(2026, 8, 20),
            'paese_nascita': 'ITA',
            'paese_allevamento': 'ITA',
            'paese_macellazione': 'ITA',
            'paese_sezionamento': 'ITA',
            'denominazione': 'Fiorentina di Scottona',
            'categoria': 'Bovino',
            'tipo_categoria': 'TAGLIO'
        }

        response = self.client.get('/stampa_etichetta_taglio/42')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Macellato il:', response.data)
        self.assertIn(b'20/08/2026', response.data)
        self.assertIn(b'Fiorentina di Scottona', response.data)


if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
