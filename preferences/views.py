import json
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Ranker, Item
from .cypher import get_direct_preferences, direct_preference_exists, insert_preference
from .serializers import RankerSerializer, ItemSerializer


@api_view(['GET', 'POST'])
def rankers(request):
    if request.method == 'GET':
        serializer = RankerSerializer(Ranker.nodes.all(), many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        serializer = RankerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'validation_error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def items(request):
    if request.method == 'GET':
        serializer = ItemSerializer(Item.nodes.all(), many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        serializer = ItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'validation_error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def ranker_preferences(request, ranker_id: str):
    ranker = Ranker.nodes.first_or_none(ranker_id=ranker_id)
    if not ranker:
        return Response(status=status.HTTP_404_NOT_FOUND, data={'error': f'Ranker with id {ranker_id} not found'})

    data = json.dumps([[ItemSerializer(i).data, ItemSerializer(j).data]
                      for i, j in get_direct_preferences(ranker)])
    return Response(data=data, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
def ranker_pairwise(request, ranker_id: str, preferred_id: str, nonpreferred_id: str):
    errors = {}

    # Check for existence of ranker, preferred, and nonpreferred
    ranker = Ranker.nodes.first_or_none(ranker_id=ranker_id)
    preferred = Item.nodes.first_or_none(item_id=preferred_id)
    nonpreferred = Item.nodes.first_or_none(item_id=nonpreferred_id)
    if not ranker: errors['ranker_error'] = f'Ranker with id {ranker_id} not found'
    if not preferred: errors['preferred_error'] = f'Item with id {preferred_id} not found'
    if not nonpreferred: errors['nonpreferred_error'] = f'Item with id {nonpreferred_id} not found'

    # Throw 404 if anything is missing
    if errors:
        return Response(status=status.HTTP_404_NOT_FOUND, data=errors)

    if request.method == 'GET':
        # Check if the requested preference exists
        if not direct_preference_exists(ranker, preferred, nonpreferred):
            # If it doesn't, return 404
            message = f'Ranker with id {ranker_id} does not have a preference '
            message += f'for {preferred_id} over {nonpreferred_id}'
            return Response(status=status.HTTP_404_NOT_FOUND, data={'preference_error': message})

        # If it does, return a JSON of the two serialized items in order of preference
        return Response(
            data=json.dumps([ItemSerializer(preferred).data,ItemSerializer(nonpreferred).data]),
            status=status.HTTP_200_OK
        )
    elif request.method == 'POST':
        # Try to insert the preference, see if it works
        result = insert_preference(ranker, preferred, nonpreferred)

        # Return the appropriate response code with an error me
        if result == 'Invalid':
            return Response(
                status=status.HTTP_400_BAD_REQUEST, 
                data={'cycle_error': f'Ranker {ranker_id} has a preference for {nonpreferred_id} over {preferred_id}, cycles not allowed'}
            )
        elif result == 'Exists':
            return Response(
                data=json.dumps([ItemSerializer(preferred).data,ItemSerializer(nonpreferred).data]),
                status=status.HTTP_200_OK
            )
        elif result == 'Created':
            return Response(
                data=json.dumps([ItemSerializer(preferred).data,ItemSerializer(nonpreferred).data]),
                status=status.HTTP_201_CREATED
            )