# myapp/urls.py
from django.urls import path
from .views import index, generate_number

urlpatterns = [
    path('', index, name='index'),
    path('generate/', generate_number, name='generate_number'),
]
