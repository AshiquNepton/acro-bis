import json
from datetime import date, datetime
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from common.views.crud import (
    BaseCRUD,
    _coerce,
    _safe,
    _parse_field_map,
)


class BaseCRUDHelperTests(SimpleTestCase):
    """Unit tests for BaseCRUD type coercion and formatting helper functions."""

    def test_coerce_int(self):
        self.assertEqual(_coerce('123', 'int'), 123)
        self.assertEqual(_coerce('yes', 'int'), 1)
        self.assertEqual(_coerce('True', 'int'), 1)
        self.assertEqual(_coerce('on', 'int'), 1)
        self.assertEqual(_coerce('active', 'int'), 1)
        self.assertEqual(_coerce('male', 'int'), 1)
        self.assertEqual(_coerce('no', 'int'), 0)
        self.assertEqual(_coerce('inactive', 'int'), 0)
        self.assertEqual(_coerce('female', 'int'), 0)
        self.assertEqual(_coerce('single', 'int'), 0)
        self.assertEqual(_coerce('married', 'int'), 1)
        self.assertEqual(_coerce('divorced', 'int'), 2)
        with self.assertRaises(ValueError):
            _coerce('invalid_int', 'int')

    def test_coerce_float(self):
        self.assertEqual(_coerce('123.45', 'float'), 123.45)
        self.assertEqual(_coerce('50', 'float'), 50.0)
        with self.assertRaises(ValueError):
            _coerce('invalid_float', 'float')

    def test_coerce_date(self):
        d = date(2026, 9, 14)
        self.assertEqual(_coerce('2026-09-14', 'date'), d)
        self.assertEqual(_coerce(d, 'date'), d)
        with self.assertRaises(ValueError):
            _coerce('invalid-date', 'date')

    def test_coerce_bool(self):
        self.assertEqual(_coerce('true', 'bool'), 1)
        self.assertEqual(_coerce('1', 'bool'), 1)
        self.assertEqual(_coerce('yes', 'bool'), 1)
        self.assertEqual(_coerce('false', 'bool'), 0)
        self.assertEqual(_coerce('0', 'bool'), 0)

    def test_coerce_empty_and_none(self):
        self.assertIsNone(_coerce(None, 'int'))
        self.assertIsNone(_coerce('', 'int'))
        self.assertIsNone(_coerce('   ', 'str'))

    def test_safe_serialization(self):
        self.assertEqual(_safe(date(2026, 9, 14)), '2026-09-14')
        self.assertEqual(_safe(datetime(2026, 9, 14, 12, 0, 0)), '2026-09-14 12:00:00')
        self.assertEqual(_safe(1, db_col='Active'), 'Active')
        self.assertEqual(_safe(0, db_col='Active'), 'Inactive')
        self.assertEqual(_safe(1, db_col='Gender'), 'Male')
        self.assertEqual(_safe(0, db_col='Gender'), 'Female')
        self.assertEqual(_safe(1, db_col='MaritalStatus'), 'Married')
        self.assertEqual(_safe('Regular String'), 'Regular String')

    def test_parse_field_map(self):
        unified = {
            'RegNo': ('reg_no', 'str'),
            'Active': ('active', 'int'),
            'DOB': ('dob', 'date'),
        }
        field_map, col_types = _parse_field_map(unified)
        self.assertEqual(field_map, {'RegNo': 'reg_no', 'Active': 'active', 'DOB': 'dob'})
        self.assertEqual(col_types, {'RegNo': 'str', 'Active': 'int', 'DOB': 'date'})

        legacy = {'RegNo': 'reg_no', 'Active': 'active'}
        field_map2, col_types2 = _parse_field_map(legacy, col_types={'Active': 'int'})
        self.assertEqual(field_map2, legacy)
        self.assertEqual(col_types2, {'Active': 'int'})


