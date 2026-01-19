import random
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from store.models import Banner, Brand, Category, Product, ProductImage


class Command(BaseCommand):
    help = "Seed categories, brands, banners, and products from backend/media/* folders."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing products, images, categories, brands, and banners.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            ProductImage.objects.all().delete()
            Product.objects.all().delete()
            Banner.objects.all().delete()
            Category.objects.all().delete()
            Brand.objects.all().delete()

        media = Path(settings.BASE_DIR) / "media"
        products_dir = media / "products"
        categories_dir = media / "categories"
        brands_dir = media / "brands"
        banners_dir = media / "banners"

        categories = [
            ("Eyeglasses", "eyeglasses"),
            ("Sunglasses", "sunglasses"),
            ("Contact Lenses", "contact-lenses"),
            ("Kids Glasses", "kids"),
            ("Special Power", "special-power"),
            ("Sale", "sale"),
        ]
        brands = [
            "Vincent Chase",
            "John Jacobs",
            "Lenskart Air",
            "Hustlr",
            "Fossil",
            "Blu",
        ]
        shapes = ["round", "rectangle", "square", "oval", "aviator", "cat-eye", "geometric"]
        frame_types = ["full-rim", "half-rim", "rimless"]
        genders = ["men", "women", "kids", "unisex"]
        colors = ["Black", "Transparent", "Blue", "Grey", "Gold", "Green", "Brown"]
        sizes = ["extra-narrow", "narrow", "medium", "wide", "extra-wide"]
        weights = ["light", "average", "heavy"]

        cat_images = sorted([p for p in categories_dir.glob("*") if p.is_file()])
        brand_images = sorted([p for p in brands_dir.glob("*") if p.is_file()])

        for index, (name, slug) in enumerate(categories):
            image_path = None
            if cat_images:
                image_path = f"categories/{cat_images[index % len(cat_images)].name}"
            Category.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "image": image_path,
                    "active": True,
                },
            )

        for index, name in enumerate(brands):
            image_path = None
            if brand_images:
                image_path = f"brands/{brand_images[index % len(brand_images)].name}"
            Brand.objects.get_or_create(
                slug=slugify(name),
                defaults={"name": name, "logo": image_path, "active": True},
            )

        banner_images = sorted([p for p in banners_dir.glob("*") if p.is_file()])
        for index, banner in enumerate(banner_images[:6]):
            Banner.objects.get_or_create(
                title=f"Hero {index + 1}",
                banner_type="hero",
                defaults={
                    "image": f"banners/{banner.name}",
                    "active": True,
                    "order": index,
                },
            )

        product_files = sorted([p for p in products_dir.glob("*") if p.is_file()])
        if not product_files:
            self.stdout.write(self.style.WARNING("No product images found."))
            return

        category_objs = list(Category.objects.all())
        brand_objs = list(Brand.objects.all())

        for i, image in enumerate(product_files):
            category = category_objs[i % len(category_objs)]
            brand = brand_objs[i % len(brand_objs)]
            slug = f"product-{i + 1}"
            name = f"Product {i + 1}"
            price = 999 + (i % 10) * 150

            product, _ = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    "category": category,
                    "brand": brand,
                    "name": name,
                    "description": "Auto-seeded product from media.",
                    "gender": genders[i % len(genders)],
                    "shape": shapes[i % len(shapes)],
                    "frame_type": frame_types[i % len(frame_types)],
                    "frame_material": "Acetate",
                    "color": colors[i % len(colors)],
                    "size": sizes[i % len(sizes)],
                    "weight_group": weights[i % len(weights)],
                    "base_price": price,
                    "is_prescription_supported": True,
                    "is_active": True,
                    "is_trending": i % 8 == 0,
                    "is_premium": i % 10 == 0,
                    "is_exclusive": i % 12 == 0,
                },
            )

            ProductImage.objects.get_or_create(
                product=product,
                image=f"products/{image.name}",
                defaults={"is_primary": True},
            )

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(product_files)} products from media."))
