from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api_views import (
    BannerViewSet,
    BrandViewSet,
    CategoryViewSet,
    ProductImageViewSet,
    ProductViewSet,
)
from .views import (
    home_view,
    category_view,
    product_detail_view,
    product_search_view,
    cart_view,
    shape_gender_view,
    around_view,
)


router = DefaultRouter()
router.register("banners", BannerViewSet)
router.register("brands", BrandViewSet)
router.register("categories", CategoryViewSet)
router.register("products", ProductViewSet)
router.register("product-images", ProductImageViewSet)


urlpatterns = [
    path('', home_view, name='home'),
    path('category/<slug:slug>/', category_view, name='category'),
    path('eyeglasses/frame-shape/<slug:shape>/<slug:gender>/', shape_gender_view, name='shape_gender'),
    path('product/<slug:slug>/', product_detail_view, name='product_detail'),
    path('search/', product_search_view, name='product_search'),
    path('cart/', cart_view, name='cart'),
    path('around/', around_view, name='around'),
    path('api/', include(router.urls)),
]
