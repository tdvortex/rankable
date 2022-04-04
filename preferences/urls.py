from django.urls import path
from . import views

urlpatterns = [
    path('preferences/items/', views.items),
    path('preferences/', views.ranker_list),
    path('preferences/<str:ranker_id>/', views.ranker_detail),
    path('preferences/<str:ranker_id>/<str:item_id>/', views.ranker_knows),
    path('preferences/<str:ranker_id>/<str:preferred_id>/<str:nonpreferred_id>/', views.ranker_pairwise_preference)
]