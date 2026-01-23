from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import get_object_or_404, redirect, render

import razorpay

from store.models import Product
from .models import CheckoutAddress, CheckoutOrder, CheckoutPayment


def _get_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def _get_cart_slugs(request):
    cart_items = request.session.get("cart_items", [])
    return [slug for slug in cart_items if slug]


def _get_cart_products(cart_items):
    products = Product.objects.filter(slug__in=cart_items, is_active=True).select_related("brand")
    product_map = {item.slug: item for item in products}
    return [product_map[slug] for slug in cart_items if slug in product_map]


def cart_view(request):
    cart_items = request.session.get("cart_items", [])
    wishlist_items = request.session.get("wishlist_items", [])

    action = request.GET.get("action")
    product_slug = request.GET.get("product") or request.GET.get("add")

    if product_slug:
        try:
            product = get_object_or_404(Product, slug=product_slug, is_active=True)
        except Exception:
            product = None
        if product:
            if action == "remove":
                if product_slug in cart_items:
                    cart_items.remove(product_slug)
            elif action == "move_to_wishlist":
                if product_slug in cart_items:
                    cart_items.remove(product_slug)
                wishlist_items.append(product_slug)
            else:
                cart_items.append(product_slug)

            request.session["cart_items"] = cart_items
            request.session["wishlist_items"] = wishlist_items
            request.session.modified = True

            if action in (None, "", "remove", "move_to_wishlist", "repeat") or request.GET.get("add"):
                return redirect("cart")

    ordered_cart = _get_cart_products(cart_items)

    wishlist_products = Product.objects.filter(slug__in=wishlist_items, is_active=True).select_related("brand")
    wishlist_map = {item.slug: item for item in wishlist_products}
    ordered_wishlist = [wishlist_map[slug] for slug in wishlist_items if slug in wishlist_map]

    total = sum([item.get_display_price() for item in ordered_cart]) if ordered_cart else 0

    context = {
        "cart_items": ordered_cart,
        "wishlist_items": ordered_wishlist,
        "total_price": total,
    }
    return render(request, "cart/cart.html", context)


def checkout_address_view(request):
    session_key = _get_session_key(request)
    if request.user.is_authenticated:
        addresses = CheckoutAddress.objects.filter(user=request.user)
    else:
        addresses = CheckoutAddress.objects.filter(session_key=session_key)

    selected_id = request.session.get("checkout_address_id")

    if request.method == "POST":
        selected_id = request.POST.get("address_id")
        if selected_id:
            address = get_object_or_404(addresses, id=selected_id)
            request.session["checkout_address_id"] = address.id
            return redirect("checkout_payment")

    cart_slugs = _get_cart_slugs(request)
    cart_products = _get_cart_products(cart_slugs)
    total = sum([item.get_display_price() for item in cart_products]) if cart_products else 0

    return render(
        request,
        "cart/checkout_address.html",
        {
            "addresses": addresses,
            "selected_id": selected_id,
            "total_price": total,
        },
    )


def checkout_address_form_view(request, address_id=None):
    session_key = _get_session_key(request)
    address = None
    if address_id:
        if request.user.is_authenticated:
            address = get_object_or_404(CheckoutAddress, id=address_id, user=request.user)
        else:
            address = get_object_or_404(CheckoutAddress, id=address_id, session_key=session_key)

    if request.method == "POST":
        payload = {
            "label": request.POST.get("label", "home"),
            "name": request.POST.get("name", "").strip(),
            "phone": request.POST.get("phone", "").strip(),
            "email": request.POST.get("email", "").strip(),
            "address_line1": request.POST.get("address_line1", "").strip(),
            "address_line2": request.POST.get("address_line2", "").strip(),
            "city": request.POST.get("city", "").strip(),
            "state": request.POST.get("state", "").strip(),
            "pincode": request.POST.get("pincode", "").strip(),
        }
        set_default = request.POST.get("is_default") == "on"

        if address:
            for key, value in payload.items():
                setattr(address, key, value)
        else:
            address = CheckoutAddress(**payload)
            if request.user.is_authenticated:
                address.user = request.user
            else:
                address.session_key = session_key

        address.is_default = set_default
        address.save()

        if set_default:
            filter_kwargs = {}
            if request.user.is_authenticated:
                filter_kwargs["user"] = address.user
            else:
                filter_kwargs["session_key"] = address.session_key
            CheckoutAddress.objects.filter(**filter_kwargs).exclude(id=address.id).update(is_default=False)

        request.session["checkout_address_id"] = address.id
        return redirect("checkout_payment")

    cart_slugs = _get_cart_slugs(request)
    cart_products = _get_cart_products(cart_slugs)
    total = sum([item.get_display_price() for item in cart_products]) if cart_products else 0

    return render(
        request,
        "cart/checkout_address_form.html",
        {
            "address": address,
            "label_choices": CheckoutAddress.LABEL_CHOICES,
            "total_price": total,
        },
    )


def checkout_address_delete_view(request, address_id):
    session_key = _get_session_key(request)
    if request.user.is_authenticated:
        address = get_object_or_404(CheckoutAddress, id=address_id, user=request.user)
    else:
        address = get_object_or_404(CheckoutAddress, id=address_id, session_key=session_key)

    if request.method == "POST":
        if request.session.get("checkout_address_id") == address.id:
            request.session.pop("checkout_address_id", None)
        address.delete()
    return redirect("checkout_address")


