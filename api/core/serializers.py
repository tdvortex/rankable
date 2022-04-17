from rest_framework import serializers

class MovieNodeSerialiazer(serializers.Serializer):
    id = serializers.CharField(read_only=True, source='item_id')
    title = serializers.CharField(read_only=True)
    year = serializers.IntegerField(read_only=True)