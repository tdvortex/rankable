
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.contrib.postgres.aggregates import StringAgg
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework import status
from .models import Movie
from .serializers import MovieSerializer, SimpleMovieSerializer
from .imdb import do_populate_movies


@api_view(http_method_names=['GET', 'POST'])
@permission_classes([IsAdminUser])
def populate_movies(request):
    if request.method == 'GET':
        return Response(status=status.HTTP_200_OK)

    return do_populate_movies()


class MovieViewSet(ReadOnlyModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = SimpleMovieSerializer

    @method_decorator(cache_page(60*60))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(60 * 60))
    def retrieve(self, request, *args, **kwargs):
        movie = Movie.objects.prefetch_related('genres').prefetch_related(
            'stars').filter(id=kwargs['pk']).first()
        if not movie:
            return Response(data={'error': 'No movie with id {} found'.format(kwargs['pk'])}, status=status.HTTP_404_NOT_FOUND)

        serializer = MovieSerializer(movie)
        return Response(serializer.data)


    @action(detail=False)
    @method_decorator(cache_page(5 * 60))
    def search(self, request):
        search_vector = SearchVector('title', 'year', weight='A')
        search_vector += SearchVector(StringAgg('stars__name', delimiter=' '),
                                      weight='B')
        search_vector += SearchVector(StringAgg('genres__name', delimiter=' '),
                                      weight='B')
        search_vector += SearchVector('plot', 'content_rating', weight='D')

        query = self.request.GET.get('q')
        if not query:
            return Response(data={'error': 'Search query is required'}, status=status.HTTP_400_BAD_REQUEST)

        search_query = SearchQuery(self.request.GET.get('q'))
        search_rank = SearchRank(vector=search_vector, query=search_query)
        queryset = Movie.objects.annotate(search=search_vector,
                                          rank=search_rank
                                          ).filter(search=search_query
                                                   ).order_by('-rank')
        serializer = SimpleMovieSerializer(queryset, many=True)
        return Response(serializer.data)
