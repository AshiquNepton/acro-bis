# restaurant/urls.py

from django.urls import path
from restaurant.views import dashboard, menu, orders, tables, kitchen, pos, reports

app_name = 'restaurant'

urlpatterns = [
    # Dashboard
    path('', dashboard.dashboard_view, name='dashboard'),
    path('dashboard/', dashboard.dashboard_view, name='dashboard'),
    
    # Menu Management
    # path('menu/', menu.menu_list, name='menu_list'),
    # path('menu/create/', menu.menu_create, name='menu_create'),
    # path('menu/<int:menu_id>/', menu.menu_detail, name='menu_detail'),
    
    # Orders
    # path('orders/', orders.order_list, name='order_list'),
    # path('orders/active/', orders.active_orders, name='active_orders'),
    # path('orders/billing/', orders.billing, name='billing'),
    
    # Tables
    # path('tables/', tables.table_list, name='table_list'),
    # path('tables/layout/', tables.table_layout, name='table_layout'),
    # path('tables/booking/', tables.booking_form, name='booking_form'),
    
    # Kitchen
    # path('kitchen/', kitchen.kitchen_dashboard, name='kitchen_dashboard'),
    # path('kitchen/kot/', kitchen.kot_display, name='kot_display'),
    
    # POS
    # path('pos/', pos.pos_interface, name='pos_interface'),
    
    # Reports
    # path('reports/sales/', reports.sales_report, name='sales_report'),
    # path('reports/menu-performance/', reports.menu_performance, name='menu_performance'),
]