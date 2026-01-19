from django.contrib import admin
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_id", "user", "status", "total_price", "created_at")
    list_filter = ("status",)
    search_fields = ("order_id", "user__username")
