import os
import requests
from django.conf import settings
from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import ReadOnlyModelViewSet
from .models import Movie, Star, Genre
from .serializers import MovieSerializer, SimpleMovieSerializer


@api_view(http_method_names=['GET', 'POST'])
@permission_classes([IsAdminUser])
def populate_movies(request):
    if request.method == 'GET':
        return Response(status=status.HTTP_200_OK)

    if settings.DEBUG:
        f = open('.apikey', 'r')
        key = f.read()
        f.close()
    else:
        key = os.environ.get('IMDB_API_KEY', '')

    offset = Movie.objects.count() + 1

    url = "https://imdb-api.com/API/AdvancedSearch/" + key
    url += "?title_type=feature&count=250&sort=num_votes,desc"
    if offset is not None:
        url += "&start=" + str(offset)

    response = requests.request("GET", url, headers={}, data={})
    results = response.json()['results']

    for movie in results:
        id = movie['id']
        title = movie['title']
        year = int(movie['description'][-5:-1])  # '(1999)' -> 1999
        runtime = int(movie['runtimeStr'].split(' ')[0])  # '150 min' -> 150
        genre_list = [genre['value'] for genre in movie['genreList']]
        content_rating = str(movie['contentRating'])
        plot = movie['plot']
        star_list = [star['name'] for star in movie['starList']]

        new_movie = Movie(id=id,
                          title=title,
                          year=year,
                          runtime=runtime,
                          plot=plot,
                          content_rating=content_rating)

        new_movie, created = Movie.objects.get_or_create(id=id,
                                                         defaults={'title': title,
                                                                   'year': year,
                                                                   'runtime': runtime,
                                                                   'plot': plot,
                                                                   'content_rating': content_rating})

        if not created:
            continue

        for genre_name in genre_list:
            genre, created = Genre.objects.get_or_create(name=genre_name)
            Movie.genres.through.objects.get_or_create(genre=genre, movie=new_movie)

        for star_name in star_list:
            star, created = Star.objects.get_or_create(name=star_name)
            Movie.stars.through.objects.get_or_create(star=star, movie=new_movie)

    return Response(status=status.HTTP_201_CREATED)

class MovieViewSet(ReadOnlyModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = SimpleMovieSerializer

    def retrieve(self, request, *args, **kwargs):
        movie = Movie.objects.prefetch_related('genres').prefetch_related('stars').filter(id=kwargs['pk']).first()
        serializer = MovieSerializer(movie)
        return Response(serializer.data)