class BaseCRUDValidationAndMappingTests(SimpleTestCase):
    """Unit tests for field validation and form-to-database dictionary mapping."""

    def setUp(self):
        self.field_map = {
            'RegNo': ('reg_no', 'str'),
            'EmpName': ('emp_name', 'str'),
            'BasicPay': ('basic_pay', 'float'),
            'Active': ('active', 'int'),
            'Notes': ('notes', 'str'),
        }
        self.crud = BaseCRUD(
            table='Employees',
            pk_col='RegNo',
            field_map=self.field_map,
            required=['reg_no', 'emp_name'],
            preserve_empty_on_update=['notes'],
        )

    def test_validate_required_fields(self):
        # Missing emp_name
        post_data = {'reg_no': 'E100', 'emp_name': ''}
        missing = self.crud._validate(post_data)
        self.assertEqual(missing, ['emp_name'])

        # Both present
        post_data = {'reg_no': 'E100', 'emp_name': 'Alice'}
        self.assertEqual(self.crud._validate(post_data), [])

        # Whitespace only
        post_data = {'reg_no': '   ', 'emp_name': 'Bob'}
        self.assertEqual(self.crud._validate(post_data), ['reg_no'])

    def test_pk_val(self):
        self.assertEqual(BaseCRUD._pk_val(' 123 '), '123')
        self.assertIsNone(BaseCRUD._pk_val('   '))
        self.assertIsNone(BaseCRUD._pk_val(None))

    def test_post_to_db_mapping(self):
        post_data = {
            'reg_no': 'E101',
            'emp_name': 'John Doe',
            'basic_pay': '4500.50',
            'active': 'active',
            'unrelated_field': 'ignored',
        }
        db_data = self.crud._post_to_db(post_data)
        self.assertEqual(db_data['RegNo'], 'E101')
        self.assertEqual(db_data['EmpName'], 'John Doe')
        self.assertEqual(db_data['BasicPay'], 4500.50)
        self.assertEqual(db_data['Active'], 1)
        self.assertNotIn('unrelated_field', db_data)

    def test_preserve_empty_on_update(self):
        post_data = {
            'reg_no': 'E101',
            'emp_name': 'John Doe',
            'notes': '',
        }
        # On update: notes is preserved (omitted from db_data)
        db_data_update = self.crud._post_to_db(post_data, is_update=True)
        self.assertNotIn('Notes', db_data_update)

        # On insert: notes is included as None
        db_data_insert = self.crud._post_to_db(post_data, is_update=False)
        self.assertIn('Notes', db_data_insert)
        self.assertIsNone(db_data_insert['Notes'])


