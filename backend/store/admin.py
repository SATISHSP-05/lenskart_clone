from django.contrib import admin
from .models import Banner, Brand, Category, Product, ProductImage


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 2
    max_num = 2
    min_num = 2


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "brand", "category", "frame_type", "shape", "base_price", "is_active")
    list_filter = (
        "brand",
        "category",
        "gender",
        "shape",
        "frame_type",
        "frame_material",
        "color",
        "size",
        "weight_group",
        "is_trending",
        "is_premium",
        "is_exclusive",
    )
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "brand__name")
    inlines = [ProductImageInline]


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "is_primary")
    list_filter = ("is_primary",)


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("title", "banner_type", "order", "active")
    list_filter = ("banner_type", "active")
    list_editable = ("order", "active")
