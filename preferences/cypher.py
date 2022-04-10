from .models import Item, Ranker
from neomodel import db

# Boolean checks
def ranker_knows_item(ranker: Ranker, item: Item) -> bool:
    return ranker.known_items.get_or_none(item_id=item.item_id) is not None

def direct_preference_exists(ranker: Ranker, preferred: Item, nonpreferred: Item):
    query = "MATCH (i:Item)-[r:PREFERRED_TO_BY]->(j:Item) "
    query += f"WHERE i.item_id='{preferred.item_id}' AND j.item_id='{nonpreferred.item_id}' AND r.by='{ranker.ranker_id}' "
    query += "RETURN count(r)>0"

    results, _ = db.cypher_query(query)
    return results[0][0]

def is_valid_preference(ranker: Ranker, preferred: Item, nonpreferred: Item) -> bool:
    if not ranker_knows_item(ranker, preferred) or not ranker_knows_item(ranker, nonpreferred):
        # Ranker must know both items to be have a preference
        return False

    # Preference must not violate existing preferences and create a cycle
    cyclic_query = "MATCH p=(j:Item)-[r:PREFERRED_TO_BY*]->(i:Item) "
    cyclic_query += f"WHERE i.item_id='{preferred.item_id}' AND j.item_id='{nonpreferred.item_id}' "
    cyclic_query += f"AND all(r in relationships(p) WHERE r.by='{ranker.ranker_id}') "
    cyclic_query += "RETURN count(p)=0"

    results, _ = db.cypher_query(cyclic_query)
    return results[0][0]

# Create operations
def insert_ranker_knows(ranker: Ranker, item: Item):
    ranker.known_items.connect(item)

def insert_preference(ranker: Ranker, preferred: Item, nonpreferred: Item):
    if not is_valid_preference(ranker, preferred, nonpreferred):
        return 'Invalid'

    if direct_preference_exists(ranker, preferred, nonpreferred):
        return 'Exists'

    query = "MATCH (i:Item), (j:Item) "
    query += f"WHERE i.item_id ='{preferred.item_id}' AND j.item_id ='{nonpreferred.item_id}' "
    query += f"MERGE (i)-[:PREFERRED_TO_BY {{by:'{ranker.ranker_id}'}}]->(j) "

    db.cypher_query(query)
    return 'Created'

# Retrieve operations

def get_direct_preferences(ranker: Ranker) -> list[tuple[Item, Item]]:
    query = "MATCH (i:Item)-[r:PREFERRED_TO_BY]->(j:Item) " 
    query += f"WHERE r.by='{ranker.ranker_id}'" 
    query += "RETURN i,j"

    results, _ = db.cypher_query(query)
    return [(Item.inflate(row[0]), Item.inflate(row[1])) for row in results]


# Delete operations

def delete_direct_preference(ranker: Ranker, preferred: Item, nonpreferred: Item):
    db.begin()
    try:
        if not direct_preference_exists:
            return 'Invalid'

        query = "MATCH (i:Item)-[r:PREFERRED_TO_BY]->(j:Item) "
        query += f"WHERE i.item_id='{preferred.item_id}' AND j.item_id='{nonpreferred.item_id}' AND r.by='{ranker.ranker_id}'"
        query += " DELETE r"

        db.cypher_query(query)

        db.commit()
    except Exception as e:
        db.rollback()
        raise e

def delete_ranker_knows(ranker:Ranker, item:Item):
    db.begin()
    try:
        # Delete all direct preferences the ranker has for this item in both directions
        del_preference_query = "MATCH (i:Item)-[r:PREFERRED_TO_BY]-(:Item) "
        del_preference_query += f"WHERE i.item_id='{item.item_id}' AND r.by='{ranker.ranker_id}'"
        del_preference_query += "DELETE r"

        db.cypher_query(del_preference_query)

        # Then delete this KNOWS relationship
        ranker.known_items.disconnect(item)

        db.commit()
    except Exception as e:
        db.rollback()
        raise e

def delete_ranker(ranker:Ranker):
    db.begin()
    try:
        # Delete all preferences the ranker has for all items in both directions
        del_preference_query = f"MATCH (:Item)-[r:PREFERRED_TO_BY]-(:Item) "
        del_preference_query += f"WHERE r.by = '{ranker.ranker_id}' "
        del_preference_query += f"DELETE r"
        db.cypher_query(del_preference_query)

        # Delete all KNOWS relationships the ranker has for all items
        ranker.known_items.disconnect_all()

        # Then delete the ranker
        del_ranker_query = f"MATCH (x:Ranker) WHERE x.ranker_id='{ranker.ranker_id}' DELETE x"
        db.cypher_query(del_ranker_query)

        db.commit()
    except Exception as e:
        db.rollback()
        raise e

def delete_item(item:Item):
    db.begin()
    try:
        # Detach item from other items (removing preferences for all rankers)
        # Detach item from rankers (removing known relationships)
        # Then delete item
        del_preference_query = f"MATCH (i:Item) "
        del_preference_query += f"WHERE i.item_id = '{item.item_id}'"
        del_preference_query += f"DETACH DELETE i"
        db.cypher_query(del_preference_query)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e