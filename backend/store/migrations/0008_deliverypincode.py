from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0007_htoaddress"),
    ]

    operations = [
        migrations.CreateModel(
            name="DeliveryPincode",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("pincode", models.CharField(max_length=6, unique=True)),
                ("city", models.CharField(blank=True, max_length=120)),
                ("state", models.CharField(blank=True, max_length=120)),
                ("delivery_days", models.PositiveSmallIntegerField(default=3)),
                ("active", models.BooleanField(default=True)),
                ("source", models.CharField(default="db", max_length=20)),
                ("last_checked", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["pincode"],
            },
        ),
    ]
