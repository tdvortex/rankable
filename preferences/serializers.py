from rest_framework import serializers
from .models import Ranker, Item

class RankerSerializer(serializers.Serializer):
    ranker_id = serializers.CharField(required=True)

    def create(self, validated_data):
        return Ranker(**validated_data).save()

    def update(self, instance, validated_data):
        instance.ranker_id = validated_data.get('ranker_id', instance.ranker_id)
        instance.save()
        return instance

class ItemSerializer(serializers.Serializer):
    item_id = serializers.CharField(required=True)

    def create(self, validated_data):
        return Item(**validated_data).save()

    def update(self, instance, validated_data):
        instance.item_id = validated_data.get('item_id', instance.item_id)
        instance.save()
        return instance