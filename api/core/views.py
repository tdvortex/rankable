from movies.models import Movie as MovieSql
from core.models import Movie as MovieNode, User as UserNode
from movies.serializers import SimpleMovieSerializer
from preferences.views import RankerKnowsViewSet, RankerPairwiseViewSet, RankerViewSet
from .serializers import MovieNodeSerialiazer

def get_simple_movie_from_node(self, movie_node: MovieNode):
    return MovieNodeSerialiazer(movie_node)

class MovieRankerViewSet(RankerViewSet):
    ranker_class = UserNode
    item_class = MovieNode
    serialize_item = get_simple_movie_from_node

class MovieRankerKnowsViewSet(RankerKnowsViewSet):
    ranker_class = UserNode
    item_class = MovieNode
    serialize_item = get_simple_movie_from_node

class MovieRankerPairwiseViewSet(RankerPairwiseViewSet):
    ranker_class = UserNode
    item_class = MovieNode
    serialize_item = get_simple_movie_from_node


