from random import sample
from .models import Item, Ranker
from neomodel import db

# Boolean checks
def ranker_knows_item(ranker: Ranker, item: Item) -> bool:
    return item in ranker.known_items.all()

def ranker_does_not_know_item(ranker: Ranker, item: Item) -> bool:
    return item in ranker.unknown_items.all()

def direct_preference_exists(ranker: Ranker, preferred: Item, nonpreferred: Item):
    return nonpreferred in preferred.preferred_to_items.match(by=ranker.ranker_id)

# Create operations
def insert_ranker_knows(ranker: Ranker, known_items: list[Item], unknown_items: list[Item]):   
    if known_items:
        with db.transaction:
            # Remove that they do not know each item
            query = "MATCH (r)-[d:DOES_NOT_KNOW]->(i) "
            query += f"WHERE r.ranker_id='{ranker.ranker_id}' "
            query += f"AND i.item_id IN {[item.item_id for item in known_items]} "
            query += f"DELETE d"
            db.cypher_query(query)

            # Add that they do know each item
            query = "MATCH (r), (i) "
            query += f"WHERE r.ranker_id='{ranker.ranker_id}' "
            query += f"AND i.item_id IN {[item.item_id for item in known_items]} "
            query += f"MERGE (r)-[:KNOWS]->(i)"
            db.cypher_query(query)

    if unknown_items:
        with db.transaction:
            # Delete any existing preferences or queued comparisons
            query = "MATCH (i)-[pc:PREFERRED_TO_BY|COMPARE_WITH_BY]-() "
            query += f"WHERE pc.by='{ranker.ranker_id}' "
            query += f"AND i.item_id IN {[item.item_id for item in unknown_items]} "
            query += f"DELETE pc"
            db.cypher_query(query)

            # Remove that they know each item
            query = "MATCH (r)-[k:KNOWS]->(i) "
            query += f"WHERE r.ranker_id='{ranker.ranker_id}' "
            query += f"AND i.item_id IN {[item.item_id for item in unknown_items]} "
            query += f"DELETE k"
            db.cypher_query(query)

            # Add that they do not know each item
            query = "MATCH (r), (i) "
            query += f"WHERE r.ranker_id='{ranker.ranker_id}' "
            query += f"AND i.item_id IN {[item.item_id for item in unknown_items]} "
            query += f"MERGE (r)-[:DOES_NOT_KNOW]->(i)"            
            db.cypher_query(query)

def insert_preferences(ranker: Ranker, new_preferences: list[tuple[Item,Item]]):
    warnings = []

    for preferred, nonpreferred in new_preferences:
        with db.transaction:
            # If this preference were a queued comparison, we remove that comparison from the queue
            # We delete this comparison even if the preference is invalid (so that invalid comparisons are no longer queued)
            query = "MATCH (i)-[r:COMPARE_WITH_BY]-(j) "
            query += f"WHERE i.item_id='{preferred.item_id}' AND j.item_id='{nonpreferred.item_id}' AND r.by='{ranker.ranker_id}' "
            query += "DELETE r"
            db.cypher_query(query)

            query = "MATCH (i), (u), (j) "
            query += f"WHERE (i.item_id='{preferred.item_id}') AND (u.ranker_id='{ranker.ranker_id}') AND (j.item_id='{nonpreferred.item_id}') "
            query += "AND EXISTS((i)<-[:KNOWS]-(u)-[:KNOWS]->(j))"
            query += f"AND NOT EXISTS((i)<-[:PREFERRED_TO_BY* {{by:'{ranker.ranker_id}'}}]-(j)) "
            query += f"MERGE (i)-[:PREFERRED_TO_BY {{by:'{ranker.ranker_id}'}}]->(j)"
            query += f"RETURN size((i)-[:PREFERRED_TO_BY {{by:'{ranker.ranker_id}'}}]->(j))=1"
            results, _ = db.cypher_query(query)
            if not results or not results[0][0]:
                warnings.append(f'Cound not insert preference {preferred.item_id}, {nonpreferred.item_id}')
    
    return warnings


