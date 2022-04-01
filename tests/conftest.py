import pytest
from rest_framework.test import APIClient
from model_bakery import baker
from users.models import User
from movies.models import Movie
from django.contrib.auth.hashers import make_password


@pytest.fixture
def api_client():
    '''An unauthenticated, userless client'''
    return APIClient()


@pytest.fixture
def default_username():
    '''A generic username for use in creating test users'''
    return 'testusername'


@pytest.fixture
def default_password():
    '''A generic password for use in creating test users'''
    return 'xyz123TestPasswordabc890'


@pytest.fixture
def bake_user(default_username, default_password):
    '''A function to create a User directly in the database with specified parameters'''
    def do_bake_user(username=default_username, password=default_password, *args, **kwargs):
        return baker.make(User, username=username, password=make_password(password), *args, **kwargs)
    return do_bake_user


@pytest.fixture
def bake_movie():
    '''A function to greate a Movie directly in the database with specified parameters'''
    def do_bake_movie(*args, **kwargs):
        return baker.make(Movie, *args, **kwargs)
    return do_bake_movie


@pytest.fixture
def authenticate(api_client):
    '''Authenticates a client but does not attach user info'''
    def do_authenticate(username=None, is_staff=False):
        return api_client.force_authenticate(user=User(username=username, is_staff=is_staff))
    return do_authenticate


@pytest.fixture
def authenticated_user_client(api_client, bake_user):
    '''Creates a user in the database and returns a client authenticated as that user'''
    user = bake_user()
    api_client.force_authenticate(user=user)
    return api_client
