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
        movie = Movie.objects.prefetch_related('genres').prefetch_related('stars').filter(id=kwargs['pk']).first()
        serializer = MovieSerializer(movie)
        return Response(serializer.data)