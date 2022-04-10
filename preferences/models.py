from django_neomodel import DjangoNode
from neomodel import StringProperty, RelationshipTo


class Item(DjangoNode):
    '''Profile for a an item which rankes prefer over other items'''
    item_id = StringProperty(required=True, unique_index=True)
    class Meta:
        app_label = 'preferences'

class Ranker(DjangoNode):
    '''Profile for a user who provides rankings for items'''
    ranker_id = StringProperty(required=True, unique_index=True, primary_key=True)
    known_items = RelationshipTo('Item', 'KNOWS')
    class Meta:
        app_label = 'preferences'