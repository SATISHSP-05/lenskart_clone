from django.conf import settings
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    whatsapp_opt_in = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class OTPCode(models.Model):
    CHANNEL_CHOICES = [
        ("phone", "Phone"),
        ("email", "Email"),
    ]
    identifier = models.CharField(max_length=255)
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES)
    code = models.CharField(max_length=10)
    expires_at = models.DateTimeField()
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.identifier} ({self.channel})"


class Prescription(models.Model):
    POWER_CHOICES = [
        ("single", "Single Vision"),
        ("progressive", "Progressive"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    power_type = models.CharField(max_length=20, choices=POWER_CHOICES)
    right_sph = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    left_sph = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    right_cyl = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    left_cyl = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    axis = models.IntegerField(null=True, blank=True)
    pd = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class StoreCredit(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(max_length=50, unique=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.code}"
