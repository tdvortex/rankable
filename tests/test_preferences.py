import pytest
from rest_framework import status
from neomodel import db


class TestItemList:
    def test_get_returns_all_items_and_200(self, api_client, setup_neo4j_database):
        response = api_client.get('/api/preferences/items/')

        assert response.status_code == status.HTTP_200_OK

    def test_if_unauthenticated_post_returns_401(self, api_client, setup_neo4j_database):
        response = api_client.post(
            '/api/preferences/items/', data={'item_id': 'G'})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_not_admin_post_returns_403(self, api_client, authenticate, setup_neo4j_database):
        authenticate()
        
        response = api_client.post(
            '/api/preferences/items/', data={'item_id': 'G'})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_if_admin_post_returns_201(self, api_client, authenticate, setup_neo4j_database):
        authenticate(is_staff=True)
        
        response = api_client.post(
            '/api/preferences/items/', data={'item_id': 'G'})

        assert response.status_code == status.HTTP_201_CREATED

    def test_if_post_bad_data_returns_400(self, api_client, authenticate, setup_neo4j_database):
        authenticate(is_staff=True)
        
        response = api_client.post(
            '/api/preferences/items/', data={'garbage': 'XXXXX'})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_if_duplicate_item_returns_400(self, api_client, authenticate, setup_neo4j_database):
        authenticate(is_staff=True)

        response = api_client.post(
            '/api/preferences/items/', data={'item_id': 'A'})

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestItemDetail:
    def test_if_no_item_get_returns_404(self, api_client, setup_neo4j_database):
        response = api_client.get('/api/preferences/items/bad/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_item_get_returns_200(self, api_client, setup_neo4j_database):
        response = api_client.get('/api/preferences/items/A/')

        assert response.status_code == status.HTTP_200_OK

    def test_if_unauthenticated_delete_returns_401(self, api_client, setup_neo4j_database):
        response = api_client.delete('/api/preferences/items/A/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_not_admin_delete_returns_403(self, api_client, authenticate, setup_neo4j_database):
        authenticate()

        response = api_client.delete('/api/preferences/items/A/')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_if_no_item_delete_returns_404(self, api_client, authenticate, setup_neo4j_database):
        authenticate(is_staff=True)

        response = api_client.delete('/api/preferences/items/bad/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_item_delete_returns_204(self, api_client, authenticate, setup_neo4j_database):
        authenticate(is_staff=True)

        response = api_client.delete('/api/preferences/items/A/')

        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestRankerList:
    def test_get_returns_all_rankers_and_200(self, api_client, setup_neo4j_database):
        response = api_client.get('/api/preferences/ranker/')

        assert response.status_code == status.HTTP_200_OK

    def test_if_post_creates_new_ranker_returns_201(self, api_client, setup_neo4j_database):
        response = api_client.post('/api/preferences/ranker/',
                                    data={'ranker_id': 'G'})

        assert response.status_code == status.HTTP_201_CREATED

    def test_if_post_bad_data_returns_400(self, api_client, setup_neo4j_database):
        response = api_client.post(
            '/api/preferences/ranker/', data={'garbage': 'XXXXX'})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_if_duplicate_ranker_returns_400(self, api_client, setup_neo4j_database):
        response = api_client.post(
            '/api/preferences/ranker/', data={'ranker_id': '123'})

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestRankerDetail:
    def test_if_ranker_dne_get_returns_404(self, api_client, setup_neo4j_database):
        response = api_client.get('/api/preferences/ranker/x/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_ranker_dne_delete_returns_404(self, api_client, setup_neo4j_database):
        response = api_client.delete('/api/preferences/ranker/x/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_ranker_exists_get_returns_200(self, api_client, setup_neo4j_database):
        response = api_client.get('/api/preferences/ranker/123/')

        assert response.status_code == status.HTTP_200_OK

    def test_if_ranker_exists_delete_returns_204(self, api_client, setup_neo4j_database):
        response = api_client.delete('/api/preferences/ranker/123/')

        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestRankerKnows:
    def test_if_ranker_dne_get_returns_404(self, api_client, setup_neo4j_database):
        response = api_client.get('/api/preferences/ranker/knows/xxx/knows/A/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_ranker_dne_post_returns_404(self, api_client, setup_neo4j_database):
        response = api_client.post('/api/preferences/ranker/xxx/knows/A/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_ranker_dne_delete_returns_404(self, api_client, setup_neo4j_database):
        response = api_client.delete('/api/preferences/ranker/xxx/knows/A/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_item_dne_get_returns_404(self, api_client, setup_neo4j_database):
        response = api_client.get('/api/preferences/ranker/123/knows/X/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_item_dne_post_returns_404(self, api_client, setup_neo4j_database):
        response = api_client.post('/api/preferences/ranker/123/knows/X/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_item_dne_delete_returns_404(self, api_client, setup_neo4j_database):
        response = api_client.delete('/api/preferences/ranker/123/knows/X/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_ranker_does_not_know_item_get_returns_204(self, api_client, setup_neo4j_database):
        response = api_client.get('/api/preferences/ranker/123/knows/F/')

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_if_ranker_knows_item_get_returns_200(self, api_client, setup_neo4j_database):
        response = api_client.get('/api/preferences/ranker/123/knows/A/')

        assert response.status_code == status.HTTP_200_OK

    def test_if_ranker_does_not_know_item_post_returns_201(self, api_client, setup_neo4j_database):
        response = api_client.post('/api/preferences/ranker/123/knows/F/')

        assert response.status_code == status.HTTP_201_CREATED

    def test_if_ranker_knows_item_post_returns_200(self, api_client, setup_neo4j_database):
        response = api_client.post('/api/preferences/ranker/123/knows/A/')

        assert response.status_code == status.HTTP_200_OK

    def test_if_ranker_knows_item_delete_removes_preferences_returns_204(self, api_client, setup_neo4j_database):
        response = api_client.delete(
            '/api/preferences/ranker/123/knows/A/')

        assert response.status_code == status.HTTP_204_NO_CONTENT

class TestRankerPairwiseGet:
    def test_if_ranker_dne_get_returns_404(self, api_client, setup_neo4j_database):
        response = api_client.get('/api/preferences/ranker/xxx/prefers/A/B/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_preferred_dne_get_returns_404(self, api_client, setup_neo4j_database):
        response = api_client.get('/api/preferences/ranker/123/prefers/X/B/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_nonpreferred_dne_get_returns_404(self, api_client, setup_neo4j_database):
        response = api_client.get('/api/preferences/ranker/123/prefers/A/X/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_preference_exists_get_returns_200(self, api_client, setup_neo4j_database):
        response = api_client.get('/api/preferences/ranker/123/prefers/A/B/')

        assert response.status_code == status.HTTP_200_OK

    def test_if_preference_dne_get_returns_204(self, api_client, setup_neo4j_database):
        response = api_client.get('/api/preferences/ranker/123/prefers/A/E/')

        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestRankerPairwisePost:
    def test_if_ranker_dne_post_returns_404(self, api_client, setup_neo4j_database):
        response = api_client.post('/api/preferences/ranker/xxx/prefers/A/B/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_preferred_dne_post_returns_404(self, api_client, setup_neo4j_database):
        response = api_client.post('/api/preferences/ranker/123/prefers/X/B/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_nonpreferred_dne_post_returns_404(self, api_client, setup_neo4j_database):
        response = api_client.post('/api/preferences/ranker/123/prefers/A/X/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_cyclic_preference_post_returns_400(self, api_client, setup_neo4j_database):
        response = api_client.post('/api/preferences/ranker/123/prefers/E/A/')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_if_unknown_item_post_returns_400(self, api_client, setup_neo4j_database):
        response = api_client.post('/api/preferences/ranker/123/prefers/A/F/')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_if_existing_preference_post_returns_200(self, api_client, setup_neo4j_database):
        response = api_client.post('/api/preferences/ranker/123/prefers/A/B/')

        assert response.status_code == status.HTTP_200_OK

    def test_if_valid_preference_post_returns_201(self, api_client, setup_neo4j_database):
        response = api_client.post(
            '/api/preferences/ranker/123/prefers/A/E/')

        assert response.status_code == status.HTTP_201_CREATED


class TestRankerPairwiseDelete:
    def test_if_ranker_dne_delete_returns_404(self, api_client, setup_neo4j_database):
        response = api_client.delete(
            '/api/preferences/ranker/xxx/prefers/A/B/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_preferred_dne_delete_returns_404(self, api_client, setup_neo4j_database):
        response = api_client.delete(
            '/api/preferences/ranker/123/prefers/X/B/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_nonpreferred_dne_delete_returns_404(self, api_client, setup_neo4j_database):
        response = api_client.delete(
            '/api/preferences/ranker/123/prefers/A/X/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_valid_delete_returns_204(self, api_client, setup_neo4j_database):
        response = api_client.delete(
            '/api/preferences/ranker/123/prefers/A/B/')

        assert response.status_code == status.HTTP_204_NO_CONTENT

class TestRankerSort:
    def test_if_ranker_dne_get_returns_404(self, api_client, setup_neo4j_database):
        response = api_client.get('/api/preferences/ranker/xxx/sort/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_ranker_exists_get_returns_200(self, api_client, setup_neo4j_database):
        response = api_client.get('/api/preferences/ranker/123/sort/')

        assert response.status_code == status.HTTP_200_OK
