import json
import re
from datetime import timedelta
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import ssl

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from .models import Banner, Brand, Category, DeliveryPincode, Product, HtoAddress


def home_view(request):
    banners = Banner.objects.filter(active=True, banner_type='hero').order_by('order')[:5]
    categories = Category.objects.filter(active=True)
    trending_products = Product.objects.filter(is_active=True, is_trending=True).order_by('-created_at')[:12]
    premium_products = Product.objects.filter(is_active=True, is_premium=True).order_by('-created_at')[:12]
    exclusive_products = Product.objects.filter(is_active=True, is_exclusive=True).order_by('-created_at')[:12]
    coupon_banner = Banner.objects.filter(active=True, banner_type='coupon').order_by('order').first()
    replacement_banner = Banner.objects.filter(active=True, banner_type='replacement').order_by('order').first()
    buy1get1_banner = Banner.objects.filter(active=True, banner_type='buy1get1').order_by('order').first()
    exclusive_banner = Banner.objects.filter(active=True, banner_type='exclusive').order_by('order').first()
    exclusive_banners = Banner.objects.filter(active=True, banner_type='exclusive').order_by('order')
    premium_banner = Banner.objects.filter(active=True, banner_type='premium').order_by('order').first()

    context = {
        'banners': banners,
        'categories': categories,
        'trending_products': trending_products,
        'premium_products': premium_products,
        'exclusive_products': exclusive_products,
        'coupon_banner': coupon_banner,
        'replacement_banner': replacement_banner,
        'buy1get1_banner': buy1get1_banner,
        'exclusive_banner': exclusive_banner,
        'exclusive_banners': exclusive_banners,
        'premium_banner': premium_banner,
        'shape_choices': Product.SHAPE_CHOICES,
    }
    return render(request, 'store/home.html', context)


PINCODE_RE = re.compile(r"^[1-9][0-9]{5}$")


def _format_delivery_date(days):
    delivery_date = timezone.localdate() + timedelta(days=days)
    return delivery_date.strftime("%a %b %d %Y")


def _pincode_payload(record):
    return {
        "pincode": record.pincode,
        "city": record.city,
        "state": record.state,
        "delivery_days": record.delivery_days,
        "delivery_date": _format_delivery_date(record.delivery_days),
        "source": record.source,
    }


def _fetch_external_pincode(pin):
    api_template = getattr(settings, "PINCODE_API_URL", "")
    if not api_template:
        return None, "External pincode service not configured."
    url = api_template.format(pincode=pin)
    request = Request(url, headers={"User-Agent": "lenskart-ecommerce/1.0"})
    verify_ssl = getattr(settings, "PINCODE_VERIFY_SSL", True)
    context = ssl.create_default_context() if verify_ssl else ssl._create_unverified_context()
    try:
        with urlopen(request, timeout=5, context=context) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (URLError, HTTPError, ValueError) as exc:
        return None, f"External pincode lookup failed: {exc}"

    if not payload or not isinstance(payload, list):
        return None, "External pincode response invalid."
    entry = payload[0] or {}
    if entry.get("Status") != "Success":
        return None, "Pincode not serviceable."
    post_offices = entry.get("PostOffice") or []
    if not post_offices:
        return None, "Pincode not serviceable."
    office = post_offices[0] or {}
    return {
        "city": office.get("District") or office.get("Block") or "",
        "state": office.get("State") or "",
    }, None


def pincode_check_view(request):
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed."}, status=405)

    pin = (request.GET.get("pincode") or "").strip()
    if not PINCODE_RE.match(pin):
        return JsonResponse({"error": "Please enter a valid 6 digit pincode."}, status=400)

    record = DeliveryPincode.objects.filter(pincode=pin, active=True).first()
    if record:
        return JsonResponse(_pincode_payload(record))

    external_data, error = _fetch_external_pincode(pin)
    if error:
        status = 404 if error == "Pincode not serviceable." else 502
        return JsonResponse({"error": error}, status=status)

    delivery_days = getattr(settings, "PINCODE_DEFAULT_DELIVERY_DAYS", 3)
    record, _ = DeliveryPincode.objects.update_or_create(
        pincode=pin,
        defaults={
            "city": external_data.get("city", ""),
            "state": external_data.get("state", ""),
            "delivery_days": delivery_days,
            "active": True,
            "source": "external",
            "last_checked": timezone.now(),
        },
    )
    return JsonResponse(_pincode_payload(record))


