from django.contrib import admin
from .models import OTPCode, Prescription, StoreCredit, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "whatsapp_opt_in")
    search_fields = ("user__username", "phone")


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ("identifier", "channel", "verified", "expires_at", "created_at")
    list_filter = ("channel", "verified")
    search_fields = ("identifier",)


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "power_type", "created_at")
    list_filter = ("power_type",)
    search_fields = ("user__username", "name")


@admin.register(StoreCredit)
class StoreCreditAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "balance", "updated_at")
    search_fields = ("user__username", "code")
