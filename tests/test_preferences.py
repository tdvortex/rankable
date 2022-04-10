import pytest
from rest_framework import status

class TestItemList:
    def test_get_returns_all_items_and_200(self, api_client, setup_neo4j_database):
        response = api_client.get('/api/preferences/items/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 6

    def test_if_post_creates_new_item_returns_201(self, api_client, setup_neo4j_database):
        response = api_client.post('/api/preferences/items/', data={'item_id':'G'})

        assert response.status_code == status.HTTP_201_CREATED

    def test_if_post_bad_data_returns_400(self, api_client, setup_neo4j_database):
        response = api_client.post('/api/preferences/items/', data={'garbage':'XXXXX'})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_if_duplicate_item_returns_400(self, api_client, setup_neo4j_database):
        response = api_client.post('/api/preferences/items/', data={'item_id':'A'})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

class TestItemDetail:
    def test_if_no_item_get_returns_404(self, api_client, setup_neo4j_database):
        response = api_client.get('/api/preferences/items/bad/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_item_get_returns_200(self, api_client, setup_neo4j_database):
        response = api_client.get('/api/preferences/items/A/')

        assert response.status_code == status.HTTP_200_OK

    def test_if_no_item_delete_returns_404(self, api_client, setup_neo4j_database):
        response = api_client.delete('/api/preferences/items/bad/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_item_delete_returns_204(self, api_client, setup_neo4j_database):
        response = api_client.delete('/api/preferences/items/A/')

        assert response.status_code == status.HTTP_204_NO_CONTENT

class TestRankerList:
    def test_get_returns_all_rankers_and_200(self, api_client, setup_neo4j_database):
        response = api_client.get('/api/preferences/ranker/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

    def test_if_post_creates_new_ranker_returns_201(self, api_client, setup_neo4j_database):
        response = api_client.post('/api/preferences/ranker/', data={'ranker_id':'G'})

        assert response.status_code == status.HTTP_201_CREATED

    def test_if_post_bad_data_returns_400(self, api_client, setup_neo4j_database):
        response = api_client.post('/api/preferences/ranker/', data={'garbage':'XXXXX'})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_if_duplicate_ranker_returns_400(self, api_client, setup_neo4j_database):
        response = api_client.post('/api/preferences/ranker/', data={'ranker_id':'123'})

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
        response = api_client.get('/api/preferences/ranker/xxx/A/')

        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_if_ranker_dne_post_returns_404(self, api_client, setup_neo4j_database):
        response = api_client.post('/api/preferences/ranker/xxx/A/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_ranker_dne_delete_returns_404(self, api_client, setup_neo4j_database):
        response = api_client.delete('/api/preferences/ranker/xxx/A/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_item_dne_get_returns_404(self, api_client, setup_neo4j_database):
        response = api_client.get('/api/preferences/ranker/123/X/')

        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_if_item_dne_post_returns_404(self, api_client, setup_neo4j_database):
        response = api_client.post('/api/preferences/ranker/123/X/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_item_dne_delete_returns_404(self, api_client, setup_neo4j_database):
        response = api_client.delete('/api/preferences/ranker/123/X/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_ranker_does_not_know_item_get_returns_204(self, api_client, setup_neo4j_database):
        response = api_client.get('/api/preferences/ranker/123/F/')

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_if_ranker_knows_item_get_returns_200(self, api_client, setup_neo4j_database):
        response = api_client.get('/api/preferences/ranker/123/A/')

        assert response.status_code == status.HTTP_200_OK

    def test_if_ranker_does_not_know_item_post_returns_201(self, api_client, setup_neo4j_database):
        response = api_client.post('/api/preferences/ranker/123/F/')

        assert response.status_code == status.HTTP_201_CREATED

    def test_if_ranker_knows_item_post_returns_200(self, api_client, setup_neo4j_database):
        response = api_client.post('/api/preferences/ranker/123/A/')

        assert response.status_code == status.HTTP_200_OK

    def test_if_ranker_knows_item_delete_removes_preferences_returns_204(self, api_client, setup_neo4j_database):
        response = api_client.delete('/api/preferences/ranker/123/A/')

        assert response.status_code == status.HTTP_204_NO_CONTENT