def insert_queued_compares(ranker: Ranker, new_queued: list[tuple[Item,Item]]):
    inserted_count = 0

    for left, right in new_queued:
        query = "MATCH (i), (u), (j) "
        query += f"WHERE (i.item_id='{left.item_id}') AND (u.ranker_id='{ranker.ranker_id}') AND (j.item_id='{right.item_id}') "
        query += "AND EXISTS((i)<-[:KNOWS]-(u)-[:KNOWS]->(j))"
        query += f"AND NOT EXISTS((i)-[:PREFERRED_TO_BY|COMPARE_WITH_BY* {{by:'{ranker.ranker_id}'}}]->(j)) "
        query += f"AND NOT EXISTS((i)<-[:PREFERRED_TO_BY|COMPARE_WITH_BY* {{by:'{ranker.ranker_id}'}}]-(j)) "
        query += f"MERGE (i)-[:COMPARE_WITH_BY {{by:'{ranker.ranker_id}'}}]->(j) "
        query += f"MERGE (i)<-[:COMPARE_WITH_BY {{by:'{ranker.ranker_id}'}}]-(j) "
        query += f"RETURN size((i)-[:COMPARE_WITH_BY {{by:'{ranker.ranker_id}'}}]-(j))=2"
        results, _ = db.cypher_query(query)
        if results and results[0][0]:
            inserted_count += 1
    
    return inserted_count
       

# Retrieve operations
def get_direct_preferences(ranker: Ranker, item_class) -> list[tuple[Item, Item]]:
    item_labels = ':'.join(item_class.inherited_labels())

    query = f"MATCH (i:{item_labels})-[r:PREFERRED_TO_BY]->(j:{item_labels}) "
    query += f"WHERE r.by='{ranker.ranker_id}'"
    query += "RETURN i,j"

    results, _ = db.cypher_query(query)
    return [(item_class.inflate(row[0]), item_class.inflate(row[1])) for row in results]


def topological_sort(ranker: Ranker, item_class):
    item_labels = ':'.join(item_class.inherited_labels())

    query = f"MATCH (:Ranker {{ranker_id:'{ranker.ranker_id}'}})-[:KNOWS]->(i:{item_labels}) "
    query += "RETURN i "
    query += f"ORDER BY size([(i)-[:PREFERRED_TO_BY*{{by:'{ranker.ranker_id}'}}]->(j:{item_labels}) | j.item_id]) DESC"

    results, _ = db.cypher_query(query)
    return [item_class.inflate(row[0]) for row in results]


def list_queued_compares(ranker: Ranker, item_class, limit=None):
    item_labels = ':'.join(item_class.inherited_labels())

    # Get any existing comparisons to be made
    query = f"MATCH (u)-[:KNOWS]->(i:{item_labels})-[r:COMPARE_WITH_BY]->(j:{item_labels})<-[:KNOWS]-(u) "
    query += f"WHERE r.by='{ranker.ranker_id}' "
    query += f"AND id(i) < id(j) "  # Don't double-count
    query += "RETURN i,j"

    # Limit if needed
    if limit is not None:
        query += f" LIMIT {limit}"

    results, _ = db.cypher_query(query)

    # Present each comparison in a random order
    output = []
    for row in results:
        left, right = item_class.inflate(row[0]), item_class.inflate(row[1])
        pair = sample([left, right],2)
        output.append(tuple(pair))
    return output


def get_random_possible_queued_compares(ranker: Ranker, item_class, limit=100):
    item_labels = ':'.join(item_class.inherited_labels())

    query = f"MATCH (i:{item_labels})<-[:KNOWS]-(u)-[:KNOWS]->(j:{item_labels}) "
    query += f"WHERE u.ranker_id='{ranker.ranker_id}' "
    query += "AND id(i) < id(j) "
    query += f"AND NOT EXISTS((i)-[:PREFERRED_TO_BY|COMPARE_WITH_BY* {{by:'{ranker.ranker_id}'}}]->(j)) "
    query += f"AND NOT EXISTS((i)<-[:PREFERRED_TO_BY|COMPARE_WITH_BY* {{by:'{ranker.ranker_id}'}}]-(j)) "
    query += f"WITH i,j, rand() as r "
    query += "ORDER BY r "
    query += "RETURN i,j"
    if limit is not None:
        query += f" LIMIT {limit}"

    results, _ = db.cypher_query(query)

    return [(item_class.inflate(row[0]), item_class.inflate(row[1])) for row in results]


