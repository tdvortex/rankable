from .models import Item, Ranker
from neomodel import db


def ranker_knows_item(ranker: Ranker, item: Item) -> bool:
    query = f"RETURN exists(x:Ranker)-[:KNOWS]->(i:item) "
    query += f"WHERE x.ranker_id='{ranker.ranker_id}', i.item_id='{item.item_id}'"

    results, _ = db.cypher_query(query)
    return results[0][0]


def insert_ranker_knows(ranker: Ranker, item: Item):
    query = f"MERGE (x:Ranker {{ranker_id = '{ranker.ranker_id}'}})-[:KNOWS]->(i:Item {{item_id=='{item.item_id}'}}) "
    query += f"ON MATCH RETURN 'Exists' "
    query += f"ON CREATE RETURN 'Created'"

    results, _ = db.cypher_query(query)
    return results[0][0]


def is_valid_preference(ranker: Ranker, preferred: Item, nonpreferred: Item) -> bool:
    if not ranker_knows_item(ranker, preferred) or not ranker_knows_item(ranker, nonpreferred):
        # Ranker must know both items to be have a preference
        return False

    # Preference must not violate existing preferences and create a cycle
    cyclic_query = f"RETURN NOT exists((j:Item)-[r:PREFERRED_TO_BY*]->(i:Item) "
    cyclic_query += f"WHERE i.item_id='{preferred.item_id}', j.item_id='{nonpreferred.item_id}', r.by='{ranker.ranker_id}'"

    results, _ = db.cypher_query(cyclic_query)
    return results[0][0]


def insert_preference(ranker: Ranker, preferred: Item, nonpreferred: Item):
    if not is_valid_preference(ranker, preferred, nonpreferred):
        return 'Invalid'

    query = f"MATCH (i:Item), (j:Item) WHERE i.item_id ='{preferred.item_id}', j.item_id ='{nonpreferred.item_id}' "
    query += f"MERGE (i)-[:PREFERRED_TO_BY {{by:'{ranker.ranker_id}'}}]->(j) "
    query += f"ON MATCH RETURN 'Exists' "
    query += f"ON CREATE RETURN 'Created'"

    results, _ = db.cypher_query(query)
    return results[0][0]


def direct_preference_exists(ranker: Ranker, preferred: Item, nonpreferred: Item):
    query = f"RETURN exists((i:Item)-[r:PREFERRED_TO_BY]->(j:Item)) "
    query += f"WHERE i.item_id ='{preferred.item_id}', j.item_id ='{nonpreferred.item_id}', r.by='{ranker.ranker_id}'"

    results, _ = db.cypher_query(query)
    return results[0][0]


def get_direct_preferences(ranker: Ranker) -> list[tuple[Item, Item]]:
    query = f"MATCH (i:Item)-[:PREFERRED_TO_BY {{by:'{ranker.ranker_id}'}}]->(j:Item) RETURN i,j"

    results, _ = db.cypher_query(query)
    return [(Item.inflate(row[0]), Item.inflate(row[1])) for row in results]


def delete_direct_preference(ranker: Ranker, preferred: Item, nonpreferred: Item):
    if not direct_preference_exists:
        return 'Invalid'

    query = f"MATCH (i:Item)-[r:PREFERRED_TO_BY {{by:'{ranker.ranker_id}'}}]->(j:Item) "
    query += f"WHERE i.item_id='{preferred.item_id}', j.item_id='{nonpreferred.item_id}' "
    query += f" DELETE r"

    db.cypher_query(query)
    return True
