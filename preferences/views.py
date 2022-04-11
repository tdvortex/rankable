from django.http import Http404
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.mixins import ListModelMixin, CreateModelMixin, RetrieveModelMixin, DestroyModelMixin
from rest_framework.viewsets import GenericViewSet
from neomodel.exceptions import ConstraintValidationFailed, DoesNotExist, UniqueProperty
from .models import Ranker, Item
from .cypher import (delete_direct_preference, delete_item, delete_ranker, delete_ranker_knows, direct_preference_exists,
                     get_direct_preferences, insert_preference, insert_ranker_knows, ranker_knows_item, topological_sort)
from .serializers import RankerSerializer, ItemSerializer


class NeomodelGenericViewSet(GenericViewSet):
    '''Overrides GenericViewSet to use neomodel queryset construction'''

    def get_queryset(self):
        return self.queryset.all()

    def get_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        try:
            obj = self.queryset.get(**filter_kwargs)
        except DoesNotExist:
            raise Http404

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj


class NeomodelCreateModelMixin(CreateModelMixin):
    '''Adds additional Neomodel constraint validation not handled by Django REST framework'''

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except ConstraintValidationFailed:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class ItemViewSet(ListModelMixin, NeomodelCreateModelMixin, RetrieveModelMixin, DestroyModelMixin, NeomodelGenericViewSet):
    queryset = Item.nodes
    serializer_class = ItemSerializer
    lookup_field = 'item_id'

    def perform_destroy(self, instance):
        return delete_item(instance)


class RankerViewSet(ListModelMixin, NeomodelCreateModelMixin, RetrieveModelMixin, DestroyModelMixin, NeomodelGenericViewSet):
    queryset = Ranker.nodes
    serializer_class = RankerSerializer
    lookup_field = 'ranker_id'

    def retrieve(self, request, *args, **kwargs):
        ranker = self.get_object()
        ranker_data = self.serializer_class(ranker).data

        preference_data = [[ItemSerializer(i).data, ItemSerializer(j).data]
                           for i, j in get_direct_preferences(ranker)]

        # Combine into a single JSON object
        data = {'ranker': ranker_data, 'preferences': preference_data}

        return Response(data)

    def perform_destroy(self, instance):
        return delete_ranker(instance)


class RankerKnowsViewSet(GenericViewSet):
    def get_object(self):
        try:
            ranker = Ranker.nodes.get(ranker_id=self.kwargs['ranker_id'])
            item = Item.nodes.get(item_id=self.kwargs['item_id'])
        except DoesNotExist:
            raise Http404

        self.check_object_permissions(self.request, ranker)
        self.check_object_permissions(self.request, item)

        return ranker, item

    def retrieve(self, request, *args, **kwargs):
        ranker, item = self.get_object()

        if ranker_knows_item(ranker, item):
            serializer = ItemSerializer(item)
            return Response(serializer.data)
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)

    def create(self, request, *args, **kwargs):
        ranker, item = self.get_object()
        if ranker_knows_item(ranker, item):
            return Response(status=status.HTTP_200_OK)
        else:
            insert_ranker_knows(ranker, item)
            serializer = ItemSerializer(item)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        ranker, item = self.get_object()
        delete_ranker_knows(ranker, item)
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'HEAD', 'POST', 'DELETE'])
def ranker_pairwise_preference(request, ranker_id: str, preferred_id: str, nonpreferred_id: str):
    errors = {}

    # Check for existence of ranker, preferred, and nonpreferred
    ranker = Ranker.nodes.first_or_none(ranker_id=ranker_id)
    preferred = Item.nodes.first_or_none(item_id=preferred_id)
    nonpreferred = Item.nodes.first_or_none(item_id=nonpreferred_id)
    if not ranker:
        errors['ranker_error'] = f'Ranker with id {ranker_id} not found'
    if not preferred:
        errors['preferred_error'] = f'Item with id {preferred_id} not found'
    if not nonpreferred:
        errors['nonpreferred_error'] = f'Item with id {nonpreferred_id} not found'

    # Throw 404 if anything is missing
    if errors:
        return Response(status=status.HTTP_404_NOT_FOUND, data=errors)

    if request.method == 'GET' or request.method == 'HEAD':
        # Check if the requested preference exists
        if not direct_preference_exists(ranker, preferred, nonpreferred):
            # If it doesn't, return 204
            return Response(status=status.HTTP_204_NO_CONTENT)

        # If it does, return a JSON of the two serialized items in order of preference if GET
        # Or just 200 on a HEAD
        if request.method == 'GET':
            data = [ItemSerializer(preferred).data,
                    ItemSerializer(nonpreferred).data]
        else:
            data = []
        return Response(data=data, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        # Try to insert the preference, see if it works
        result = insert_preference(ranker, preferred, nonpreferred)

        # Return the appropriate response code
        if result == 'Invalid':
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={'cycle_error': f'Ranker {ranker_id} has a preference for {nonpreferred_id} over {preferred_id}, cycles not allowed'}
            )
        elif result == 'Exists':
            return Response(
                data=[ItemSerializer(preferred).data,
                      ItemSerializer(nonpreferred).data],
                status=status.HTTP_200_OK
            )
        elif result == 'Created':
            return Response(
                data=[ItemSerializer(preferred).data,
                      ItemSerializer(nonpreferred).data],
                status=status.HTTP_201_CREATED
            )
    elif request.method == 'DELETE':
        delete_direct_preference(ranker, preferred, nonpreferred)
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'HEAD'])
def ranker_sort(request, ranker_id: str):
    # Check for existence of ranker
    ranker = Ranker.nodes.first_or_none(ranker_id=ranker_id)
    if not ranker:
        return Response(status=status.HTTP_404_NOT_FOUND,
                        data={'ranker_error':
                              f'Ranker with id {ranker_id} not found'})

    sorted_known_items = topological_sort(ranker)
    serializer = ItemSerializer(sorted_known_items, many=True)
    data = serializer.data if request.method == 'GET' else []
    return Response(data=data, status=status.HTTP_200_OK)
