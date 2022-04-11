import pytest
from django.contrib.auth.hashers import make_password
from rest_framework.test import APIClient
from neomodel import db, clear_neo4j_database, install_all_labels
from model_bakery import baker
from users.models import User
from movies.models import Movie
from preferences.models import Item, Ranker

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


@pytest.fixture
def setup_neo4j_database():
    clear_neo4j_database(db)
    install_all_labels()
    # Create ranker with id 123
    ranker_123 = Ranker(ranker_id='123').save()

    # Create six items with IDs A,B,C,D,E,F
    item_a = Item(item_id='A').save()
    item_b = Item(item_id='B').save()
    item_c = Item(item_id='C').save()
    item_d = Item(item_id='D').save()
    item_e = Item(item_id='E').save()
    item_f = Item(item_id='F').save()

    # Ranker 123 knows and prefers A->B->E, A->C->E, A->D and does not know F
    ranker_123.known_items.connect(item_a)
    ranker_123.known_items.connect(item_b)
    ranker_123.known_items.connect(item_c)
    ranker_123.known_items.connect(item_d)
    ranker_123.known_items.connect(item_e)

    item_a.preferred_to_items.connect(item_b, {'by':'123'})
    item_a.preferred_to_items.connect(item_c, {'by':'123'})
    item_a.preferred_to_items.connect(item_d, {'by':'123'})
    item_b.preferred_to_items.connect(item_e, {'by':'123'})
    item_c.preferred_to_items.connect(item_e, {'by':'123'})