@ensure_csrf_cookie
def checkout_payment_view(request):
    session_key = _get_session_key(request)
    address_id = request.session.get("checkout_address_id")
    if not address_id:
        return redirect("checkout_address")

    if request.user.is_authenticated:
        address = get_object_or_404(CheckoutAddress, id=address_id, user=request.user)
    else:
        address = get_object_or_404(CheckoutAddress, id=address_id, session_key=session_key)

    cart_slugs = _get_cart_slugs(request)
    cart_products = _get_cart_products(cart_slugs)
    total = sum([item.get_display_price() for item in cart_products]) if cart_products else 0

    return render(
        request,
        "cart/checkout_payment.html",
        {
            "address": address,
            "total_price": total,
            "cart_items": cart_products,
            "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        },
    )


def checkout_payment_create_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed."}, status=405)

    session_key = _get_session_key(request)
    address_id = request.session.get("checkout_address_id")
    if not address_id:
        return JsonResponse({"error": "No address selected."}, status=400)

    if request.user.is_authenticated:
        address = get_object_or_404(CheckoutAddress, id=address_id, user=request.user)
    else:
        address = get_object_or_404(CheckoutAddress, id=address_id, session_key=session_key)

    cart_slugs = _get_cart_slugs(request)
    cart_products = _get_cart_products(cart_slugs)
    total = sum([item.get_display_price() for item in cart_products]) if cart_products else 0
    if total <= 0:
        return JsonResponse({"error": "Cart is empty."}, status=400)

    amount_paise = int(total * 100)
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        return JsonResponse({"error": "Razorpay keys are not configured."}, status=500)

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    receipt = f"rcpt_{session_key[-8:]}"
    try:
        order = client.order.create(
            {
                "amount": amount_paise,
                "currency": "INR",
                "receipt": receipt,
                "payment_capture": 1,
            }
        )
    except Exception as exc:
        return JsonResponse({"error": f"Unable to create Razorpay order: {exc}"}, status=502)

    items = [{"slug": item.slug, "name": item.name, "price": str(item.get_display_price())} for item in cart_products]
    CheckoutOrder.objects.create(
        user=request.user if request.user.is_authenticated else None,
        session_key=session_key,
        address=address,
        amount_paise=amount_paise,
        currency=order.get("currency", "INR"),
        razorpay_order_id=order["id"],
        status="created",
        items=items,
    )

    return JsonResponse(
        {
            "order_id": order["id"],
            "amount": amount_paise,
            "currency": "INR",
            "name": "Lenskart",
            "prefill": {
                "name": address.name,
                "email": address.email,
                "contact": address.phone,
            },
        }
    )


def checkout_payment_verify_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed."}, status=405)

    razorpay_order_id = request.POST.get("razorpay_order_id", "")
    razorpay_payment_id = request.POST.get("razorpay_payment_id", "")
    razorpay_signature = request.POST.get("razorpay_signature", "")

    if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
        return render(request, "cart/checkout_payment_result.html", {"success": False})

    order = get_object_or_404(CheckoutOrder, razorpay_order_id=razorpay_order_id)
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    try:
        client.utility.verify_payment_signature(
            {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            }
        )
    except razorpay.errors.SignatureVerificationError:
        order.status = "failed"
        order.save(update_fields=["status"])
        return render(request, "cart/checkout_payment_result.html", {"success": False})

    CheckoutPayment.objects.get_or_create(
        order=order,
        razorpay_payment_id=razorpay_payment_id,
        defaults={
            "razorpay_signature": razorpay_signature,
            "status": "captured",
        },
    )
    order.status = "paid"
    order.save(update_fields=["status"])

    request.session["cart_items"] = []
    request.session.modified = True
    request.session["checkout_order_id"] = order.id

    return redirect("checkout_summary")


def checkout_summary_view(request):
    session_key = _get_session_key(request)
    order_id = request.session.get("checkout_order_id")
    if not order_id:
        return redirect("cart")

    if request.user.is_authenticated:
        order = get_object_or_404(CheckoutOrder, id=order_id, user=request.user)
    else:
        order = get_object_or_404(CheckoutOrder, id=order_id, session_key=session_key)

    return render(
        request,
        "cart/checkout_summary.html",
        {
            "order": order,
            "address": order.address,
            "total_price": order.amount_paise / 100,
        },
    )


def order_detail_view(request, order_id):
    session_key = _get_session_key(request)
    if request.user.is_authenticated:
        order = get_object_or_404(CheckoutOrder, id=order_id, user=request.user)
    else:
        order = get_object_or_404(CheckoutOrder, id=order_id, session_key=session_key)

    return render(
        request,
        "cart/checkout_summary.html",
        {
            "order": order,
            "address": order.address,
            "total_price": order.amount_paise / 100,
        },
    )


def track_orders_view(request):
    session_key = _get_session_key(request)
    if request.user.is_authenticated:
        orders = CheckoutOrder.objects.filter(user=request.user).order_by("-created_at")
    else:
        orders = CheckoutOrder.objects.filter(session_key=session_key).order_by("-created_at")

    order_rows = []
    for order in orders:
        order_rows.append(
            {
                "order": order,
                "total_price": order.amount_paise / 100,
            }
        )

    return render(
        request,
        "cart/track_orders.html",
        {
            "order_rows": order_rows,
        },
    )
