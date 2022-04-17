from rest_framework.serializers import ModelSerializer, SlugRelatedField
from .models import Genre, Star, Movie


class GenreSerializer(ModelSerializer):
    class Meta:
        model = Genre


class StarSerializer(ModelSerializer):
    class Meta:
        model = Star


class SimpleMovieSerializer(ModelSerializer):
    class Meta:
        model = Movie
        fields = ['id', 'title', 'year']


class MovieSerializer(ModelSerializer):
    genres = SlugRelatedField(many=True, read_only=True, slug_field='name')
    stars = SlugRelatedField(many=True, read_only=True, slug_field='name')

    class Meta:
        model = Movie
        fields = ['id', 'title', 'year', 'runtime', 'plot', 'content_rating', 'genres', 'stars']