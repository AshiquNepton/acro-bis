# laundry/urls.py

from django.urls import path
from laundry.views import dashboard, orders, services, pricing, delivery, reports

app_name = 'laundry'

urlpatterns = [
    # Dashboard
    path('', dashboard.dashboard_view, name='dashboard'),
    path('dashboard/', dashboard.dashboard_view, name='dashboard'),
    
    # Orders
    # path('orders/', orders.order_list, name='order_list'),
    # path('orders/create/', orders.order_create, name='order_create'),
    # path('orders/<int:order_id>/', orders.order_detail, name='order_detail'),
    
    # Services
    # path('services/', services.service_list, name='service_list'),
    # path('services/create/', services.service_create, name='service_create'),
    
    # Pricing
    # path('pricing/', pricing.pricing_list, name='pricing_list'),
    
    # Delivery
    # path('delivery/schedule/', delivery.delivery_schedule, name='delivery_schedule'),
    # path('pickup/schedule/', delivery.pickup_schedule, name='pickup_schedule'),
    
    # Reports
    # path('reports/daily/', reports.daily_report, name='daily_report'),
    # path('reports/service/', reports.service_report, name='service_report'),
]