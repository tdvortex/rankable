import pytest
from rest_framework import status


@pytest.fixture
def create_user(api_client):
    def do_create_user(data):
        return api_client.post('/api/auth/users/', data)
    return do_create_user

@pytest.mark.django_db
class TestCreateUser:
    def test_if_username_is_blank_returns_400(self, create_user):
        response = create_user(data={'password': 'testpassword123'})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_if_password_is_blank_returns_400(self, create_user):
        response = create_user(data={'username':'testuser'})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_if_good_returns_201(self, create_user):
        response = create_user(data={'username':'testuser', 'password': 'testpassword123'})

        assert response.status_code == status.HTTP_201_CREATED

@pytest.fixture
def get_user(api_client):
    def do_get_user(client=api_client):
        return client.get('/api/auth/users/me/')
    return do_get_user

@pytest.mark.django_db
class TestGetUser:
    def test_if_user_is_authenticated_return_200(self, get_user, default_username, authenticated_user_client):
        response = get_user(client=authenticated_user_client)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == default_username

    def test_if_user_is_not_authenticated_return_401(self, get_user):
        response = get_user()

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.fixture
def put_user(api_client):
    def do_put_user(data, client=api_client):
        return client.put('/api/auth/users/me/')
    return do_put_user

@pytest.mark.django_db
class TestPutUser:
    def test_if_user_is_not_authenticated_return_401(self, put_user):
        response = put_user(data={'username':'changeduser', 'password':'changedpassword'})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_user_is_authenticated_return_200(self, put_user, authenticated_user_client):
        response = put_user(data={}, client=authenticated_user_client)

        assert response.status_code == status.HTTP_200_OK

@pytest.fixture
def patch_user(api_client):
    def do_patch_user(data, client=api_client):
        return client.patch('/api/auth/users/me/')
    return do_patch_user

@pytest.mark.django_db
class TestPatchUser:
    def test_if_user_is_not_authenticated_return_401(self, patch_user):
        response = patch_user(data={'username':'changeduser', 'password':'changedpassword'})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_user_is_authenticated_return_200(self, patch_user, authenticated_user_client):
        response = patch_user(data={}, client=authenticated_user_client)

        assert response.status_code == status.HTTP_200_OK


@pytest.fixture
def delete_user(api_client):
    def do_delete_user(data, client=api_client):
        return client.delete('/api/auth/users/me/', data=data)
    return do_delete_user

@pytest.mark.django_db
class TestDeleteUser:
    def test_if_user_is_not_authenticated_return_401(self, delete_user, default_password):
        response = delete_user(
            data={'current_password':default_password}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_password_is_wrong_return_400(self, delete_user, authenticated_user_client):
        response = delete_user(
            data={'current_password':'wrong_password'}, 
            client=authenticated_user_client
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST