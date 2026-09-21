# reports/urls.py

from django.urls import path
from reports.views import dashboard, financial_reports, inventory_reports, sales_reports, custom_reports, party_reports

app_name = 'reports'

urlpatterns = [
    # Dashboard
    path('', dashboard.dashboard_view, name='dashboard'),
    path('dashboard/', dashboard.dashboard_view, name='dashboard'),
    
    # Financial Reports
    # path('financial/', financial_reports.financial_report, name='financial_report'),
    
    # Inventory Reports
    path('stock-report/', inventory_reports.stock_report, name='stock_report'),
    
    # Sales Reports
    # path('sales/', sales_reports.sales_report, name='sales_report'),
    
    # Custom Reports
    # path('custom/', custom_reports.custom_report, name='custom_report'),

    # Party Reports
    path('customer-list/', party_reports.customer_list, name='customer_list'),
    path('vendor-list/', party_reports.vendor_list, name='vendor_list'),

]