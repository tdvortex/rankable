from django.urls import path
from . import views

urlpatterns = [
    path('preferences/rankers/', views.rankers),
    path('preferences/rankers/<str:ranker_id>/', views.ranker_preferences),
    path('preferences/items/', views.items),
    path('preferences/<str:ranker_id>/<str:preferred_id>/<str:nonpreferred_id>/', views.ranker_pairwise)
]