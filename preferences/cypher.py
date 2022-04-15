from .models import Item, Ranker
from neomodel import db

# Boolean checks
def ranker_knows_item(ranker: Ranker, item: Item) -> bool:
    return item in ranker.known_items.all()


def direct_preference_exists(ranker: Ranker, preferred: Item, nonpreferred: Item):
    return nonpreferred in preferred.preferred_to_items.match(by=ranker.ranker_id)


def indirect_preference_exists(ranker: Ranker, preferred: Item, nonpreferred: Item):
    query = "MATCH p=(i:Item)-[r:PREFERRED_TO_BY*]->(j:Item) "
    query += f"WHERE i.item_id='{preferred.item_id}' AND j.item_id='{nonpreferred.item_id}' "
    query += f"AND all(r in relationships(p) WHERE r.by='{ranker.ranker_id}') "
    query += "RETURN count(p)>0"

    results, _ = db.cypher_query(query)
    return results[0][0]


def queued_preference_may_exist(ranker: Ranker, preferred: Item, nonpreferred: Item):
    # Check if an indirect preference exists or might exist after all queued comparisons are resolved
    query = "MATCH p=(i:Item)-[r:PREFERRED_TO_BY|COMPARE_WITH_BY*]->(j:Item) "
    query += f"WHERE i.item_id='{preferred.item_id}' AND j.item_id='{nonpreferred.item_id}' "
    query += f"AND all(r in relationships(p) WHERE r.by='{ranker.ranker_id}') "
    query += "RETURN count(p)>0"

    results, _ = db.cypher_query(query)
    return results[0][0]

# Create operations
def insert_ranker_knows(ranker: Ranker, item: Item):
    ranker.known_items.connect(item)


def insert_preference(ranker: Ranker, preferred: Item, nonpreferred: Item):
    with db.transaction:
        if not ranker_knows_item(ranker, preferred) or not ranker_knows_item(ranker, nonpreferred):
            # Ranker must know both items to have a preference
            return 'Invalid'

        if indirect_preference_exists(ranker, preferred=nonpreferred, nonpreferred=preferred):
            # Preference must not violate existing preferences and create a cycle
            return 'Invalid'

        if direct_preference_exists(ranker, preferred, nonpreferred):
            return 'Exists'

        # If this preference were a comparison, we remove that comparison from the queue
        # We do this regardless of whether the preference is valid or not;
        query = "MATCH (i:Item)-[r:COMPARE_WITH_BY]-(j:Item) "
        query += f"WHERE i.item_id='{preferred.item_id}' AND j.item_id='{nonpreferred.item_id}' AND r.by='{ranker.ranker_id}' "
        query += "DELETE r"
        db.cypher_query(query)

        preferred.preferred_to_items.connect(nonpreferred,
                                             {'by': ranker.ranker_id})
        return 'Created'


def insert_queued_compare(ranker: Ranker, left: Item, right: Item):
    with db.transaction:
        if not ranker_knows_item(ranker, left) or not ranker_knows_item(ranker, right):
            # Ranker must know both items to be have a preference
            return False

        if (queued_preference_may_exist(ranker, preferred=left, nonpreferred=right)
                or queued_preference_may_exist(ranker, preferred=right, nonpreferred=left)):
            # Comparison must not be able to violate existing preferences and create a cycle
            return False

        # Insert in both directions so that traversal paths work either way
        left.queued_compares.connect(right, {'by': ranker.ranker_id})
        right.queued_compares.connect(left, {'by': ranker.ranker_id})
        return True


# Retrieve operations
def get_direct_preferences(ranker: Ranker) -> list[tuple[Item, Item]]:
    query = "MATCH (i:Item)-[r:PREFERRED_TO_BY]->(j:Item) "
    query += f"WHERE r.by='{ranker.ranker_id}'"
    query += "RETURN i,j"

    results, _ = db.cypher_query(query)
    return [(Item.inflate(row[0]), Item.inflate(row[1])) for row in results]


