from django.db import models
from django.utils.text import slugify


class UnrestrictedImageField(models.ImageField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Allow uploads without relying on filename extensions.
        self.validators = []

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        # Keep migrations stable by treating this like a standard ImageField.
        return name, "django.db.models.ImageField", args, kwargs


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    logo = UnrestrictedImageField(upload_to='brands/', blank=True, null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    image = UnrestrictedImageField(upload_to='categories/', blank=True, null=True)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    GENDER_CHOICES = [
        ('men', 'Men'),
        ('women', 'Women'),
        ('kids', 'Kids'),
        ('unisex', 'Unisex'),
    ]
    SHAPE_CHOICES = [
        ('round', 'Round'),
        ('rectangle', 'Rectangle'),
        ('square', 'Square'),
        ('oval', 'Oval'),
        ('aviator', 'Aviator'),
        ('cat-eye', 'Cat Eye'),
        ('geometric', 'Geometric'),
    ]
    FRAME_TYPE_CHOICES = [
        ('full-rim', 'Full Rim'),
        ('half-rim', 'Half Rim'),
        ('rimless', 'Rimless'),
    ]
    SIZE_CHOICES = [
        ('extra-narrow', 'Extra Narrow'),
        ('narrow', 'Narrow'),
        ('medium', 'Medium'),
        ('wide', 'Wide'),
        ('extra-wide', 'Extra Wide'),
    ]
    WEIGHT_CHOICES = [
        ('light', 'Light'),
        ('average', 'Average'),
        ('heavy', 'Heavy'),
    ]

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, default='unisex')
    shape = models.CharField(max_length=50, choices=SHAPE_CHOICES, blank=True)
    frame_type = models.CharField(max_length=50, choices=FRAME_TYPE_CHOICES, blank=True)
    frame_material = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=50, blank=True)
    size = models.CharField(max_length=20, choices=SIZE_CHOICES, blank=True)
    weight_group = models.CharField(max_length=20, choices=WEIGHT_CHOICES, blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_prescription_supported = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_trending = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    is_exclusive = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_primary_image(self):
        primary = self.images.filter(is_primary=True).first()
        if primary:
            return primary
        return self.images.first()

    def get_display_price(self):
        return self.base_price

    def get_secondary_image(self):
        images = self.images.order_by('-is_primary', 'id')
        if images.count() > 1:
            return images[1]
        return None


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = UnrestrictedImageField(upload_to='products/')
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.product.name} Image"


class Banner(models.Model):
    BANNER_TYPES = [
        ('hero', 'Hero'),
        ('coupon', 'Coupon'),
        ('replacement', 'Replacement'),
        ('exclusive', 'Exclusive'),
        ('premium', 'Premium'),
        ('buy1get1', 'Buy 1 Get 1'),
        ('misc', 'Misc'),
    ]
    title = models.CharField(max_length=255, blank=True)
    banner_type = models.CharField(max_length=30, choices=BANNER_TYPES, default='misc')
    image = UnrestrictedImageField(upload_to='banners/')
    link = models.URLField(blank=True, null=True)
    active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title if self.title else f"Banner {self.id}"


class HtoAddress(models.Model):
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30)
    address_line = models.CharField(max_length=255)
    city = models.CharField(max_length=120)
    state = models.CharField(max_length=120)
    pincode = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_default", "id"]

    def __str__(self):
        return f"{self.name} - {self.city}"


class DeliveryPincode(models.Model):
    pincode = models.CharField(max_length=6, unique=True)
    city = models.CharField(max_length=120, blank=True)
    state = models.CharField(max_length=120, blank=True)
    delivery_days = models.PositiveSmallIntegerField(default=3)
    active = models.BooleanField(default=True)
    source = models.CharField(max_length=20, default="db")
    last_checked = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["pincode"]

    def __str__(self):
        return self.pincode
