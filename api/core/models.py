from preferences.models import Item, Ranker
from neomodel.properties import StringProperty, IntegerProperty
class Movie(Item):
    '''Extends the Item class in preferences with simple movie information
    
    This denormalization is an efficiency improvement to prevent excessive 1-row SQL queries'''
    title = StringProperty(max_length=100)
    year = IntegerProperty()

class User(Ranker):
    '''Extends the Ranker class in preferences'''
    pass