from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('info', views.MovieViewSet)

urlpatterns = [
    path('populate/', views.populate_movies)
]

urlpatterns += router.urls