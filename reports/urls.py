# reports/urls.py

from django.urls import path
from reports.views import dashboard, financial_reports, inventory_reports, sales_reports, custom_reports

app_name = 'reports'

urlpatterns = [
    # Dashboard
    path('', dashboard.dashboard_view, name='dashboard'),
    path('dashboard/', dashboard.dashboard_view, name='dashboard'),
    
    # Financial Reports
    # path('financial/', financial_reports.financial_report, name='financial_report'),
    
    # Inventory Reports
    # path('inventory/', inventory_reports.inventory_report, name='inventory_report'),
    
    # Sales Reports
    # path('sales/', sales_reports.sales_report, name='sales_report'),
    
    # Custom Reports
    # path('custom/', custom_reports.custom_report, name='custom_report'),
]