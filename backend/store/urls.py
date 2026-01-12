from django.urls import path
from .views import home_view, category_view, product_detail_view,  product_search_view, cart_view


urlpatterns = [
    path('', home_view, name='home'),
    path('category/<slug:slug>/', category_view, name='category'),
    path('product/<slug:slug>/', product_detail_view, name='product_detail'),
    path('search/', product_search_view, name='product_search'),
    path('cart/', cart_view, name='cart'),
]
