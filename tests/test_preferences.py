import pytest
from rest_framework import status

class TestItemList:
    def test_get_returns_all_items_and_200(self, api_client, setup_neo4j_database):
        response = api_client.get('/api/preferences/items/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 6