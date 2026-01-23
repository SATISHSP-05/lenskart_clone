from django.contrib import admin

from .models import CheckoutAddress, CheckoutOrder, CheckoutPayment


@admin.register(CheckoutAddress)
class CheckoutAddressAdmin(admin.ModelAdmin):
    list_display = ("name", "label", "city", "state", "pincode", "phone", "is_default")
    list_filter = ("label", "state", "is_default")
    search_fields = ("name", "phone", "pincode", "city", "state")


@admin.register(CheckoutOrder)
class CheckoutOrderAdmin(admin.ModelAdmin):
    list_display = ("razorpay_order_id", "amount_paise", "currency", "status", "created_at")
    list_filter = ("status", "currency")
    search_fields = ("razorpay_order_id",)


@admin.register(CheckoutPayment)
class CheckoutPaymentAdmin(admin.ModelAdmin):
    list_display = ("razorpay_payment_id", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("razorpay_payment_id",)
