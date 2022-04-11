from django.urls import path
from . import views

urlpatterns = [
    path('items/', views.ItemViewSet.as_view({'get':'list', 'post':'create'})),
    path('items/<str:item_id>/', views.ItemViewSet.as_view({'get':'retrieve', 'delete':'destroy'})),
    path('ranker/', views.RankerViewSet.as_view({'get':'list', 'post':'create'})),
    path('ranker/<str:ranker_id>/', views.RankerViewSet.as_view({'get':'retrieve', 'delete':'destroy'})),
    path('ranker/<str:ranker_id>/knows/<str:item_id>/', views.ranker_knows),
    path('ranker/<str:ranker_id>/prefers/<str:preferred_id>/<str:nonpreferred_id>/', views.ranker_pairwise_preference),
    path('ranker/<str:ranker_id>/sort/', views.ranker_sort)
]