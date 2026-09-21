"""
Employee import type registration.
"""
from common.middleware.database_middleware import get_customer_db
from common.views.import_excel import register_import_type
from common.models.employee import ensure_employees_table

def register_employee_imports():
    """Idempotent - safe to call on every request."""
    register_import_type('employee', {
        'label'        : 'Employee',
        'table'        : 'Employees',
        'pk_col'       : 'RegNo',
        'db_alias_fn'  : get_customer_db,
        'table_creator': ensure_employees_table,
        'columns'      : [
            {'excel': 'Reg No',         'db_col': 'RegNo',         'type': 'str',   'required': True},
            {'excel': 'Emp Name',       'db_col': 'EmpName',       'type': 'str',   'required': True},
            {'excel': 'Mobile',         'db_col': 'Mobile',        'type': 'str',   'required': False},
            # ItemGroup lookup fields
            {'excel': 'Designation',    'db_col': 'Desig',         'type': 'int',   'required': False, 'itemgroup_col': True, 'category_id': 13},
            {'excel': 'Actual Job',     'db_col': 'ActualJob',     'type': 'int',   'required': False, 'itemgroup_col': True, 'category_id': 44},
            {'excel': 'Nationality',    'db_col': 'Nationality',   'type': 'int',   'required': False, 'itemgroup_col': True, 'category_id': 51},
            {'excel': 'Accomedation',   'db_col': 'Accomadation',  'type': 'int',   'required': False, 'itemgroup_col': True, 'category_id': 98},
            # Plain fields
            {'excel': 'Gender',         'db_col': 'Gender',        'type': 'str',   'required': False},
            {'excel': 'Passport No',    'db_col': 'PasportNo',     'type': 'str',   'required': False},
            {'excel': 'PP Expiry',      'db_col': 'PPExpiryDate',  'type': 'date',  'required': False},
            {'excel': 'QID No',         'db_col': 'RPNo',          'type': 'str',   'required': False},
            {'excel': 'ID Expiry',      'db_col': 'RPExpiryDate',  'type': 'date',  'required': False},
            {'excel': 'DOJ',            'db_col': 'DOJ',           'type': 'date',  'required': False},
            {'excel': 'DOB',            'db_col': 'DOB',           'type': 'date',  'required': False},
            {'excel': 'Current Proj',   'db_col': 'CurrentProj',   'type': 'str',   'required': False},
            {'excel': 'Basic Salary',   'db_col': 'BasicPay',      'type': 'float', 'required': False},
            {'excel': 'Allowance',      'db_col': 'DefAllowance',  'type': 'float', 'required': False},
            {'excel': 'Acc Allowance',  'db_col': 'AccAllowance',  'type': 'float', 'required': False},
            {'excel': 'Food Allowance', 'db_col': 'FoodAllowance', 'type': 'float', 'required': False},
            {'excel': 'Remarks',        'db_col': 'Remarks',       'type': 'str',   'required': False},
        ],
    })