class BaseCRUDSQLGenerationTests(SimpleTestCase):
    """Unit tests for BaseCRUD SQL query generation with mocked database cursors."""

    def setUp(self):
        self.field_map = {
            'RegNo': ('reg_no', 'str'),
            'EmpName': ('emp_name', 'str'),
            'BasicPay': ('basic_pay', 'float'),
            'Active': ('active', 'int'),
        }
        self.crud = BaseCRUD(
            table='Employees',
            pk_col='RegNo',
            field_map=self.field_map,
            db_alias='test_db',
            required=['reg_no', 'emp_name'],
        )

    def _setup_mock_cursor(self, mock_connections):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connections.__getitem__.return_value = mock_conn
        return mock_cursor

    @patch('common.views.crud.connections')
    def test_get_sql_generation(self, mock_connections):
        mock_cursor = self._setup_mock_cursor(mock_connections)
        mock_cursor.description = [('RegNo',), ('EmpName',), ('BasicPay',), ('Active',)]
        mock_cursor.fetchone.return_value = ('E101', 'Alice', 5000.0, 1)

        response = self.crud.get('E101')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['reg_no'], 'E101')
        self.assertEqual(data['data']['emp_name'], 'Alice')

        # Check executed SQL
        mock_cursor.execute.assert_called_once()
        sql, params = mock_cursor.execute.call_args[0]
        self.assertIn('SELECT * FROM "Employees" WHERE "RegNo" = %s', sql)
        self.assertEqual(params, ['E101'])

    @patch('common.views.crud.connections')
    def test_get_record_not_found(self, mock_connections):
        mock_cursor = self._setup_mock_cursor(mock_connections)
        mock_cursor.fetchone.return_value = None

        response = self.crud.get('E999')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Record not found')

    @patch('common.views.crud.connections')
    def test_delete_sql_generation(self, mock_connections):
        mock_cursor = self._setup_mock_cursor(mock_connections)
        mock_cursor.fetchone.return_value = (1,)

        response = self.crud.delete('E101')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

        # Verify existence check and DELETE queries
        calls = mock_cursor.execute.call_args_list
        self.assertEqual(len(calls), 2)
        exist_sql, exist_params = calls[0][0]
        self.assertIn('SELECT 1 FROM "Employees" WHERE "RegNo" = %s', exist_sql)
        self.assertEqual(exist_params, ['E101'])

        delete_sql, delete_params = calls[1][0]
        self.assertIn('DELETE FROM "Employees" WHERE "RegNo" = %s', delete_sql)
        self.assertEqual(delete_params, ['E101'])

    @patch('common.views.crud.connections')
    def test_lookup_sql_generation(self, mock_connections):
        mock_cursor = self._setup_mock_cursor(mock_connections)
        mock_cursor.description = [('RegNo',), ('EmpName',)]
        mock_cursor.fetchone.return_value = ('E101', 'Alice')

        response = self.crud.lookup('EmpName', 'Alice')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

        mock_cursor.execute.assert_called_once()
        sql, params = mock_cursor.execute.call_args[0]
        self.assertIn('SELECT * FROM "Employees" WHERE "EmpName" = %s', sql)
        self.assertEqual(params, ['Alice'])

    @patch('common.views.crud.connections')
    def test_search_sql_generation(self, mock_connections):
        mock_cursor = self._setup_mock_cursor(mock_connections)
        mock_cursor.fetchall.return_value = [('E101', 'Alice')]

        response = self.crud.search('Ali', search_col='EmpName', display_cols=['RegNo', 'EmpName'], limit=10)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['results']), 1)

        mock_cursor.execute.assert_called_once()
        sql, params = mock_cursor.execute.call_args[0]
        self.assertIn('SELECT "RegNo", "EmpName" FROM "Employees" WHERE "EmpName" ILIKE %s LIMIT %s', sql)
        self.assertEqual(params, ['%Ali%', 10])

    @patch('common.views.crud.connections')
    def test_list_sql_generation(self, mock_connections):
        mock_cursor = self._setup_mock_cursor(mock_connections)
        mock_cursor.description = [('RegNo',), ('EmpName',), ('Active',)]
        mock_cursor.fetchall.return_value = [('E101', 'Alice', 1)]

        response = self.crud.list(filters={'Active': 1}, order_by='-RegNo', limit=5)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 1)

        mock_cursor.execute.assert_called_once()
        sql, params = mock_cursor.execute.call_args[0]
        self.assertIn('SELECT * FROM "Employees"', sql)
        self.assertIn('WHERE "Active" = %s', sql)
        self.assertIn('ORDER BY "RegNo" DESC', sql)
        self.assertIn('LIMIT 5', sql)
        self.assertEqual(params, [1])

    @patch('common.views.crud.connections')
    def test_check_duplicate_sql(self, mock_connections):
        mock_cursor = self._setup_mock_cursor(mock_connections)
        mock_cursor.fetchone.return_value = ('E101',)

        # Test duplicate check with text column and numeric column
        result = self.crud.check_duplicate(
            unique_fields=[('EmpName', 'Alice'), ('Active', 1)],
            exclude_pk='E102',
        )
        self.assertTrue(result['is_duplicate'])
        self.assertEqual(result['existing_pk'], 'E101')

        mock_cursor.execute.assert_called_once()
        sql, params = mock_cursor.execute.call_args[0]
        self.assertIn('LOWER("EmpName") = LOWER(%s)', sql)
        self.assertIn('"Active" = %s', sql)
        self.assertIn('"RegNo" != %s', sql)
        self.assertIn('LIMIT 1', sql)
        self.assertEqual(params, ['Alice', 1, 'E102'])


