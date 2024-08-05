from django.urls import path
from . import views

app_name = 'spotify'
urlpatterns = [
    path('', views.login, name='home'),
    path('redirect/', views.find),
    path('transfer/', views.transfer, name='transfer'),
]