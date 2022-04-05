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