from django.urls import path
from . import views

urlpatterns = [
    path('', views.extract_license_plate, name='extract_license_plate'),
]
