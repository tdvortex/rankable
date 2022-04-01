from django.urls import include, path
from . import views

urlpatterns = [
    path('populate/', views.populate_movies)
]