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
    # Create three rankers with ids 123, 456, and 789
    Ranker(ranker_id='123').save()
    Ranker(ranker_id='456').save()
    Ranker(ranker_id='789').save()

    # Create six items with IDs A,B,C,D,E,F
    Item(item_id='A').save()
    Item(item_id='B').save()
    Item(item_id='C').save()
    Item(item_id='D').save()
    Item(item_id='E').save()
    Item(item_id='F').save()

    # Ranker 123 knows and prefers A->B->E, A->C->E, A->D and does not know F
    query = "MATCH (x:Ranker), (i:Item) "
    query += "WHERE x.ranker_id='123' AND i.item_id IN ['A','B','C','D','E'] "
    query += "MERGE (x)-[:KNOWS]->(i) "
    db.cypher_query(query)

    query = "MATCH (i:Item), (j:Item), (x:Ranker) "
    query += "WHERE x.ranker_id = '123' AND "
    query += "((i.item_id='A' AND j.item_id IN ['B','C']) OR"
    query += "(i.item_id='B' AND j.item_id='E') OR "
    query += "(i.item_id='C' AND j.item_id='E')) "
    query += f"MERGE (i)-[:PREFERRED_TO_BY {{by:x.ranker_id}}]->(j) "
    db.cypher_query(query)

    # Ranker 456 knows and prefers F->E->D->C->B and does not know A
    query = "MATCH (x:Ranker), (i:Item) "
    query += "WHERE x.ranker_id='456' AND i.item_id IN ['B','C','D','E','F'] "
    query += "MERGE (x)-[:KNOWS]->(i) "
    db.cypher_query(query)

    query = "MATCH (i:Item), (j:Item), (x:Ranker) "
    query += "WHERE x.ranker_id = '456' AND "
    query += "((i.item_id='F' AND j.item_id='E') OR"
    query += "(i.item_id='E' AND j.item_id='D') OR "
    query += "(i.item_id='D' AND j.item_id='C') OR "
    query += "(i.item_id='C' AND j.item_id='B')) "
    query += f"MERGE (i)-[:PREFERRED_TO_BY {{by:x.ranker_id}}]->(j) "
    db.cypher_query(query)

    # Ranker 789 knows A,C,E but has no known preferences between them, and does not know B,D,F
    query = "MATCH (x:Ranker), (i:Item) "
    query += "WHERE x.ranker_id='789' AND i.item_id IN ['A','C','E'] "
    query += "MERGE (x)-[:KNOWS]->(i) "
    db.cypher_query(query)