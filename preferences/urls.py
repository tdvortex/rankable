from django.urls import path
from . import views

urlpatterns = [
    path('items/',
         views.ItemViewSet.as_view({'get': 'list',
                                    'post': 'create'})),
    path('items/<str:item_id>/',
         views.ItemViewSet.as_view({'get': 'retrieve',
                                    'delete': 'destroy'})),
    path('ranker/',
         views.RankerViewSet.as_view({'get': 'list',
                                      'post': 'create'})),
    path('ranker/<str:ranker_id>/',
         views.RankerViewSet.as_view({'get': 'retrieve',
                                      'delete': 'destroy'})),
    path('ranker/<str:ranker_id>/knows/<str:item_id>/',
         views.RankerKnowsViewSet.as_view({'get': 'retrieve',
                                           'post': 'create',
                                           'delete': 'destroy'})),
    path('ranker/<str:ranker_id>/prefers/<str:preferred_id>/<str:nonpreferred_id>/',
         views.RankerPairwiseViewSet.as_view({'get': 'retrieve',
                                              'post': 'create',
                                              'delete': 'destroy'})),
    path('ranker/<str:ranker_id>/sort/',
         views.RankerViewSet.as_view({'get': 'get_sorted_list'}))
]
