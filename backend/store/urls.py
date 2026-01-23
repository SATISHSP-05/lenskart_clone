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
    shape_gender_view,
    around_view,
    home_eye_test_view,
    hto_address_view,
    hto_new_location_view,
    hto_location_unavailable_view,
    hto_explore_frames_view,
    hto_date_time_view,
    hto_confirm_view,
    promo_jj_stranger_things_view,
    brand_listing_view,
    promo_all_switch_view,
    promo_air_x_view,
    promo_transparent_view,
    pincode_check_view,
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
    path('around/', around_view, name='around'),
    path('home-eye-test/', home_eye_test_view, name='home_eye_test'),
    path('home-eye-test/address/', hto_address_view, name='hto_address'),
    path('home-eye-test/new-location/', hto_new_location_view, name='hto_new_location'),
    path('home-eye-test/location-unavailable/', hto_location_unavailable_view, name='hto_location_unavailable'),
    path('home-eye-test/explore-frames/', hto_explore_frames_view, name='hto_explore_frames'),
    path('home-eye-test/date-time/', hto_date_time_view, name='hto_date_time'),
    path('home-eye-test/confirm/', hto_confirm_view, name='hto_confirm'),
    path('stores-lenskart/', hto_explore_frames_view, name='stores_lenskart'),
    path('jj-x-stranger-things.html', promo_jj_stranger_things_view, name='promo_jj_stranger_things'),
    path('brands/<slug:slug>.html', brand_listing_view, name='brand_listing'),
    path('all-switch.html', promo_all_switch_view, name='promo_all_switch'),
    path('air-x.html', promo_air_x_view, name='promo_air_x'),
    path('transparents-eyeglasses.html', promo_transparent_view, name='promo_transparent'),
    path('api/pincode-check/', pincode_check_view, name='pincode_check'),
    path('api/', include(router.urls)),
]
