from django.urls import path

from .views import (
    cart_view,
    checkout_address_view,
    checkout_address_form_view,
    checkout_address_delete_view,
    checkout_payment_view,
    checkout_payment_create_view,
    checkout_payment_verify_view,
    checkout_summary_view,
    track_orders_view,
    order_detail_view,
)


urlpatterns = [
    path("cart/", cart_view, name="cart"),
    path("checkout/address/", checkout_address_view, name="checkout_address"),
    path("checkout/address/new/", checkout_address_form_view, name="checkout_address_new"),
    path("checkout/address/<int:address_id>/edit/", checkout_address_form_view, name="checkout_address_edit"),
    path("checkout/address/<int:address_id>/delete/", checkout_address_delete_view, name="checkout_address_delete"),
    path("checkout/payment/", checkout_payment_view, name="checkout_payment"),
    path("checkout/payment/create/", checkout_payment_create_view, name="checkout_payment_create"),
    path("checkout/payment/verify/", checkout_payment_verify_view, name="checkout_payment_verify"),
    path("checkout/summary/", checkout_summary_view, name="checkout_summary"),
    path("orders/", track_orders_view, name="track_orders"),
    path("orders/<int:order_id>/", order_detail_view, name="order_detail"),
]
