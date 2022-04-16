import pytest
from rest_framework import status
from preferences.models import Item, Ranker


class TestMovieDiscover:
    url = '/api/movies/discover/'

    def test_if_not_authenticated_get_returns_401(self, api_client):
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.django_db
    def test_if_authenticated_get_returns_200(self, user_client_with_movie_preferences):
        response = user_client_with_movie_preferences.get(self.url)

        assert response.status_code == status.HTTP_200_OK

class TestMovieKnowsList:
    url = '/api/movies/knows/'
    def test_if_not_authenticated_get_returns_401(self, api_client):
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.django_db
    def test_if_authenticated_get_returns_200(self, authenticated_user_client):
        response = authenticated_user_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK


class TestMovieKnowsDetail:
    url = '/api/movies/knows/'
    @pytest.mark.django_db
    def test_if_not_authenticated_get_returns_401(self, api_client, bake_movie):
        movie = bake_movie()

        response = api_client.get(self.url + movie.id + '/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_if_movie_dne_returns_404(self, authenticated_user_client):
        response = authenticated_user_client.get(self.url + 'xxxgarbagexxx/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_if_knows_get_returns_200_and_true(self, setup_neo4j_labels, create_client, bake_user, bake_movie, insert_known_items):
        user = bake_user()
        ranker: Ranker = Ranker.nodes.get(ranker_id=user.id)

        movie = bake_movie()
        item: Item = Item.nodes.get(item_id=movie.id)

        insert_known_items(ranker, [item])
        client = create_client(user)
        
        response = client.get(self.url + movie.id + '/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['knows'] == True
        
    @pytest.mark.django_db
    def test_if_does_not_know_get_returns_200_and_false(self, setup_neo4j_labels, create_client, bake_user, bake_movie, insert_unknown_items):
        user = bake_user()
        ranker: Ranker = Ranker.nodes.get(ranker_id=user.id)

        movie = bake_movie()
        item: Item = Item.nodes.get(item_id=movie.id)

        insert_unknown_items(ranker, [item])
        client = create_client(user)
        
        response = client.get(self.url + movie.id + '/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['knows'] == False

    @pytest.mark.django_db
    def test_if_unstated_get_returns_200_and_undefined(self, setup_neo4j_labels, create_client, bake_user, bake_movie):
        user = bake_user()

        movie = bake_movie()

        client = create_client(user)
        
        response = client.get(self.url + movie.id + '/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['knows'] == 'undefined'