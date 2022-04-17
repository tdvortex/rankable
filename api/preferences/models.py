from django_neomodel import DjangoNode
from neomodel import StringProperty, RelationshipTo, StructuredRel


class Preference(StructuredRel):
    by = StringProperty(required=True)

class QueuedComparison(StructuredRel):
    by = StringProperty(required=True)

class Item(DjangoNode):
    '''Profile for a an item which rankes prefer over other items'''
    item_id = StringProperty(required=True, unique_index=True)
    preferred_to_items = RelationshipTo('Item', 'PREFERRED_TO_BY', model=Preference)
    queued_compares = RelationshipTo('Item', 'COMPARE_WITH_BY', model=QueuedComparison)
    class Meta:
        app_label = 'preferences'

class Ranker(DjangoNode):
    '''Profile for a user who provides rankings for items'''
    ranker_id = StringProperty(required=True, unique_index=True, primary_key=True)
    known_items = RelationshipTo('Item', 'KNOWS')
    unknown_items = RelationshipTo('Item', 'DOES_NOT_KNOW')
    class Meta:
        app_label = 'preferences'