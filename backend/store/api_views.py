from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Banner, Brand, Category, Product, ProductImage
from .serializers import (
    BannerSerializer,
    BrandSerializer,
    CategorySerializer,
    ProductImageSerializer,
    ProductReadSerializer,
    ProductNestedCreateSerializer,
    ProductSerializer,
)


class BannerViewSet(viewsets.ModelViewSet):
    queryset = Banner.objects.all()
    serializer_class = BannerSerializer

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]
        return [IsAuthenticated()]


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]
        return [IsAuthenticated()]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]
        return [IsAuthenticated()]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return ProductReadSerializer
        if self.action == "nested_create":
            return ProductNestedCreateSerializer
        return ProductSerializer

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=False, methods=["post"], url_path="nested")
    def nested_create(self, request):
        serializer = ProductNestedCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data
        images_data = validated.pop("images", [])

        with transaction.atomic():
            product = Product.objects.create(**validated)
            for image_payload in images_data:
                ProductImage.objects.create(product=product, **image_payload)

        return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="bulk")
    def bulk_create(self, request):
        if not isinstance(request.data, list):
            return Response({"detail": "Expected a list of products."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = ProductSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        products = Product.objects.bulk_create([Product(**item) for item in serializer.validated_data])
        return Response(ProductSerializer(products, many=True).data, status=status.HTTP_201_CREATED)


class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]
        return [IsAuthenticated()]
