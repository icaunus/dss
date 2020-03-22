from django.urls import path
from . import views

urlpatterns = [
  path('', views.appidx, name='appidx'),
  path('continents', views.continents, name='continents'),
  path('regions', views.regions, name='regions'),
  path('countries', views.countries, name='countries'),
  path('country', views.country, name='country'),
  path('cities', views.cities, name='cities'),
  path('city', views.city, name='city'),
  path('add', views.add, name='addCity'),
  path('update', views.update, name='updateCity'),
  path('delete', views.delete, name='deleteCity')
]
