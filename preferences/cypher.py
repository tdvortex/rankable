from .models import Item, Ranker, PreferredToByRel
from neomodel import db


def insert_ranker(ranker_id:str)->bool:
    try:
        ranker = Ranker(ranker_id)
        ranker.save()
    except Exception as e:
        print(e)
        return False
    return True

def insert_item(item_id:str)->bool:
    try:
        ranker = Item(item_id)
        ranker.save()
    except Exception as e:
        print(e)
        return False
    return True

def is_valid_preference(ranker: Ranker, preferred: Item, nonpreferred: Item) -> bool:
    if (ranker.knows.first_or_none(preferred.item_id) is None
            or ranker.knows.first_or_none(nonpreferred.item_id) is None):
        # Ranker must know both items to be have a preference
        return False

    query = f"RETURN NOT exists((j:Item)-[r:PREFERRED_TO_BY*]->(i:Item) "
    query += f"WHERE i.item_id='{preferred.item_id}', j.item_id='{nonpreferred.item_id}', r.by='{ranker.ranker_id}')"

    results, _ = db.cypher_query(query)
    return results[0]

def insert_preference(ranker: Ranker, preferred: Item, nonpreferred: Item) -> bool:
    if not is_valid_preference(ranker, preferred, nonpreferred):
        return False
    
    query = f"MATCH (i:Item), (j:Item) WHERE i.item_id ='{preferred.item_id}', j.item_id ='{nonpreferred.item_id}'"
    query += f"MERGE (i)-[:PREFERRED_TO_BY {{by:'{ranker.id}'}}]->(j)"

    try:
        db.cypher_query(query)
    except Exception as e:
        print(e)
        return False
    else:
        return True

def get_direct_preferences(ranker: Ranker) -> list[tuple[Item, Item]]:
    query = f"MATCH (i:Item)-[:PREFERRED_TO_BY {{by:'{ranker.ranker_id}'}}]->(j:Item) RETURN i,j"

    results, _ = db.cypher_query(query)
    return [(Item.inflate(row[0]), Item.inflate(row[1])) for row in results]