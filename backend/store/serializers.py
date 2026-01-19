from rest_framework import serializers

from .models import Banner, Brand, Category, Product, ProductImage


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = "__all__"


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = "__all__"


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"


class ProductImageReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("id", "image", "is_primary")

class ProductReadSerializer(serializers.ModelSerializer):
    images = ProductImageReadSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "category",
            "brand",
            "name",
            "slug",
            "description",
            "gender",
            "shape",
            "frame_type",
            "frame_material",
            "base_price",
            "is_prescription_supported",
            "is_active",
            "is_trending",
            "is_premium",
            "is_exclusive",
            "images",
        )


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = "__all__"


class ProductImageNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("image", "is_primary")


class ProductNestedCreateSerializer(serializers.ModelSerializer):
    images = ProductImageNestedSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = (
            "category",
            "brand",
            "name",
            "slug",
            "description",
            "gender",
            "shape",
            "frame_type",
            "frame_material",
            "color",
            "size",
            "weight_group",
            "base_price",
            "is_prescription_supported",
            "is_active",
            "is_trending",
            "is_premium",
            "is_exclusive",
            "images",
        )
