from django.urls import path
from . import views

urlpatterns = [
    path('preferences/items/', views.items),
    path('preferences/', views.rankers),
    path('preferences/<str:ranker_id>/', views.ranker_preferences),
    path('preferences/<str:ranker_id>/<str:item_id>/', views.ranker_knows),
    path('preferences/<str:ranker_id>/<str:preferred_id>/<str:nonpreferred_id>/', views.ranker_pairwise_preference)
]