from django.urls import path
from . import views

urlpatterns = [
    path('items/', views.item_list),
    path('items/<str:item_id>/', views.item_detail),
    path('ranker/', views.ranker_list),
    path('ranker/<str:ranker_id>/', views.ranker_detail),
    path('ranker/<str:ranker_id>/<str:item_id>/', views.ranker_knows),
    path('ranker/<str:ranker_id>/<str:preferred_id>/<str:nonpreferred_id>/', views.ranker_pairwise_preference)
]