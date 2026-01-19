from .models import Category


def active_categories(request):
    return {"nav_categories": Category.objects.filter(active=True)}