def topological_sort(ranker: Ranker):
    query = f"MATCH (:Ranker {{ranker_id:'{ranker.ranker_id}'}})-[:KNOWS]->(i:Item) "
    query += "RETURN i "
    query += f"ORDER BY size([(i:Item)-[:PREFERRED_TO_BY*{{by:'{ranker.ranker_id}'}}]->(j:Item) | j.item_id]) DESC"

    results, _ = db.cypher_query(query)
    return [Item.inflate(row[0]) for row in results]


def list_queued_compares(ranker: Ranker):
    # Get any existing comparisons to be made
    query = "MATCH (i:Item)-[r:COMPARE_WITH_BY]-(j:Item) "
    query += f"WHERE r.by='{ranker.ranker_id}' "
    query += "RETURN i,j"
    results, _ = db.cypher_query(query)

    return [(Item.inflate(row[0]), Item.inflate(row[1])) for row in results]


def get_random_possible_queued_compare(ranker: Ranker):
    query = "MATCH (i:Item), (j:Item) "
    query += f"WHERE EXISTS((:Ranker {{ranker_id:'{ranker.ranker_id}'}})-[:KNOWS]->(i)) "
    query += f"AND EXISTS((:Ranker {{ranker_id:'{ranker.ranker_id}'}})-[:KNOWS]->(j)) "
    query += f"AND NOT EXISTS((i)-[:PREFERRED_TO_BY|COMPARE_WITH_BY* {{by:'{ranker.ranker_id}'}}]->(j)) "
    query += f"AND NOT EXISTS((j)-[:PREFERRED_TO_BY|COMPARE_WITH_BY* {{by:'{ranker.ranker_id}'}}]->(i)) "
    query += "AND id(i) < id(j) "
    query += "RETURN i,j, rand() as r "
    query += "ORDER BY r LIMIT 1"
    results, _ = db.cypher_query(query)

    if not results:
        return None, None

    return Item.inflate(results[0][0]), Item.inflate(results[0][1])


def populate_queued_compares(ranker: Ranker):
    left, right = get_random_possible_queued_compare(ranker)

    while left is not None:
        success = insert_queued_compare(ranker, left, right)
        if not success:
            break
        left, right = get_random_possible_queued_compare(ranker)

# Delete operations
def delete_direct_preference(ranker: Ranker, preferred: Item, nonpreferred: Item):
    with db.transaction:
        if not direct_preference_exists:
            return 'Invalid'

        query = "MATCH (i:Item)-[r:PREFERRED_TO_BY]->(j:Item) "
        query += f"WHERE i.item_id='{preferred.item_id}' AND j.item_id='{nonpreferred.item_id}' AND r.by='{ranker.ranker_id}' "
        query += "DELETE r"
        db.cypher_query(query)


def delete_ranker_knows(ranker: Ranker, item: Item):
    with db.transaction:
        # Delete all direct preferences the ranker has (or has queued) for this item in both directions
        del_preference_query = "MATCH (i:Item)-[r:PREFERRED_TO_BY|COMPARE_WITH_BY]-(:Item) "
        del_preference_query += f"WHERE i.item_id='{item.item_id}' AND r.by='{ranker.ranker_id}'"
        del_preference_query += "DELETE r"

        db.cypher_query(del_preference_query)

        # Then delete this KNOWS relationship
        ranker.known_items.disconnect(item)


def delete_ranker(ranker: Ranker):
    with db.transaction:
        # Delete all preferences the ranker has (or has queued) for all items in both directions
        del_preference_query = f"MATCH (:Item)-[r:PREFERRED_TO_BY|COMPARE_WITH_BY]-(:Item) "
        del_preference_query += f"WHERE r.by = '{ranker.ranker_id}' "
        del_preference_query += f"DELETE r"
        db.cypher_query(del_preference_query)

        # Delete all KNOWS relationships the ranker has for all items
        ranker.known_items.disconnect_all()

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


def delete_all_queued_compares(ranker: Ranker):
    query = "MATCH (:Item)-[r:COMPARE_WITH_BY]-(:Item) "
    query += f"WHERE r.by='{ranker.ranker_id}' "
    query += "DELETE r"
    db.cypher_query(query)
