import pytest
from django.contrib.auth.hashers import make_password
from rest_framework.test import APIClient
from neomodel import db, install_all_labels, remove_all_labels, clear_neo4j_database
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
    '''Factory function to create one or more User objects directly in the database with specified parameters'''
    baked_users = []

    def _bake_user(username=default_username, password=default_password, *args, **kwargs):
        users = baker.make(User, username=username,
                           password=make_password(password), *args, **kwargs)
        nonlocal baked_users
        if isinstance(users, list):
            baked_users += users
        else:
            baked_users.append(users)
        return users

    yield _bake_user

    for user in baked_users:
        user.delete()


@pytest.fixture
def bake_movie():
    '''Factory function to create one or more Movies directly in the database with specified parameters'''
    baked_movies = []

    def _bake_movie(*args, **kwargs):
        movies = baker.make(Movie, *args, **kwargs)
        nonlocal baked_movies
        if isinstance(movies, list):
            baked_movies += movies
        else:
            baked_movies.append(movies)
        return movies
    yield _bake_movie

    for movie in baked_movies:
        movie.delete()

@pytest.fixture
def create_client(api_client):
    def _create_client(user=None, *args, **kwargs):
        if user:
            api_client.force_authenticate(user=user)
        return api_client

    yield _create_client


@pytest.fixture
def authenticated_user_client(bake_user, create_client):
    '''Creates a user in the database and returns a client authenticated as that user'''
    user = bake_user()

    yield create_client(user)

@pytest.fixture
def admin_user_client(bake_user, create_client):
    '''Creates an admin user in the database and returns a client authenticated as that user'''
    user = bake_user(is_staff=True)

    yield create_client(user)


@pytest.fixture()
def setup_neo4j():
    install_all_labels()

    yield

    remove_all_labels()
    clear_neo4j_database

@pytest.fixture()
def insert_known_items():
    known_pairs = []

    def _insert_known_items(ranker: Ranker, items_to_know: list[Item], *args, **kwargs):
        for item in items_to_know:
            ranker.known_items.connect(item)
            known_pairs.append((ranker, item))
        return

    yield _insert_known_items

    for ranker, item in known_pairs:
        ranker.known_items.disconnect(item)


@pytest.fixture()
def insert_unknown_items():
    unknown_pairs = []

    def _insert_unknown_items(ranker: Ranker, items_not_known: list[Item], *args, **kwargs):
        for item in items_not_known:
            ranker.unknown_items.connect(item)
            unknown_pairs.append((ranker, item))
        return

    yield _insert_unknown_items

    for ranker, item in unknown_pairs:
        ranker.unknown_items.disconnect(item)


@pytest.fixture()
def insert_preferences():
    preference_triples = []

    def _insert_preferences(ranker: Ranker, item_pairs: list[tuple[Item, Item]], *args, **kwargs):
        for i, j in item_pairs:
            i.preferred_to_items.connect(j, {'by': ranker.ranker_id})
            preference_triples.append((ranker, i, j))
        return

    yield _insert_preferences

    for ranker, i, j in preference_triples:
        query = "MATCH (i:Item)-[p:PREFERRED_TO_BY]->(j:Item) "
        query += f"WHERE i.item_id='{i.item_id}' AND j.item_id='{j.item_id}' "
        query += f"AND p.by='{ranker.ranker_id}' "
        query += "DELETE p"
        db.cypher_query(query)

@pytest.fixture()
def insert_queued_compares():
    queue_triples = []

    def _insert_queued_compares(ranker: Ranker, item_pairs: list[tuple[Item, Item]], *args, **kwargs):
        for i, j in item_pairs:
            i.queued_compares.connect(j, {'by': ranker.ranker_id})
            j.queued_compares.connect(i, {'by': ranker.ranker_id})
            queue_triples.append((ranker, i, j))
        return

    yield _insert_queued_compares

    for ranker, i, j in queue_triples:
        query = "MATCH (i:Item)-[c:COMPARE_WITH_BY]-(j:Item) "
        query += f"WHERE i.item_id='{i.item_id}' AND j.item_id='{j.item_id}' "
        query += f"AND c.by='{ranker.ranker_id}' "
        query += "DELETE c"
        db.cypher_query(query)

@pytest.fixture
def user_with_movie_preferences(setup_neo4j, bake_user, bake_movie, insert_known_items, insert_unknown_items, insert_preferences, insert_queued_compares):
    # Baking movies and users should automatically populate the test database with those nodes
    user = bake_user()
    movies = bake_movie(_quantity=7)
    items = [Item.nodes.get(item_id=movie.id) for movie in movies]

    # Find the ranker for the baked user
    ranker: Ranker = Ranker.nodes.get(ranker_id=user.id)

    # Ranker knows movies 0-4, does not know movie 5, and has not recorded knowing movie 6
    insert_known_items(ranker, items[0:5])
    insert_unknown_items(ranker, [items[5]])

    # Ranker prefers 0->1->4, 0->2->4, and 0->3
    preferences = [(items[i], items[j])
                   for i, j in [(0, 1), (0, 2), (0, 3), (1, 4), (2, 4)]]
    insert_preferences(ranker, preferences)

    # Ranker has queued comparison between movies 1 and 2 and between 3 and 4
    queued = [(items[i], items[j])
              for i, j in [(1, 2), (3, 4)]]
    insert_queued_compares(ranker, queued)

    yield user

@pytest.fixture
def user_client_with_movie_preferences(user_with_movie_preferences, create_client):
    yield create_client(user_with_movie_preferences)