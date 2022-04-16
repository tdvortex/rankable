from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('', TemplateView.as_view(template_name='core/index.html')),
    path('api/movies/sort/',
         views.MovieRankerViewSet.as_view({'get': 'get_sorted_list'})),
    path('api/movies/queue/',
         views.MovieRankerViewSet.as_view({'get': 'get_comparisons_queue',
                                           'post': 'reset_comparisons_queue',
                                           'delete': 'clear_comparisons_queue'})),
    path('api/movies/discover/',
         views.MovieRankerKnowsViewSet.as_view({'get': 'discover'})),                                   
    path('api/movies/knows/',
         views.MovieRankerKnowsViewSet.as_view({'get': 'list',
                                                'post': 'create'})),
    path('api/movies/knows/<str:item_id>/',
         views.MovieRankerKnowsViewSet.as_view({'get': 'retrieve',
                                                'delete': 'destroy'})),
    path('api/movies/preferences/',
         views.MovieRankerPairwiseViewSet.as_view({'get': 'list',
                                                   'post': 'create'})),
    path('api/movies/preferences/<str:preferred_id>/<str:nonpreferred_id>/',
         views.MovieRankerPairwiseViewSet.as_view({'get': 'retrieve',
                                                   'delete': 'destroy'}))
]