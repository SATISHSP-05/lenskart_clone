from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    account_info_view,
    my_orders_view,
    my_prescriptions_view,
    request_otp_view,
    store_credit_view,
    verify_otp_view,
    logout_view,
)

urlpatterns = [
    path('my-orders/', my_orders_view, name='my_orders'),
    path('my-prescriptions/', my_prescriptions_view, name='my_prescriptions'),
    path('store-credit/', store_credit_view, name='store_credit'),
    path('account-information/', account_info_view, name='account_information'),
    path('api/auth/request-otp/', request_otp_view, name='request_otp'),
    path('api/auth/verify-otp/', verify_otp_view, name='verify_otp'),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', logout_view, name='logout'),
]