def _build_filtered_products(request, base_products, fixed_shapes=None, fixed_genders=None):
    filter_base = base_products

    price_ranges = [
        ("1500-1999", 1500, 1999),
        ("2500-2999", 2500, 2999),
        ("3500-3999", 3500, 3999),
        ("4500-4999", 4500, 4999),
        ("6500-6999", 6500, 6999),
    ]

    selected_brands = request.GET.getlist("brand")
    selected_shapes = request.GET.getlist("shape")
    selected_frame_types = request.GET.getlist("frame_type")
    selected_colors = request.GET.getlist("color")
    selected_sizes = request.GET.getlist("size")
    selected_prices = request.GET.getlist("price")
    selected_genders = request.GET.getlist("gender")
    selected_materials = request.GET.getlist("material")
    selected_weights = request.GET.getlist("weight_group")

    if fixed_shapes:
        selected_shapes = list(fixed_shapes)
    if fixed_genders:
        selected_genders = list(fixed_genders)

    products = filter_base
    if selected_brands:
        products = products.filter(brand__slug__in=selected_brands)
    if selected_shapes:
        products = products.filter(shape__in=selected_shapes)
    if selected_frame_types:
        products = products.filter(frame_type__in=selected_frame_types)
    if selected_genders:
        products = products.filter(gender__in=selected_genders)
    if selected_materials:
        products = products.filter(frame_material__in=selected_materials)
    if selected_colors:
        products = products.filter(color__in=selected_colors)
    if selected_sizes:
        products = products.filter(size__in=selected_sizes)
    if selected_weights:
        products = products.filter(weight_group__in=selected_weights)
    if selected_prices:
        price_q = Q()
        for key in selected_prices:
            for label, min_price, max_price in price_ranges:
                if key == label:
                    price_q |= Q(base_price__gte=min_price, base_price__lte=max_price)
        if price_q:
            products = products.filter(price_q)

    products = products.order_by("id")

    products = products.order_by("id")

    available_shapes = set(filter_base.values_list("shape", flat=True))
    available_frame_types = set(filter_base.values_list("frame_type", flat=True))
    available_genders = set(filter_base.values_list("gender", flat=True))
    available_materials = sorted(
        {value for value in filter_base.values_list("frame_material", flat=True) if value}
    )
    available_colors = sorted({value for value in filter_base.values_list("color", flat=True) if value})
    available_sizes = set(filter_base.values_list("size", flat=True))
    available_weights = set(filter_base.values_list("weight_group", flat=True))

    shape_choices = [(value, label) for value, label in Product.SHAPE_CHOICES if value in available_shapes]
    frame_type_choices = [
        (value, label) for value, label in Product.FRAME_TYPE_CHOICES if value in available_frame_types
    ]
    gender_choices = [(value, label) for value, label in Product.GENDER_CHOICES if value in available_genders]
    size_choices = [
        (value, label)
        for value, label in Product.SIZE_CHOICES
        if value in available_sizes
    ]
    weight_choices = [
        (value, label)
        for value, label in Product.WEIGHT_CHOICES
        if value in available_weights
    ]
    brands = Brand.objects.filter(active=True, products__in=filter_base).distinct()

    filter_params = request.GET.copy()
    filter_params.pop("page", None)

    context = {
        "brands": brands,
        "shape_choices": shape_choices,
        "frame_type_choices": frame_type_choices,
        "gender_choices": gender_choices,
        "material_choices": available_materials,
        "color_choices": available_colors,
        "size_choices": size_choices,
        "weight_choices": weight_choices,
        "price_choices": price_ranges,
        "selected_brands": selected_brands,
        "selected_shapes": selected_shapes,
        "selected_frame_types": selected_frame_types,
        "selected_genders": selected_genders,
        "selected_materials": selected_materials,
        "selected_colors": selected_colors,
        "selected_sizes": selected_sizes,
        "selected_weights": selected_weights,
        "selected_prices": selected_prices,
        "filter_query": filter_params.urlencode(),
    }
    return products, context


