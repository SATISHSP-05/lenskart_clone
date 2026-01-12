from django.shortcuts import render
from .models import Banner, Category, Product
from django.http import HttpResponse

def home_view(request):
    banners = Banner.objects.filter(active=True).order_by('order')[:5]
    categories = Category.objects.filter(active=True)
    featured_products = Product.objects.filter(active=True).order_by('-created_at')[:12]

    context = {
        'banners': banners,
        'categories': categories,
        'featured_products': featured_products,
    }
    return render(request, 'store/home.html', context)



from django.shortcuts import get_object_or_404

def category_view(request, slug):
    category = get_object_or_404(Category, slug=slug, active=True)
    
    products = category.products.filter(active=True)

    # pagination (12 per page)
    from django.core.paginator import Paginator
    paginator = Paginator(products, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, 'store/category.html', context)


def product_detail_view(request, slug):
    return HttpResponse("Product detail page coming soon")


def product_search_view(request):
    query = request.GET.get('q', '').strip()
    products = Product.objects.filter(active=True)

    if query:
        products = products.filter(name__icontains=query)

    # pagination
    from django.core.paginator import Paginator
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'query': query,
        'page_obj': page_obj,
    }
    return render(request, 'store/search_results.html', context)

def cart_view(request):
    return HttpResponse("Cart page coming soon!")