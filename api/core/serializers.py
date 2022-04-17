from preferences.serializers import ItemSerializer
from rest_framework import serializers

class MovieNodeSerialiazer(ItemSerializer):
    id = serializers.CharField(read_only=True, source='item_id')
    title = serializers.CharField(read_only=True)
    year = serializers.IntegerField(read_only=True)