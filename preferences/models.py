from neomodel import StructuredNode, StructuredRel, StringProperty, RelationshipTo
from neomodel.cardinality import One
class Item(StructuredNode):
    '''Profile for a an item which rankes prefer over other items'''
    item_id = StringProperty(required=True, unique_index=True)
class Ranker(StructuredNode):
    '''Profile for a user who provides rankings for items'''
    ranker_id = StringProperty(required=True, unique_index=True)