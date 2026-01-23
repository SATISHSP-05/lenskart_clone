from django.conf import settings
from django.db import models


class CheckoutAddress(models.Model):
    LABEL_CHOICES = [
        ("home", "Home"),
        ("work", "Work"),
        ("family", "Friends & Family"),
        ("other", "Other"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
    session_key = models.CharField(max_length=40, blank=True)
    label = models.CharField(max_length=20, choices=LABEL_CHOICES, default="home")
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120)
    state = models.CharField(max_length=120)
    pincode = models.CharField(max_length=10)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_default", "-updated_at"]

    def __str__(self):
        return f"{self.name} - {self.pincode}"


class CheckoutOrder(models.Model):
    STATUS_CHOICES = [
        ("created", "Created"),
        ("paid", "Paid"),
        ("failed", "Failed"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
    session_key = models.CharField(max_length=40, blank=True)
    address = models.ForeignKey(CheckoutAddress, on_delete=models.SET_NULL, null=True, blank=True)
    amount_paise = models.PositiveIntegerField()
    currency = models.CharField(max_length=10, default="INR")
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="created")
    items = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.razorpay_order_id


class CheckoutPayment(models.Model):
    STATUS_CHOICES = [
        ("captured", "Captured"),
        ("failed", "Failed"),
    ]
    order = models.ForeignKey(CheckoutOrder, on_delete=models.CASCADE, related_name="payments")
    razorpay_payment_id = models.CharField(max_length=100, unique=True)
    razorpay_signature = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="captured")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.razorpay_payment_id
