import json
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

    def test_if_not_authenticated_post_returns_401(self, api_client):
        response = api_client.post(self.url, {}, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_if_authenticated_post_returns_201(self, authenticated_user_client, bake_movie):
        known_movies = bake_movie(_quantity=2)
        unknown_movies = bake_movie(_quantity=2)

        known_movie_ids = [movie.id for movie in known_movies]
        unknown_movie_ids = [movie.id for movie in unknown_movies]

        data = {'known_ids': known_movie_ids, 'unknown_ids': unknown_movie_ids}

        response = authenticated_user_client.post(
            self.url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED


class TestMovieKnowsDetail:
    url = '/api/movies/knows/'

    def test_if_not_authenticated_get_returns_401(self, api_client):
        response = api_client.get(self.url + 'xxxgarbagexxx/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_if_movie_dne_returns_404(self, authenticated_user_client):
        response = authenticated_user_client.get(self.url + 'xxxgarbagexxx/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_if_knows_get_returns_200_and_true(self, setup_neo4j, create_client, bake_user, bake_movie, insert_known_items):
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
    def test_if_does_not_know_get_returns_200_and_false(self, setup_neo4j, create_client, bake_user, bake_movie, insert_unknown_items):
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
    def test_if_unstated_get_returns_200_and_undefined(self, setup_neo4j, create_client, bake_user, bake_movie):
        user = bake_user()

        movie = bake_movie()

        client = create_client(user)

        response = client.get(self.url + movie.id + '/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['knows'] == 'undefined'

    def test_if_not_authenticated_delete_returns_401(self, api_client):
        response = api_client.delete(self.url + 'xxxgarbagexxx/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_if_authenticated_delete_returns_200(self, setup_neo4j, create_client, bake_user, bake_movie, insert_known_items):
        user = bake_user()
        ranker: Ranker = Ranker.nodes.get(ranker_id=user.id)

        movie = bake_movie()
        item: Item = Item.nodes.get(item_id=movie.id)

        insert_known_items(ranker, [item])
        client = create_client(user)

        response = client.delete(self.url + movie.id + '/')

        assert response.status_code == status.HTTP_200_OK


class TestMovieSort():
    url = '/api/movies/sort/'

    def test_if_not_authenticated_get_returns_401(self, api_client):
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_if_authenticated_get_returns_200(self, user_client_with_movie_preferences):
        response = user_client_with_movie_preferences.get(self.url)

        assert response.status_code == status.HTTP_200_OK


class TestMovieQueue:
    url = '/api/movies/queue/'

    def test_if_not_authenticated_get_returns_401(self, api_client):
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_if_authenticated_get_returns_200(self, user_client_with_movie_preferences):
        response = user_client_with_movie_preferences.get(self.url)

        assert response.status_code == status.HTTP_200_OK

    def test_if_not_authenticated_post_returns_401(self, api_client):
        response = api_client.post(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_if_authenticated_post_returns_201(self, user_client_with_movie_preferences):
        response = user_client_with_movie_preferences.post(self.url)

        assert response.status_code == status.HTTP_201_CREATED

    def test_if_not_authenticated_delete_returns_401(self, api_client):
        response = api_client.delete(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_if_authenticated_delete_returns_204(self, user_client_with_movie_preferences):
        response = user_client_with_movie_preferences.delete(self.url)

        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestMoviePrefersList:
    url = '/api/movies/preferences/'

    def test_if_not_authenticated_get_returns_401(self, api_client):
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_if_authenticated_get_returns_200(self, user_client_with_movie_preferences):
        response = user_client_with_movie_preferences.get(self.url)

        assert response.status_code == status.HTTP_200_OK

    def test_if_not_authenticated_post_returns_401(self, api_client):
        response = api_client.post(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_if_good_preferences_post_returns_201_no_warnings(self, setup_neo4j, create_client, bake_user, bake_movie, insert_known_items):
        user = bake_user()
        ranker = Ranker.nodes.get(ranker_id=user.id)
        movies = bake_movie(_quantity=3)
        items = [Item.nodes.get(item_id=movie.id) for movie in movies]
        insert_known_items(ranker, items)
        client = create_client(user)

        # A->B->C and A->C
        data = {'preferences':
                [{'preferred_id': items[i].item_id, 'nonpreferred_id': items[j].item_id}
                 for i, j in [(0, 1), (1, 2), (0, 2)]]}

        response = client.post(self.url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert 'warnings' not in response.data

    @pytest.mark.django_db
    def test_if_cyclic_preference_post_returns_201_with_warning(self, setup_neo4j, create_client, bake_user, bake_movie, insert_known_items):
        user = bake_user()
        ranker = Ranker.nodes.get(ranker_id=user.id)
        movies = bake_movie(_quantity=3)
        items = [Item.nodes.get(item_id=movie.id) for movie in movies]
        insert_known_items(ranker, items)
        client = create_client(user)

        # A->B->C->A
        data = {'preferences':
                [{'preferred_id': items[i].item_id, 'nonpreferred_id': items[j].item_id}
                 for i, j in [(0, 1), (1, 2), (2, 1)]]}

        response = client.post(self.url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data['warnings']) == 1

    @pytest.mark.django_db
    def test_if_duplicate_preference_post_returns_201_with_warning(self, setup_neo4j, create_client, bake_user, bake_movie, insert_known_items):
        user = bake_user()
        ranker = Ranker.nodes.get(ranker_id=user.id)
        movies = bake_movie(_quantity=2)
        items = [Item.nodes.get(item_id=movie.id) for movie in movies]
        insert_known_items(ranker, items)
        client = create_client(user)

        # A->B twice
        data = {'preferences':
                [{'preferred_id': items[i].item_id, 'nonpreferred_id': items[j].item_id}
                 for i, j in [(0, 1), (0, 1)]]}

        response = client.post(self.url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data['warnings']) == 1

    @pytest.mark.django_db
    def test_if_unknown_movie_post_returns_201_with_warning(self, setup_neo4j, create_client, bake_user, bake_movie, insert_known_items, insert_unknown_items):
        user = bake_user()
        ranker = Ranker.nodes.get(ranker_id=user.id)
        movies = bake_movie(_quantity=3)
        items = [Item.nodes.get(item_id=movie.id) for movie in movies]
        insert_known_items(ranker, [items[0]])
        insert_unknown_items(ranker, [items[2]])
        client = create_client(user)

        # User knows A, hasn't marked B, and has marked C as unknown
        # All six pairwise preferences should fail
        data = {'preferences':
                [{'preferred_id': items[i].item_id, 'nonpreferred_id': items[j].item_id}
                 for i, j in [(0, 1), (0, 2), (1, 2), (2, 1), (2, 0), (1, 0)]]}

        response = client.post(self.url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data['warnings']) == 6


class TestMoviePrefersDetail:
    url = '/api/movies/preferences/'

    @pytest.mark.django_db
    def test_if_not_authenticated_get_returns_401(self, api_client, bake_movie):
        movies = bake_movie(_quantity=2)

        pair_url = self.url + movies[0].id + '/' + movies[1].id + '/'
        response = api_client.get(pair_url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_if_either_movie_dne_get_returns_404(self, authenticated_user_client, bake_movie):
        movie = bake_movie()

        pair_url = self.url + movie.id + '/xxxgarbagexxx/'
        response = authenticated_user_client.get(pair_url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_if_preference_exists_get_returns_200(self, setup_neo4j, create_client, bake_user, bake_movie,
                                              insert_known_items, insert_preferences):
        user = bake_user()
        ranker = Ranker.nodes.get(ranker_id=user.id)
        movies = bake_movie(_quantity=2)
        items = [Item.nodes.get(item_id=movie.id) for movie in movies]
        insert_known_items(ranker, items)
        insert_preferences(ranker, [(items[0], items[1])])

        pair_url = self.url + movies[0].id + '/' + movies[1].id + '/'
        client = create_client(user)
        response = client.get(pair_url)

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_if_preference_dne_get_returns_204(self, setup_neo4j, authenticated_user_client, bake_user, bake_movie):
        movies = bake_movie(_quantity=2)

        pair_url = self.url + movies[0].id + '/' + movies[1].id + '/'
        response = authenticated_user_client.get(pair_url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.django_db
    def test_if_not_authenticated_delete_returns_401(self, api_client, bake_movie):
        movies = bake_movie(_quantity=2)

        pair_url = self.url + movies[0].id + '/' + movies[1].id + '/'
        response = api_client.delete(pair_url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_if_either_movie_dne_delete_returns_404(self, authenticated_user_client, bake_movie):
        movie = bake_movie()

        pair_url = self.url + movie.id + '/xxxgarbagexxx/'
        response = authenticated_user_client.delete(pair_url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_if_preference_exists_delete_returns_204(self, setup_neo4j, create_client, bake_user, bake_movie,
                                              insert_known_items, insert_preferences):
        user = bake_user()
        ranker = Ranker.nodes.get(ranker_id=user.id)
        movies = bake_movie(_quantity=2)
        items = [Item.nodes.get(item_id=movie.id) for movie in movies]
        insert_known_items(ranker, items)
        insert_preferences(ranker, [(items[0], items[1])])

        pair_url = self.url + movies[0].id + '/' + movies[1].id + '/'
        client = create_client(user)
        response = client.delete(pair_url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.django_db
    def test_if_preference_dne_delete_returns_204(self, authenticated_user_client, bake_user, bake_movie):
        movies = bake_movie(_quantity=2)

        pair_url = self.url + movies[0].id + '/' + movies[1].id + '/'
        response = authenticated_user_client.delete(pair_url)

        assert response.status_code == status.HTTP_204_NO_CONTENT