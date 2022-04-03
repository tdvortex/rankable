from .models import Item, Ranker
from neomodel import db

def is_valid_preference(ranker: Ranker, preferred: Item, nonpreferred: Item) -> bool:
    if (ranker.knows.first_or_none(preferred.item_id) is None
            or ranker.knows.first_or_none(nonpreferred.item_id) is None):
        # Ranker must know both items to be have a preference
        return False

    query = f"RETURN NOT exists((j:Item)-[r:PREFERRED_TO_BY*]->(i:Item) "
    query += f"WHERE i.item_id='{preferred.item_id}', j.item_id='{nonpreferred.item_id}', r.by='{ranker.ranker_id}')"

    results, _ = db.cypher_query(query)
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

def direct_preference_exists(ranker:Ranker, preferred:Item, nonpreferred:Item):
    query = f"RETURN exists((i:Item)-[r:PREFERRED_TO_BY]->(j:Item)) "
    query += f"WHERE i.item_id ='{preferred.item_id}', j.item_id ='{nonpreferred.item_id}', r.by='{ranker.ranker_id}'"

    results, _ = db.cypher_query(query)
    return results[0][0]

def get_direct_preferences(ranker: Ranker) -> list[tuple[Item, Item]]:
    query = f"MATCH (i:Item)-[:PREFERRED_TO_BY {{by:'{ranker.ranker_id}'}}]->(j:Item) RETURN i,j"

    results, _ = db.cypher_query(query)
    return [(Item.inflate(row[0]), Item.inflate(row[1])) for row in results]