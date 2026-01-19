from django.db import migrations, models


def seed_hto_addresses(apps, schema_editor):
    HtoAddress = apps.get_model("store", "HtoAddress")
    if HtoAddress.objects.exists():
        return
    HtoAddress.objects.create(
        name="Satish SP",
        phone="91123233351",
        address_line="2nd floor Lenskart Bannerghatta road",
        city="Bangalore",
        state="Karnataka",
        pincode="560076",
        is_default=True,
    )
    HtoAddress.objects.create(
        name="Nisha Rao",
        phone="9811122233",
        address_line="55, 4th Block, Koramangala",
        city="Bangalore",
        state="Karnataka",
        pincode="560034",
    )
    HtoAddress.objects.create(
        name="Amit Verma",
        phone="9898989898",
        address_line="Shop 21, Sector 12 Market",
        city="Dwarka",
        state="Delhi",
        pincode="110078",
    )


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0006_remove_product_tryon_glasses"),
    ]

    operations = [
        migrations.CreateModel(
            name="HtoAddress",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("phone", models.CharField(max_length=30)),
                ("address_line", models.CharField(max_length=255)),
                ("city", models.CharField(max_length=120)),
                ("state", models.CharField(max_length=120)),
                ("pincode", models.CharField(max_length=20)),
                ("is_default", models.BooleanField(default=False)),
            ],
            options={"ordering": ["-is_default", "id"]},
        ),
        migrations.RunPython(seed_hto_addresses, migrations.RunPython.noop),
    ]
