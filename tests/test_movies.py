from cgi import test
import pytest
from rest_framework import status
from movies.models import Movie


@pytest.mark.django_db
class TestListMovies:
    def test_returns_all_movies_and_200(self, api_client, bake_movie):
        bake_movie(_quantity=2)

        response = api_client.get('/api/movies/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2


@pytest.fixture
def retrieve_movie(api_client):
    def do_retrieve_movie(id):
        return api_client.get('/api/movies/{}/'.format(id))
    return do_retrieve_movie


@pytest.mark.django_db
class TestRetrieveMovie:
    def test_if_movie_does_not_exist_returns_404(self, retrieve_movie):
        response = retrieve_movie('badid')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_movie_exists_returns_movie_and_200(self, retrieve_movie, bake_movie):
        test_movie = bake_movie()

        response = retrieve_movie(test_movie.id)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == test_movie.id


@pytest.fixture
def search_movie(api_client):
    def do_search_movie(q):
        return api_client.get('/api/movies/search/?q={}'.format(q))
    return do_search_movie


@pytest.mark.django_db
class TestSearchMovie:
    def test_if_no_matching_movies_returns_empty_and_200(self, search_movie):
        response = search_movie('anything')

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_returns_matching_movies_returns_movies_and_200(self, search_movie, bake_movie):
        searched_movie = bake_movie(title='The Greatest Showman')
        not_searched_movie = bake_movie()
        assert Movie.objects.count() == 2
        assert Movie.objects.filter(title='The Greatest Showman').count() == 1

        response = search_movie(q='showman')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0
