from django.urls import path
from . import views

urlpatterns = [
    path('items/', views.item_list),
    path('items/<str:item_id>/', views.item_detail),
    path('ranker/', views.ranker_list),
    path('ranker/<str:ranker_id>/', views.ranker_detail),
    path('ranker/<str:ranker_id>/knows/<str:item_id>/', views.ranker_knows),
    path('ranker/<str:ranker_id>/prefers/<str:preferred_id>/<str:nonpreferred_id>/', views.ranker_pairwise_preference),
    path('ranker/<str:ranker_id>/sort/', views.ranker_sort)
]