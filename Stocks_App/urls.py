from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('home.html', views.home, name='home'),
    path('buy.html', views.buy, name='buy'),
    path('result.html', views.result, name='result'),
    path('insert.html', views.insert, name='insert'),
]
