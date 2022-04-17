import os
import requests
import json
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
from .models import Movie, Star, Genre

def do_populate_movies():
    if settings.DEBUG:
        f = open('api/.imdb_apikey', 'r')
        key = f.read()
        f.close()
    else:
        key = os.environ.get('IMDB_API_KEY', '')

    offset = Movie.objects.count() + 1

    filename = 'api/.imdb/' + str(offset) + '.json'

    if settings.DEBUG and os.path.exists(filename):
        f = open(filename, 'r')
        json_data = json.loads(f.read())
        f.close()
    else:
        url = "https://imdb-api.com/API/AdvancedSearch/" + key
        url += "?title_type=feature&count=250&sort=num_votes,desc"
        if offset is not None:
            url += "&start=" + str(offset)
        response = requests.request("GET", url, headers={}, data={})
        json_data = response.json()

        if settings.DEBUG:
            f = open(filename, 'w')
            f.write(json.dumps(json_data))
            f.close()

    results = json_data['results']

    created_movies = []

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

    content = {'message': 'Movies {} through {} created'.format(offset, offset+250)}
    return Response(data=content, status=status.HTTP_201_CREATED)