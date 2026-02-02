from django.urls import path
from .views import order_list_view

app_name = "orders"

urlpatterns = [
    path("", order_list_view, name="list"),
]
