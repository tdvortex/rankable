from rest_framework import serializers
from .models import Ranker, Item

class RankerSerializer(serializers.Serializer):
    ranker_id = serializers.UUIDField(required=True)

class ItemSerializer(serializers.Serializer):
    item_id = serializers.CharField(required=True)