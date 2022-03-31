from users.models import User
import pytest
from rest_framework import status


@pytest.fixture
def create_user(api_client):
    def do_create_user(user):
        return api_client.post('/api/auth/users/', user)
    return do_create_user

@pytest.mark.django_db
class TestCreateUser:
    def test_if_username_is_blank_returns_400(self, api_client, create_user):
        response = create_user({})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
