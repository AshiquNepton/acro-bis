# inventory/urls.py

from django.urls import path
from inventory.views import dashboard, items, stock, purchase, reports, item_master

app_name = 'inventory'

urlpatterns = [
    # Dashboard
    path('', dashboard.dashboard_view, name='dashboard'),
    path('dashboard/', dashboard.dashboard_view, name='dashboard'),

    # Item Master — page view
    path('item-master/', item_master.item_master_view, name='item_master'),

    # Item Master — CRUD endpoints
    path('item-master/save/',   item_master.save_item,            name='item_master_save'),
    path('item-master/load/',   item_master.load_item,            name='item_master_load'),
    path('item-master/delete/', item_master.delete_item,          name='item_master_delete'),
    path('item-master/lookup/', item_master.lookup_item,          name='item_master_lookup'),
    path('item-master/resolve-groups/', item_master.resolve_groups, name='item_master_resolve_groups'),

    # Item Master — AI product info fetcher
    path('item-master/ai-product-info/', item_master.ai_fetch_product_info, name='ai_fetch_product_info'),

    # Stock
    # path('stock/', stock.stock_list, name='stock_list'),

    # Purchase
    # path('purchase/', purchase.purchase_list, name='purchase_list'),
    # path('purchase/order/', purchase.purchase_order, name='purchase_order'),

    # Reports
    # path('reports/', reports.inventory_reports, name='inventory_reports'),
]