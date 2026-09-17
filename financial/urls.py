# financial/urls.py

from django.urls import path
from financial.views import dashboard, accounts, vouchers, reports, statements

app_name = 'financial'

urlpatterns = [
    # Dashboard
    path('', dashboard.dashboard_view, name='dashboard'),
    path('dashboard/', dashboard.dashboard_view, name='dashboard'),
    
    # Accounts
    # path('accounts/', accounts.accounts_list, name='accounts_list'),
    
    # Vouchers
    # path('vouchers/', vouchers.voucher_list, name='voucher_list'),
    # path('vouchers/create/', vouchers.voucher_create, name='voucher_create'),
    
    # Statements
    # path('ledger/', statements.ledger_view, name='ledger'),
    # path('trial-balance/', statements.trial_balance, name='trial_balance'),
    # path('profit-loss/', statements.profit_loss, name='profit_loss'),
    
    # Reports
    # path('reports/', reports.financial_reports, name='financial_reports'),
]