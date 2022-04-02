from neomodel import StructuredNode, StructuredRel, StringProperty, RelationshipTo
from neomodel.cardinality import One


class PreferredToByRel(StructuredRel):
    by = StringProperty(required=True)

class Item(StructuredNode):
    '''Profile for a an item which rankes prefer over other items'''
    item_id = StringProperty(required=True, unique_index=True)

    preferred_to_by = RelationshipTo('Item', 'PREFERRED_TO_BY', model=PreferredToByRel)


class Ranker(StructuredNode):
    '''Profile for a user who provides rankings for items'''
    ranker_id = StringProperty(required=True, unique_index=True)

    knows = RelationshipTo(Item, 'KNOWS', cardinality=One)

# Syntax examples

# To add that a ranker knows an item:
# ranker = Ranker(ranker_id='0')
# k_item = Item(item_id='K')
# ranker.knows.connect(k_item)

# To add that a ranker prefers A over B:
# ranker = Ranker(ranker_id='0')
# preferred_item = Item(item_id='A')
# nonpreferred_item = Item(item_id='B')
# preferred_item.preferred_to_by.connect(nonpreferred_item, properties={'by':ranker.ranker_id})

# To get all items which a ranker knows:
# ranker = Ranker(ranker_id='0')
# known_items = ranker.knows.all()

# To get all items for which a ranker directly prefers A:
# ranker = Ranker(ranker_id='0')
# preferred_item = Item(item_id='A')
# nonpreferred_items = preferred_item.preferred_to_by.match('by'=ranker.ranker_id)