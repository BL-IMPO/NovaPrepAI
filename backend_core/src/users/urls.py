from django.urls import path

from .views import IndexView, products_json


app_name = "users"

urlpatterns = [
    path('', IndexView.as_view(), name="index"),
    path("products/", products_json),
]