def populate_queued_compares(ranker: Ranker, item_class, max_created=100):
    created = 0
    to_attempt = get_random_possible_queued_compares(ranker, item_class, limit=max_created)

    while to_attempt and created < max_created:
        created += insert_queued_compares(ranker, to_attempt)
        to_attempt = get_random_possible_queued_compares(ranker, item_class, limit=max_created-created)
    

def list_undefined_known_items(ranker: Ranker, item_class, limit=100):
    item_labels = ':'.join(item_class.inherited_labels())

    query = f"MATCH (r:Ranker), (i:{item_labels}) "
    query += f"WHERE r.ranker_id='{ranker.ranker_id}' "
    query += "AND NOT EXISTS((r)-[:KNOWS]->(i)) " 
    query += "AND NOT EXISTS((r)-[:DOES_NOT_KNOW]->(i)) "
    query += "WITH i, rand() as x "
    query += f"ORDER BY x LIMIT {limit} "
    query += "RETURN i"
    results, _ = db.cypher_query(query)

    return [item_class.inflate(row[0]) for row in results]


# Delete operations
def delete_direct_preference(ranker: Ranker, preferred: Item, nonpreferred: Item):
    with db.transaction:
        if not direct_preference_exists:
            return 'Invalid'

        query = "MATCH (i)-[r:PREFERRED_TO_BY]->(j) "
        query += f"WHERE i.item_id='{preferred.item_id}' AND j.item_id='{nonpreferred.item_id}' AND r.by='{ranker.ranker_id}' "
        query += "DELETE r"
        db.cypher_query(query)


def delete_ranker_knows(ranker: Ranker, item: Item):
    with db.transaction:
        # Delete all direct preferences the ranker has (or has queued) for this item in both directions
        del_preference_query = "MATCH (i:Item)-[pc:PREFERRED_TO_BY|COMPARE_WITH_BY]-() "
        del_preference_query += f"WHERE i.item_id='{item.item_id}' AND pc.by='{ranker.ranker_id}'"
        del_preference_query += "DELETE pc"
        db.cypher_query(del_preference_query)

        # Then delete this KNOWS relationship
        del_preference_query = "MATCH (r:Ranker)-[kdk:KNOWS|DOES_NOT_KNOW]->(i) "
        del_preference_query += f"WHERE i.item_id='{item.item_id}' AND r.ranker_id='{ranker.ranker_id}'"
        del_preference_query += "DELETE kdk"
        db.cypher_query(del_preference_query)


def delete_ranker(ranker: Ranker):
    with db.transaction:
        # Delete all preferences the ranker has (or has queued) for all items in both directions
        del_preference_query = f"MATCH (:Item)-[pc:PREFERRED_TO_BY|COMPARE_WITH_BY]-(:Item) "
        del_preference_query += f"WHERE pc.by = '{ranker.ranker_id}' "
        del_preference_query += f"DELETE pc"
        db.cypher_query(del_preference_query)

        # Delete all KNOWS and DOES_NOT_KNOW relationships the ranker has for all items
        ranker.known_items.disconnect_all()
        ranker.unknown_items.disconnect_all()

        # Then delete the ranker
        ranker.delete()


def delete_item(item: Item):
    with db.transaction:
        # Detach item from other items (removing preferences and queued compares for all rankers)
        # Detach item from rankers (removing known relationships)
        # Then delete item
        del_preference_query = f"MATCH (i:Item) "
        del_preference_query += f"WHERE i.item_id = '{item.item_id}'"
        del_preference_query += f"DETACH DELETE i"
        db.cypher_query(del_preference_query)


def delete_all_queued_compares(ranker: Ranker, item_class):
    item_labels = ':'.join(item_class.inherited_labels())

    query = f"MATCH (:{item_labels})-[c:COMPARE_WITH_BY]-(:{item_labels}) "
    query += f"WHERE c.by='{ranker.ranker_id}' "
    query += "DELETE c"
    db.cypher_query(query)
