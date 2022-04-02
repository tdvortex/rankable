import pytest
from rest_framework import status

@pytest.fixture
def create_jwt(api_client):
    def do_create_jwt(data, client=api_client):
        return client.post('/api/auth/jwt/create', data=data)
    return do_create_jwt


@pytest.mark.django_db
class TestCreateJWT:
    def test_if_username_is_blank_returns_400(self, create_jwt, default_password):
        response = create_jwt(data={'password':default_password})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_if_password_is_blank_returns_400(self, create_jwt, default_username):
        response = create_jwt(data={'username':default_username})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_if_password_is_wrong_returns_401(self, create_jwt, default_username, authenticated_user_client):
        response = create_jwt(
            data={'username':default_username, 'password':'wrong_password'}, 
            client=authenticated_user_client
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_good_returns_200(self, create_jwt, default_username, default_password, authenticated_user_client):
        response = create_jwt(
            data={'username':default_username, 'password':default_password}, 
            client=authenticated_user_client
        )

        assert response.status_code == status.HTTP_200_OK

@pytest.fixture
def generate_jwt(api_client, bake_user, default_username, default_password):
    def do_generate_jwts(username=default_username, password=default_password):
        bake_user(username=username, password=password)
        response = api_client.post('/api/auth/jwt/create/', data={'username': username, 'password': password})
        return response.data['access'], response.data['refresh']
    return do_generate_jwts

@pytest.fixture
def verify_jwt(api_client):
    def do_verify_jwt(token, client=api_client):
        return client.post('/api/auth/jwt/verify/', data={'token':token})
    return do_verify_jwt

@pytest.mark.django_db
class TestVerifyJWT:
    def test_if_access_is_good_return_200(self, generate_jwt, verify_jwt):
        access, _ = generate_jwt()

        response = verify_jwt(token=access)

        assert response.status_code == status.HTTP_200_OK

    def test_if_access_is_bad_return_401(self, verify_jwt):
        response = verify_jwt(token='badtoken')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.fixture
def refresh_jwt(api_client):
    def do_refresh_jwt(refresh, client=api_client):
        return client.post('/api/auth/jwt/refresh/', data={'refresh':refresh})
    return do_refresh_jwt

@pytest.mark.django_db
class TestRefreshJWT:
    def test_if_refresh_is_good_return_200(self, generate_jwt, refresh_jwt):
        _, refresh = generate_jwt()

        response = refresh_jwt(refresh=refresh)

        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data

    def test_if_access_is_bad_return_401(self, refresh_jwt):
        response = refresh_jwt(refresh='badtoken')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED