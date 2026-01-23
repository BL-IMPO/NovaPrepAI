from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import TemplateView

from .models import Product


class IndexView(TemplateView):
    template_name = 'index.html'

def products_json(request):
    products = list(Product.objects.values())
    return JsonResponse(products, safe=False)
