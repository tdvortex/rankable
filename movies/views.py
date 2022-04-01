
from django.shortcuts import render
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.contrib.postgres.aggregates import StringAgg
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import ReadOnlyModelViewSet
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

    def retrieve(self, request, *args, **kwargs):
        movie = Movie.objects.prefetch_related('genres').prefetch_related(
            'stars').filter(id=kwargs['pk']).first()
        serializer = MovieSerializer(movie)
        return Response(serializer.data)

    @action(detail=False)
    def search(self, request):
        search_vector = SearchVector('title', 'year', weight='A')
        search_vector += SearchVector(StringAgg('stars__name',
                                      delimiter=' '), weight='B')
        search_vector += SearchVector(StringAgg('genres__name',
                                      delimiter=' '), weight='B')
        search_vector += SearchVector('plot', 'content_rating', weight='D')

        search_query = SearchQuery(self.request.GET.get('q'))
        search_rank = SearchRank(vector=search_vector, query=search_query)
        queryset = Movie.objects.annotate(rank=search_rank).filter(
            search_vector=search_query).order_by('-rank')
        serializer = SimpleMovieSerializer(queryset, many=True)
        return Response(serializer.data)
