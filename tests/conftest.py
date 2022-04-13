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
def admin_user_client(api_client):
    '''Creates an admin user'''
    api_client.force_authenticate(is_staff=True)
    return api_client


@pytest.fixture
def default_ranker() -> Ranker:
    print("Creating ranker")
    ranker = Ranker(ranker_id='123').save()
    yield ranker
    ranker.delete()
    print("Ranker deleted")


@pytest.fixture
def default_items():
    ids = ['A', 'B', 'C', 'D', 'E', 'F']
    items = {id: Item(item_id=id).save() for id in ids}
    yield items
    for item in items.values():
        item.delete()


@pytest.fixture
def default_known(default_ranker: Ranker, default_items):
    for id in ['A', 'B', 'C', 'D', 'E']:
        default_ranker.known_items.connect(default_items[id])
    yield
    for id in ['A', 'B', 'C', 'D', 'E']:
        default_ranker.known_items.disconnect(default_items[id])


@pytest.fixture
def default_preferences(default_ranker: Ranker, default_items):
    for id_preferred, id_nonpreferred in [('A', 'B'),
                                          ('A', 'C'),
                                          ('A', 'D'),
                                          ('B', 'E'),
                                          ('C', 'E')]:
        default_items[id_preferred].preferred_to_items.connect(
            default_items[id_nonpreferred], {'by': default_ranker.ranker_id})
    yield
    for id_preferred, id_nonpreferred in [('A', 'B'),
                                          ('A', 'C'),
                                          ('A', 'D'),
                                          ('B', 'E'),
                                          ('C', 'E')]:
        default_items[id_preferred].preferred_to_items.disconnect(
            default_items[id_nonpreferred])


@pytest.fixture
def default_queue(default_ranker: Ranker, default_items):
    for left_id, right_id in [('B', 'C'), ('D', 'E')]:
        default_items[left_id].queued_compares.connect(
            default_items[right_id], {'by': default_ranker.ranker_id})
        default_items[right_id].queued_compares.connect(
            default_items[left_id], {'by': default_ranker.ranker_id})
    yield
    for left_id, right_id in [('B', 'C'), ('D', 'E')]:
        default_items[left_id].queued_compares.disconnect(
            default_items[right_id])
        default_items[right_id].queued_compares.disconnect(
            default_items[left_id])


@pytest.fixture
def setup_neo4j_database(default_known, default_preferences, default_queue):
    install_all_labels()
    yield
    clear_neo4j_database(db)
