from django.http import Http404
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from neomodel.exceptions import DoesNotExist
from .models import Ranker, Item
from .cypher import (delete_all_queued_compares, delete_direct_preference, delete_ranker_knows,
                     direct_preference_exists, get_direct_preferences, insert_preferences,
                     insert_ranker_knows, list_queued_compares, ranker_does_not_know_item, ranker_knows_item,
                     topological_sort, populate_queued_compares, list_undefined_known_items)
from .serializers import RankerSerializer, ItemSerializer


def get_serializer_for_item(self, item: Item):
    # Default behavior
    return ItemSerializer(item)


class RankerViewSet(GenericViewSet):
    serializer_class = RankerSerializer
    permission_classes = [IsAuthenticated]
    serialize_item = get_serializer_for_item

    def get_queryset(self):
        pass

    def get_object(self):
        try:
            obj = Ranker.nodes.get(ranker_id=self.request.user.id)
        except DoesNotExist:
            raise Http404

        self.check_object_permissions(self.request, obj)

        return obj

    def get_sorted_list(self, request, *args, **kwargs):
        ranker = self.get_object()
        sorted_known_items = topological_sort(ranker)
        data = [self.serialize_item(item).data for item in sorted_known_items]
        return Response(data)

    def get_comparisons_queue(self, request, *args, **kwargs):
        ranker = self.get_object()
        data = [[self.serialize_item(i).data, self.serialize_item(j).data]
                for i, j in list_queued_compares(ranker)]

        return Response(data)

    def reset_comparisons_queue(self, request, *args, **kwargs):
        ranker = self.get_object()
        delete_all_queued_compares(ranker)
        populate_queued_compares(ranker)
        data = [[self.serialize_item(i).data, self.serialize_item(j).data]
                for i, j in list_queued_compares(ranker)]
        return Response(data, status=status.HTTP_201_CREATED)

    def clear_comparisons_queue(self, request, *args, **kwargs):
        ranker = self.get_object()
        delete_all_queued_compares(ranker)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RankerKnowsViewSet(GenericViewSet):
    serializer_class = RankerSerializer
    permission_classes = [IsAuthenticated]
    serialize_item = get_serializer_for_item

    def get_queryset(self):
        pass

    def get_ranker(self):
        try:
            ranker = Ranker.nodes.get(ranker_id=self.request.user.id)
        except DoesNotExist:
            raise Http404

        self.check_object_permissions(self.request, ranker)

        return ranker

    def get_item(self):
        try:
            item = Item.nodes.get(item_id=self.kwargs['item_id'])
        except DoesNotExist:
            raise Http404

        self.check_object_permissions(self.request, item)

        return item

    def list(self, request, *args, **kwargs):
        ranker = self.get_ranker()
        known_items = ranker.known_items.all()
        data = [self.serialize_item(item).data for item in known_items]
        return Response(data=data)

    def retrieve(self, request, *args, **kwargs):
        ranker = self.get_ranker()
        item = self.get_item()

        if ranker_knows_item(ranker, item):
            return Response(data={'knows': True})
        elif ranker_does_not_know_item(ranker, item):
            return Response(data={'knows': False})
        else:
            return Response(data={'knows': 'undefined'})

    def create(self, request, *args, **kwargs):
        ranker = self.get_ranker()
        try:
            new_known_items = [Item.nodes.get(item_id=i)
                               for i in self.kwargs['new_known_ids']]
            new_unknown_items = [Item.nodes.get(item_id=i)
                                 for i in self.kwargs['new_unknown_ids']]
        except DoesNotExist:
            raise Http404

        insert_ranker_knows(ranker,
                            new_known_items=new_known_items,
                            new_unknown_items=new_unknown_items)

        return Response(status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        ranker = self.get_ranker()
        item = self.get_item()
        delete_ranker_knows(ranker, item)
        return Response(data={'knows': 'undefined'})

    def discover(self, request, *args, **kwargs):
        ranker = self.get_ranker()
        discoverable_items = list_undefined_known_items(ranker)
        data = [self.serialize_item(item).data for item in discoverable_items]
        return Response(data=data)


class RankerPairwiseViewSet(GenericViewSet):
    serializer_class = RankerSerializer
    permission_classes = [IsAuthenticated]
    serialize_item = get_serializer_for_item

    def get_queryset(self):
        pass

    def get_ranker(self):
        try:
            ranker = Ranker.nodes.get(ranker_id=self.request.user.id)
        except DoesNotExist:
            raise Http404

        self.check_object_permissions(self.request, ranker)

        return ranker

    def get_items(self):
        try:
            preferred = Item.nodes.get(item_id=self.kwargs['preferred_id'])
            nonpreferred = Item.nodes.get(
                item_id=self.kwargs['nonpreferred_id'])
        except DoesNotExist:
            raise Http404

        self.check_object_permissions(self.request, preferred)
        self.check_object_permissions(self.request, nonpreferred)

        return preferred, nonpreferred

    def list(self, request, *args, **kwargs):
        ranker = self.get_ranker()
        ranker_data = RankerSerializer(ranker).data

        preference_data = [[self.serialize_item(i).data, self.serialize_item(j).data]
                           for i, j in get_direct_preferences(ranker)]

        # Combine into a single JSON object
        data = {'ranker': ranker_data, 'preferences': preference_data}

        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        ranker = self.get_ranker()
        preferred, nonpreferred = self.get_items()
        if direct_preference_exists(ranker, preferred, nonpreferred):
            data = [self.serialize_item(preferred).data,
                    self.serialize_item(nonpreferred).data]
            return Response(data=data)
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)

    def create(self, request, *args, **kwargs):
        ranker = self.get_ranker()

        try:
            new_preferences = [(Item.nodes.get(item_id=i), Item.nodes.get(item_id=j))
                               for i,j in self.kwargs['new_preference_ids']]
        except DoesNotExist:
            raise Http404

        warnings = insert_preferences(ranker, new_preferences)

        data = {'warnings': warnings} if warnings else {}

        return Response(data=data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        ranker = self.get_ranker()
        preferred, nonpreferred = self.get_items()
        delete_direct_preference(ranker, preferred, nonpreferred)
        return Response(status=status.HTTP_204_NO_CONTENT)