def category_view(request, slug):
    category = get_object_or_404(Category, slug=slug, active=True)

    products = category.products.filter(is_active=True)
    filter_base = products

    price_ranges = [
        ("1500-1999", 1500, 1999),
        ("2500-2999", 2500, 2999),
        ("3500-3999", 3500, 3999),
        ("4500-4999", 4500, 4999),
        ("6500-6999", 6500, 6999),
    ]

    selected_brands = request.GET.getlist("brand")
    selected_shapes = request.GET.getlist("shape")
    selected_frame_types = request.GET.getlist("frame_type")
    selected_colors = request.GET.getlist("color")
    selected_sizes = request.GET.getlist("size")
    selected_prices = request.GET.getlist("price")
    selected_genders = request.GET.getlist("gender")
    selected_materials = request.GET.getlist("material")
    selected_weights = request.GET.getlist("weight_group")

    if selected_brands:
        products = products.filter(brand__slug__in=selected_brands)
    if selected_shapes:
        products = products.filter(shape__in=selected_shapes)
    if selected_frame_types:
        products = products.filter(frame_type__in=selected_frame_types)
    if selected_genders:
        products = products.filter(gender__in=selected_genders)
    if selected_materials:
        products = products.filter(frame_material__in=selected_materials)
    if selected_colors:
        products = products.filter(color__in=selected_colors)
    if selected_sizes:
        products = products.filter(size__in=selected_sizes)
    if selected_weights:
        products = products.filter(weight_group__in=selected_weights)
    if selected_prices:
        price_q = Q()
        for key in selected_prices:
            for label, min_price, max_price in price_ranges:
                if key == label:
                    price_q |= Q(base_price__gte=min_price, base_price__lte=max_price)
        if price_q:
            products = products.filter(price_q)

    paginator = Paginator(products, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    available_shapes = set(filter_base.values_list("shape", flat=True))
    available_frame_types = set(filter_base.values_list("frame_type", flat=True))
    available_genders = set(filter_base.values_list("gender", flat=True))
    available_materials = sorted(
        {value for value in filter_base.values_list("frame_material", flat=True) if value}
    )
    available_colors = sorted({value for value in filter_base.values_list("color", flat=True) if value})
    available_sizes = set(filter_base.values_list("size", flat=True))
    available_weights = set(filter_base.values_list("weight_group", flat=True))

    shape_choices = [(value, label) for value, label in Product.SHAPE_CHOICES if value in available_shapes]
    frame_type_choices = [
        (value, label) for value, label in Product.FRAME_TYPE_CHOICES if value in available_frame_types
    ]
    gender_choices = [(value, label) for value, label in Product.GENDER_CHOICES if value in available_genders]
    size_choices = [
        (value, label)
        for value, label in Product.SIZE_CHOICES
        if value in available_sizes
    ]
    weight_choices = [
        (value, label)
        for value, label in Product.WEIGHT_CHOICES
        if value in available_weights
    ]
    brands = Brand.objects.filter(active=True, products__in=filter_base).distinct()

    filter_params = request.GET.copy()
    filter_params.pop("page", None)

    context = {
        'category': category,
        'page_obj': page_obj,
        'brands': brands,
        'shape_choices': shape_choices,
        'frame_type_choices': frame_type_choices,
        'gender_choices': gender_choices,
        'material_choices': available_materials,
        'color_choices': available_colors,
        'size_choices': size_choices,
        'weight_choices': weight_choices,
        'price_choices': price_ranges,
        'selected_brands': selected_brands,
        'selected_shapes': selected_shapes,
        'selected_frame_types': selected_frame_types,
        'selected_genders': selected_genders,
        'selected_materials': selected_materials,
        'selected_colors': selected_colors,
        'selected_sizes': selected_sizes,
        'selected_weights': selected_weights,
        'selected_prices': selected_prices,
        'filter_query': filter_params.urlencode(),
    }
    return render(request, 'store/category.html', context)


def product_detail_view(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    product_images = product.images.all()

    context = {
        'product': product,
        'product_images': product_images,
    }
    return render(request, 'store/product_detail.html', context)


def shape_gender_view(request, shape, gender):
    category_slug = request.GET.get("category")
    base_products = Product.objects.filter(is_active=True, shape=shape, gender=gender)
    if category_slug:
        base_products = base_products.filter(category__slug=category_slug)
    products, filter_context = _build_filtered_products(
        request,
        base_products,
        fixed_shapes=[shape],
        fixed_genders=[gender],
    )
    paginator = Paginator(products, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    shape_label = dict(Product.SHAPE_CHOICES).get(shape, shape)
    gender_label = dict(Product.GENDER_CHOICES).get(gender, gender)
    category = None
    if category_slug:
        category = Category.objects.filter(slug=category_slug, active=True).first()
    if not category:
        category = Category.objects.filter(slug="eyeglasses", active=True).first()
    category_label = category.name if category else "Eyeglasses"

    context = {
        "category": category,
        "page_obj": page_obj,
        "page_title": f"{shape_label} {category_label} for {gender_label}",
        "category_label": category_label,
        "shape_label": shape_label,
        "gender_label": gender_label,
        "shape_value": shape,
        "gender_value": gender,
        "tryon_enabled": request.GET.get("tryon") == "1",
    }
    context.update(filter_context)
    return render(request, "store/shape_listing.html", context)


def product_search_view(request):
    query = request.GET.get('q', '').strip()
    products = Product.objects.filter(is_active=True)

    if query:
        terms = [term for term in query.split() if term]
        query_q = Q()
        for term in terms:
            query_q |= Q(name__icontains=term)
            query_q |= Q(brand__name__icontains=term)
            query_q |= Q(category__name__icontains=term)
            query_q |= Q(shape__icontains=term)
            query_q |= Q(gender__icontains=term)
            query_q |= Q(frame_type__icontains=term)
            query_q |= Q(frame_material__icontains=term)
            query_q |= Q(color__icontains=term)
        products = products.filter(query_q)

    brand_slug = request.GET.get("brand")
    shape = request.GET.get("shape")
    gender = request.GET.get("gender")
    if brand_slug:
        products = products.filter(brand__slug=brand_slug)
    if shape:
        products = products.filter(shape=shape)
    if gender:
        products = products.filter(gender=gender)

    products = products.order_by("id")

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'query': query,
        'page_obj': page_obj,
        'brands': Brand.objects.filter(active=True),
        'selected_brand': brand_slug,
        'selected_shape': shape,
        'selected_gender': gender,
        'shape_choices': Product.SHAPE_CHOICES,
    }
    return render(request, 'store/search_results.html', context)


def cart_view(request):
    return HttpResponse("Cart page coming soon!")


def around_view(request):
    return render(request, "store/around.html")


def home_eye_test_view(request):
    return render(request, "store/home_eye_test.html")


def hto_address_view(request):
    addresses = list(
        HtoAddress.objects.all().values(
            "id",
            "name",
            "phone",
            "address_line",
            "city",
            "state",
            "pincode",
        )
    )
    return render(request, "store/hto_address.html", {"addresses": addresses})


def hto_new_location_view(request):
    return render(request, "store/hto_new_location.html")


def hto_location_unavailable_view(request):
    return render(request, "store/hto_location_unavailable.html")


def hto_explore_frames_view(request):
    return render(request, "store/hto_explore_frames.html")


def hto_date_time_view(request):
    return render(request, "store/hto_date_time.html")


def hto_confirm_view(request):
    return render(request, "store/hto_confirm.html")


def promo_jj_stranger_things_view(request):
    base_products = Product.objects.filter(is_active=True)
    products, filter_context = _build_filtered_products(request, base_products)
    paginator = Paginator(products, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "page_title": "JJ x Stranger Things",
        "category_label": "Eyewear",
        "tryon_enabled": request.GET.get("tryon") == "1",
    }
    context.update(filter_context)
    return render(request, "store/promo_jj_stranger_things.html", context)


def brand_listing_view(request, slug):
    brand = get_object_or_404(Brand, slug=slug, active=True)
    base_products = Product.objects.filter(is_active=True, brand=brand)
    products, filter_context = _build_filtered_products(request, base_products)
    paginator = Paginator(products, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    filter_context["selected_brands"] = [brand.slug]

    context = {
        "brand": brand,
        "page_obj": page_obj,
        "page_title": brand.name,
        "category_label": "Eyewear",
        "tryon_enabled": request.GET.get("tryon") == "1",
    }
    context.update(filter_context)
    return render(request, "store/brand_listing.html", context)


def promo_collection_view(request, slug, title, keyword):
    base_products = Product.objects.filter(is_active=True).filter(
        Q(name__icontains=keyword)
        | Q(category__name__icontains=keyword)
        | Q(brand__name__icontains=keyword)
    )
    products, filter_context = _build_filtered_products(request, base_products)
    paginator = Paginator(products, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "page_title": title,
        "category_label": "Eyewear",
        "tryon_enabled": request.GET.get("tryon") == "1",
        "promo_slug": slug,
    }
    context.update(filter_context)
    return render(request, "store/promo_collection_listing.html", context)


def promo_all_switch_view(request):
    return promo_collection_view(request, "all-switch", "All Switch", "switch")


def promo_air_x_view(request):
    return promo_collection_view(request, "air-x", "Air X", "air")


def promo_transparent_view(request):
    return promo_collection_view(request, "transparents-eyeglasses", "Transparent Eyeglasses", "transparent")
