import random
import re
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from twilio.rest import Client

from .models import OTPCode, Prescription, StoreCredit, UserProfile
from orders.models import Order


def _normalize_phone(value):
    digits = re.sub(r"[^\d+]", "", value)
    if not digits.startswith("+"):
        digits = f"+{digits}"
    return digits


def _generate_otp():
    length = int(getattr(settings, "OTP_LENGTH", 6))
    return str(random.randint(10 ** (length - 1), (10 ** length) - 1))


@api_view(["POST"])
@permission_classes([AllowAny])
def request_otp_view(request):
    identifier = str(request.data.get("identifier", "")).strip()
    whatsapp_opt_in = bool(request.data.get("whatsapp_opt_in", False))
    first_name = str(request.data.get("first_name", "")).strip()
    last_name = str(request.data.get("last_name", "")).strip()
    if not identifier:
        return Response({"detail": "Identifier required."}, status=400)

    channel = "email" if "@" in identifier else "phone"
    if channel == "phone":
        identifier = _normalize_phone(identifier)

    code = _generate_otp()
    expires_at = timezone.now() + timedelta(minutes=int(getattr(settings, "OTP_EXPIRY_MINUTES", 5)))
    OTPCode.objects.create(
        identifier=identifier,
        channel=channel,
        code=code,
        expires_at=expires_at,
    )
    request.session["whatsapp_opt_in"] = whatsapp_opt_in
    request.session["pending_first_name"] = first_name
    request.session["pending_last_name"] = last_name

    if channel == "phone":
        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
            return Response({"detail": "SMS provider not configured."}, status=500)
        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=f"Your Lenskart OTP is {code}",
                from_=settings.TWILIO_FROM_NUMBER,
                to=identifier,
            )
        except Exception as exc:
            return Response({"detail": f"Failed to send SMS OTP: {exc}"}, status=500)
    else:
        if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            return Response({"detail": "Email provider not configured."}, status=500)
        try:
            send_mail(
                subject="Your Lenskart OTP",
                message=f"Your Lenskart OTP is {code}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[identifier],
                fail_silently=False,
            )
        except Exception as exc:
            return Response({"detail": f"Failed to send email OTP: {exc}"}, status=500)

    return Response({"detail": "OTP sent.", "channel": channel})


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_otp_view(request):
    identifier = str(request.data.get("identifier", "")).strip()
    code = str(request.data.get("code", "")).strip()
    if not identifier or not code:
        return Response({"detail": "Identifier and code required."}, status=400)

    channel = "email" if "@" in identifier else "phone"
    if channel == "phone":
        identifier = _normalize_phone(identifier)

    otp = (
        OTPCode.objects.filter(identifier=identifier, channel=channel, verified=False)
        .order_by("-created_at")
        .first()
    )
    if not otp or otp.code != code:
        return Response({"detail": "Invalid OTP."}, status=400)
    if otp.is_expired():
        return Response({"detail": "OTP expired."}, status=400)

    otp.verified = True
    otp.save(update_fields=["verified"])

    user = None
    if channel == "email":
        user = User.objects.filter(email__iexact=identifier).first()
        if not user:
            username = identifier.split("@", 1)[0]
            if User.objects.filter(username=username).exists():
                username = f"{username}_{random.randint(1000, 9999)}"
            user = User.objects.create_user(username=username, email=identifier)
    else:
        profile = UserProfile.objects.filter(phone=identifier).select_related("user").first()
        if profile:
            user = profile.user
        else:
            username = f"user_{identifier[-6:]}"
            if User.objects.filter(username=username).exists():
                username = f"{username}_{random.randint(1000, 9999)}"
            user = User.objects.create_user(username=username)
            UserProfile.objects.create(user=user, phone=identifier)

    opt_in = bool(request.session.pop("whatsapp_opt_in", False))
    pending_first = str(request.session.pop("pending_first_name", "")).strip()
    pending_last = str(request.session.pop("pending_last_name", "")).strip()
    profile, _ = UserProfile.objects.get_or_create(user=user)
    if opt_in and not profile.whatsapp_opt_in:
        profile.whatsapp_opt_in = True
        if channel == "phone" and identifier:
            profile.phone = identifier
        profile.save(update_fields=["whatsapp_opt_in", "phone"])

    if pending_first and not user.first_name:
        user.first_name = pending_first
    if pending_last and not user.last_name:
        user.last_name = pending_last
    if pending_first or pending_last:
        user.save(update_fields=["first_name", "last_name"])

    login(request, user)

    refresh = RefreshToken.for_user(user)
    return Response(
        {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "username": user.username,
        }
    )


@login_required
def my_orders_view(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "accounts/my_orders.html", {"orders": orders})


@login_required
def my_prescriptions_view(request):
    prescriptions = Prescription.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "accounts/my_prescriptions.html", {"prescriptions": prescriptions})


@login_required
def store_credit_view(request):
    credits = StoreCredit.objects.filter(user=request.user)
    return render(request, "accounts/store_credit.html", {"credits": credits})


@login_required
def account_info_view(request):
    profile = UserProfile.objects.filter(user=request.user).first()
    return render(request, "accounts/account_information.html", {"profile": profile})


def logout_view(request):
    logout(request)
    return redirect("home")
