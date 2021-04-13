from django.urls import path
from .views import (
    order_view,
    json_all_orders_view
)

urlpatterns = [
    path('exchange/', order_view, name='exchange-view'),
    path('exchange/json', json_all_orders_view, name='json-all-orders-view'),
]