from django.http import Http404
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.mixins import ListModelMixin, CreateModelMixin, RetrieveModelMixin, DestroyModelMixin
from rest_framework.viewsets import GenericViewSet
from neomodel.exceptions import ConstraintValidationFailed, DoesNotExist, UniqueProperty
from .models import Ranker, Item
from .cypher import (delete_all_queued_compares, delete_direct_preference, delete_item, delete_ranker, delete_ranker_knows,
                     direct_preference_exists, get_direct_preferences, insert_preference,
                     insert_ranker_knows, list_queued_compares, ranker_knows_item, topological_sort, populate_queued_compares)
from .serializers import RankerSerializer, ItemSerializer
from .permissions import IsAdminOrReadOnly


class NeomodelCreateModelMixin(CreateModelMixin):
    '''Adds additional Neomodel constraint validation not handled by Django REST framework'''

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except ConstraintValidationFailed:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class ItemViewSet(ListModelMixin, NeomodelCreateModelMixin, RetrieveModelMixin, DestroyModelMixin, GenericViewSet):
    queryset = Item.nodes
    serializer_class = ItemSerializer
    lookup_field = 'item_id'
    permission_classes = [IsAdminOrReadOnly]

    def get_object(self):
        try:
            obj = Item.nodes.get(item_id=self.kwargs['item_id'])
        except DoesNotExist:
            raise Http404

        self.check_object_permissions(self.request, obj)

        return obj

    def perform_destroy(self, instance):
        return delete_item(instance)


class RankerViewSet(ListModelMixin, NeomodelCreateModelMixin, RetrieveModelMixin, DestroyModelMixin, GenericViewSet):
    queryset = Ranker.nodes
    serializer_class = RankerSerializer
    lookup_field = 'ranker_id'

    def get_object(self):
        try:
            obj = Ranker.nodes.get(ranker_id=self.kwargs['ranker_id'])
        except DoesNotExist:
            raise Http404

        self.check_object_permissions(self.request, obj)

        return obj

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

    def get_sorted_list(self, request, *args, **kwargs):
        ranker = self.get_object()
        sorted_known_items = topological_sort(ranker)
        serializer = ItemSerializer(sorted_known_items, many=True)
        return Response(data=serializer.data)

    def get_comparisons_queue(self, request, *args, **kwargs):
        ranker = self.get_object()
        data = [[ItemSerializer(i).data, ItemSerializer(j).data]
                for i, j in list_queued_compares(ranker)]

        return Response(data)

    def reset_comparisons_queue(self, request, *args, **kwargs):
        ranker = self.get_object()
        delete_all_queued_compares(ranker)
        populate_queued_compares(ranker)
        data = [[ItemSerializer(i).data, ItemSerializer(j).data]
                for i, j in list_queued_compares(ranker)]
        return Response(data, status=status.HTTP_201_CREATED)

    def clear_comparisons_queue(self, request, *args, **kwargs):
        ranker = self.get_object()
        delete_all_queued_compares(ranker)
        return Response(status=status.HTTP_204_NO_CONTENT)

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


class RankerPairwiseViewSet(GenericViewSet):
    def get_object(self):
        try:
            ranker = Ranker.nodes.get(ranker_id=self.kwargs['ranker_id'])
            preferred = Item.nodes.get(item_id=self.kwargs['preferred_id'])
            nonpreferred = Item.nodes.get(
                item_id=self.kwargs['nonpreferred_id'])
        except DoesNotExist:
            raise Http404

        self.check_object_permissions(self.request, ranker)
        self.check_object_permissions(self.request, preferred)
        self.check_object_permissions(self.request, nonpreferred)

        return ranker, preferred, nonpreferred

    def retrieve(self, request, *args, **kwargs):
        ranker, preferred, nonpreferred = self.get_object()
        if direct_preference_exists(ranker, preferred, nonpreferred):
            data = [ItemSerializer(preferred).data,
                    ItemSerializer(nonpreferred).data]
            return Response(data)
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)

    def create(self, request, *args, **kwargs):
        ranker, preferred, nonpreferred = self.get_object()

        # Try to insert the preference, see if it works
        result = insert_preference(ranker, preferred, nonpreferred)

        # Return the appropriate response code
        if result == 'Invalid':
            return Response(status=status.HTTP_400_BAD_REQUEST,)
        else:
            data = [ItemSerializer(preferred).data,
                    ItemSerializer(nonpreferred).data]

            if result == 'Exists':
                return Response(data, status=status.HTTP_200_OK)
            else:
                return Response(data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        ranker, preferred, nonpreferred = self.get_object()
        delete_direct_preference(ranker, preferred, nonpreferred)
        return Response(status=status.HTTP_204_NO_CONTENT)