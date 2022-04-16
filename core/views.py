from django.shortcuts import render
from preferences.models import Item
from movies.models import Movie
from movies.serializers import SimpleMovieSerializer
from preferences.views import RankerKnowsViewSet, RankerPairwiseViewSet, RankerViewSet

def get_simple_movie_from_item(self, item: Item):
    movie = Movie.objects.get(id=item.item_id)
    return SimpleMovieSerializer(movie)

class MovieRankerViewSet(RankerViewSet):
    serialize_item = get_simple_movie_from_item

class MovieRankerKnowsViewSet(RankerKnowsViewSet):
    serialize_item = get_simple_movie_from_item

class MovieRankerPairwiseViewSet(RankerPairwiseViewSet):
    serialize_item = get_simple_movie_from_item