class BaseCRUDSaveTests(SimpleTestCase):
    """Unit tests for BaseCRUD.save operation (INSERT, UPDATE, and duplicate checking)."""

    def setUp(self):
        self.print_patcher = patch('builtins.print')
        self.mock_print = self.print_patcher.start()

        self.field_map = {
            'RegNo': ('reg_no', 'str'),
            'EmpName': ('emp_name', 'str'),
            'BasicPay': ('basic_pay', 'float'),
        }
        self.crud = BaseCRUD(
            table='Employees',
            pk_col='RegNo',
            field_map=self.field_map,
            db_alias='test_db',
            required=['reg_no', 'emp_name'],
        )

    def tearDown(self):
        self.print_patcher.stop()

    def _setup_mock_cursor(self, mock_connections):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connections.__getitem__.return_value = mock_conn
        return mock_cursor

    def test_save_missing_required_fields(self):
        post_data = {'reg_no': 'E101'}  # emp_name missing
        response = self.crud.save(post_data)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Required fields missing', data['error'])

    @patch('common.views.crud._is_identity_column', return_value=False)
    @patch('common.views.crud.connections')
    def test_save_insert(self, mock_connections, mock_is_identity):
        mock_cursor = self._setup_mock_cursor(mock_connections)
        # Existence check returns None (new record)
        mock_cursor.fetchone.side_effect = [
            None,          # SELECT 1 FROM Employees WHERE RegNo = 'E101' -> does not exist
            ('E101',),     # INSERT ... RETURNING RegNo
        ]

        post_data = {'reg_no': 'E101', 'emp_name': 'Bob', 'basic_pay': '3000'}
        response = self.crud.save(post_data)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['pk'], 'E101')
        self.assertIn('created', data['message'])

        calls = mock_cursor.execute.call_args_list
        self.assertEqual(len(calls), 2)
        insert_sql, insert_params = calls[1][0]
        self.assertIn('INSERT INTO "Employees"', insert_sql)
        self.assertIn('RETURNING "RegNo"', insert_sql)

    @patch('common.views.crud.connections')
    def test_save_update(self, mock_connections):
        mock_cursor = self._setup_mock_cursor(mock_connections)
        # Existence check returns record (updating existing record)
        mock_cursor.fetchone.return_value = (1,)

        post_data = {'reg_no': 'E101', 'emp_name': 'Bob Updated', 'basic_pay': '3500'}
        response = self.crud.save(post_data)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['pk'], 'E101')
        self.assertIn('updated', data['message'])

        calls = mock_cursor.execute.call_args_list
        self.assertEqual(len(calls), 2)
        update_sql, update_params = calls[1][0]
        self.assertIn('UPDATE "Employees" SET', update_sql)
        self.assertIn('WHERE "RegNo" = %s', update_sql)
        self.assertEqual(update_params[-1], 'E101')

    @patch('common.views.crud.connections')
    def test_save_duplicate_aborted(self, mock_connections):
        mock_cursor = self._setup_mock_cursor(mock_connections)
        # Step 4 existence check returns None (new record)
        # Step 5 duplicate check returns existing record ('E999')
        mock_cursor.fetchone.side_effect = [
            None,         # Existence check
            ('E999',),    # Duplicate check SELECT "RegNo" FROM "Employees" WHERE ...
        ]

        post_data = {'reg_no': 'E101', 'emp_name': 'Bob', 'basic_pay': '3000'}
        response = self.crud.save(post_data, unique_fields=[('EmpName', 'emp_name')])
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertTrue(data.get('duplicate'))
        self.assertEqual(data.get('existing_pk'), 'E999')
